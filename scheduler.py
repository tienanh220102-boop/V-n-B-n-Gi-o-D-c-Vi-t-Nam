"""
SCHEDULER — Tự động cào văn bản giáo dục & gửi Telegram mỗi 1 giờ
===================================================================
Cách chạy:
  python scheduler.py          # Chạy liên tục, gửi Telegram khi có văn bản mới
  python scheduler.py --once   # Chạy 1 lần rồi thoát (dùng với Task Scheduler)
  python scheduler.py --test   # Test ngay: cào 2 trang/nguồn, không gửi Telegram

Lần đầu chạy: hệ thống sẽ lưu tất cả văn bản hiện có làm "mốc" (không gửi spam),
sau đó từ lần thứ 2 trở đi chỉ gửi văn bản MỚI xuất hiện.
"""

import sys
import io
import time
import logging
import argparse
from datetime import datetime
from pathlib import Path

# Fix encoding Windows terminal
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding and sys.stderr.encoding.lower() != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent))

from scrapers.chinhphu import ChinhPhuScraper
from scrapers.vbpl import VbplScraper
from scrapers.moet import MoetScraper
from notifier.telegram_bot import TelegramNotifier
from notifier.tracker import DocTracker
from utils.storage import save_to_excel
from config import (
    REQUEST_DELAY, MAX_RETRIES, TIMEOUT, OUTPUT_DIR,
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
    SCHEDULE_INTERVAL_HOURS, SAVE_EXCEL_ON_UPDATE,
)

LOG_DIR = Path(OUTPUT_DIR)
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / 'scheduler.log', encoding='utf-8', mode='a'),
    ],
)
logger = logging.getLogger(__name__)


# ------------------------------------------------------------------ #
# Hàm cào dữ liệu
# ------------------------------------------------------------------ #

def run_scrapers(max_pages=None, fetch_detail=False) -> dict:
    """Chạy tất cả scraper, trả về dict {sheet: [docs]}."""
    kwargs = dict(delay=REQUEST_DELAY, max_retries=MAX_RETRIES, timeout=TIMEOUT)
    scrapers = {
        'Chính phủ': ChinhPhuScraper(**kwargs),
        'VBPL':      VbplScraper(**kwargs),
        'MOET':      MoetScraper(**kwargs),
    }
    result = {}
    for sheet, scraper in scrapers.items():
        logger.info(f'Cào {scraper.SOURCE_NAME}...')
        try:
            docs = scraper.scrape(max_pages=max_pages, fetch_detail=fetch_detail)
            result[sheet] = docs
            logger.info(f'  → {len(docs)} văn bản')
        except Exception as e:
            logger.error(f'  Lỗi {sheet}: {e}')
            result[sheet] = []
    return result


# ------------------------------------------------------------------ #
# Một chu kỳ cập nhật
# ------------------------------------------------------------------ #

def run_update_cycle(bot: TelegramNotifier, tracker: DocTracker,
                     test_mode: bool = False):
    """Chạy 1 chu kỳ: cào → lọc mới → gửi Telegram → lưu Excel."""
    now = datetime.now().strftime('%d/%m/%Y %H:%M')
    logger.info(f'====== Bắt đầu chu kỳ cập nhật: {now} ======')

    max_pages = 2 if test_mode else None

    # Bước 1: Cào dữ liệu
    docs_by_source = run_scrapers(max_pages=max_pages, fetch_detail=False)
    all_docs = [d for docs in docs_by_source.values() for d in docs]
    logger.info(f'Tổng văn bản cào được: {len(all_docs)}')

    # Bước 2: Lọc văn bản mới
    is_first = tracker.is_first_run()

    if is_first:
        # Lần đầu: lưu tất cả làm mốc, không gửi spam
        logger.info(f'Lần đầu khởi động — lưu {len(all_docs)} văn bản làm mốc')
        tracker.mark_all_seen(all_docs)
        tracker.update_last_run()
        if bot and not test_mode:
            bot.notify_startup(tracker.total_known)
        logger.info('Đã gửi tin khởi động lên Telegram.')
    else:
        new_docs = tracker.filter_new(all_docs)
        logger.info(f'Văn bản mới: {len(new_docs)}')

        if test_mode:
            # Trong test mode: in ra màn hình, không gửi Telegram
            if new_docs:
                print(f'\n=== {len(new_docs)} văn bản MỚI sẽ được gửi Telegram ===')
                for d in new_docs[:5]:
                    print(f'  • [{d.get("so_hieu","")}] {d.get("ten_van_ban","")[:60]}')
            else:
                print('\n=== Không có văn bản mới ===')
        else:
            if new_docs:
                sent = bot.notify_new_docs(new_docs)
                logger.info(f'Đã gửi {sent} văn bản lên Telegram')
                tracker.mark_seen(new_docs)
            else:
                logger.info('Không có văn bản mới — bỏ qua')

        tracker.update_last_run()

    # Bước 3: Lưu Excel (nếu bật)
    if SAVE_EXCEL_ON_UPDATE and all_docs and not test_mode:
        try:
            path = save_to_excel(docs_by_source, OUTPUT_DIR)
            logger.info(f'Đã lưu Excel: {path}')
        except Exception as e:
            logger.error(f'Lỗi lưu Excel: {e}')

    logger.info(f'====== Chu kỳ hoàn thành. Đã theo dõi: {tracker.total_known} văn bản ======\n')


# ------------------------------------------------------------------ #
# Vòng lặp chính
# ------------------------------------------------------------------ #

def send_latest(bot: TelegramNotifier, n: int = 5):
    """Cào và gửi N văn bản mới nhất lên Telegram (bất kể đã seen chưa)."""
    logger.info(f'====== Gửi {n} văn bản mới nhất ======')
    docs_by_source = run_scrapers(max_pages=2, fetch_detail=False)
    all_docs = [d for docs in docs_by_source.values() for d in docs]
    if not all_docs:
        bot.send('⚠️ Không cào được văn bản nào.')
        return
    latest = all_docs[:n]
    logger.info(f'Gửi {len(latest)} văn bản lên Telegram...')
    bot.notify_new_docs(latest)
    logger.info('Gửi xong.')


def main():
    parser = argparse.ArgumentParser(description='Scheduler tự động theo dõi văn bản giáo dục')
    parser.add_argument('--once',        action='store_true', help='Chạy 1 lần rồi thoát')
    parser.add_argument('--test',        action='store_true', help='Test: 2 trang, không gửi Telegram')
    parser.add_argument('--send-latest', type=int, metavar='N', help='Gửi N văn bản mới nhất lên Telegram ngay')
    args = parser.parse_args()

    # Khởi tạo bot và tracker
    tracker = DocTracker()
    bot = None

    if not args.test:
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            print('\n[LỖI] Chưa điền TELEGRAM_BOT_TOKEN và TELEGRAM_CHAT_ID trong config.py')
            print('      Xem hướng dẫn trong file README_TELEGRAM.txt\n')
            sys.exit(1)
        bot = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
        logger.info('Kiểm tra kết nối Telegram...')
        if not bot.test_connection():
            print('\n[LỖI] Không kết nối được Telegram. Kiểm tra lại BOT_TOKEN.\n')
            sys.exit(1)

    # Gửi N văn bản mới nhất
    if args.send_latest:
        send_latest(bot, args.send_latest)
        return

    # Chạy 1 lần
    if args.once or args.test:
        run_update_cycle(bot, tracker, test_mode=args.test)
        return

    # Chạy liên tục
    interval_sec = SCHEDULE_INTERVAL_HOURS * 3600
    logger.info(f'Scheduler khởi động — cập nhật mỗi {SCHEDULE_INTERVAL_HOURS} giờ')
    logger.info(f'Nhấn Ctrl+C để dừng.\n')

    while True:
        try:
            run_update_cycle(bot, tracker)
        except KeyboardInterrupt:
            logger.info('Đã dừng scheduler.')
            break
        except Exception as e:
            logger.error(f'Lỗi chu kỳ: {e}')
            if bot:
                bot.notify_error(str(e))

        next_run = datetime.fromtimestamp(time.time() + interval_sec)
        logger.info(f'Chu kỳ tiếp theo: {next_run.strftime("%H:%M:%S %d/%m/%Y")}')
        logger.info(f'Đang ngủ {SCHEDULE_INTERVAL_HOURS} giờ...\n')

        try:
            time.sleep(interval_sec)
        except KeyboardInterrupt:
            logger.info('Đã dừng scheduler.')
            break


if __name__ == '__main__':
    main()
