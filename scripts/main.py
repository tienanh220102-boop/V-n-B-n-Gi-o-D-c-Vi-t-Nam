"""
CÀO VĂN BẢN GIÁO DỤC VIỆT NAM
================================
Nguồn chính thức:
  - vanban.chinhphu.vn  (Cổng TTĐT Chính phủ)
  - vbpl.vn             (CSDL Quốc gia về Pháp luật)
  - moet.gov.vn         (Bộ Giáo dục và Đào tạo)

Cách dùng:
  python main.py                          # Cào tất cả, lấy chi tiết
  python main.py --source chinhphu        # Chỉ cào chinhphu.vn
  python main.py --max-pages 5            # Giới hạn 5 trang/nguồn
  python main.py --no-detail              # Chỉ lấy danh sách, không vào từng trang
  python main.py --test                   # Test nhanh: 2 trang/nguồn, không detail
"""

import sys
import io
import logging
import argparse
from datetime import datetime
from pathlib import Path

# Fix encoding trên Windows terminal (cp1252 không hiểu tiếng Việt)
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding and sys.stderr.encoding.lower() != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Thêm project root vào sys.path để import scrapers/, utils/, config.py
sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapers.chinhphu import ChinhPhuScraper
from scrapers.vbpl import VbplScraper
from scrapers.moet import MoetScraper
from utils.storage import save_to_excel
from config import REQUEST_DELAY, MAX_RETRIES, TIMEOUT, OUTPUT_DIR


def setup_logging(output_dir: str):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    log_file = Path(output_dir) / 'scraper.log'

    fmt = '%(asctime)s | %(levelname)-8s | %(message)s'
    datefmt = '%H:%M:%S'

    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, encoding='utf-8', mode='a'),
    ]
    logging.basicConfig(level=logging.INFO, format=fmt, datefmt=datefmt, handlers=handlers)


def parse_args():
    p = argparse.ArgumentParser(
        description='Cào văn bản giáo dục từ cổng thông tin chính phủ Việt Nam',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument('--source', choices=['all', 'chinhphu', 'vbpl', 'moet'],
                   default='all', help='Nguồn cần cào (mặc định: all)')
    p.add_argument('--max-pages', type=int, default=None,
                   help='Giới hạn số trang mỗi nguồn (mặc định: cào hết)')
    p.add_argument('--no-detail', action='store_true',
                   help='Chỉ lấy danh sách, không vào từng văn bản')
    p.add_argument('--test', action='store_true',
                   help='Chế độ test: 2 trang/nguồn, không lấy chi tiết')
    p.add_argument('--output', default=OUTPUT_DIR,
                   help=f'Thư mục lưu file Excel (mặc định: {OUTPUT_DIR})')
    return p.parse_args()


def print_banner():
    w = 65
    print('\n' + '=' * w)
    print(f"{'CÀO VĂN BẢN GIÁO DỤC VIỆT NAM':^{w}}")
    print(f"{'vanban.chinhphu.vn | vbpl.vn | moet.gov.vn':^{w}}")
    print(f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S'):^{w}}")
    print('=' * w + '\n')


def main():
    args = parse_args()
    setup_logging(args.output)

    print_banner()

    max_pages    = 2 if args.test else args.max_pages
    fetch_detail = False if args.test else not args.no_detail

    if args.test:
        print('  [TEST] Chế độ test: 2 trang/nguồn, bỏ qua chi tiết\n')
    if not fetch_detail and not args.test:
        print('  [INFO] Chế độ nhanh: chỉ lấy danh sách (--no-detail)\n')

    scraper_kwargs = dict(
        delay       = REQUEST_DELAY,
        max_retries = MAX_RETRIES,
        timeout     = TIMEOUT,
    )

    # Cấu hình nguồn
    all_scrapers = {
        'chinhphu': ('Chính phủ', ChinhPhuScraper(**scraper_kwargs)),
        'vbpl':     ('VBPL',      VbplScraper(**scraper_kwargs)),
        'moet':     ('MOET',      MoetScraper(**scraper_kwargs)),
    }

    sources_to_run = (
        list(all_scrapers.keys()) if args.source == 'all'
        else [args.source]
    )

    docs_by_source = {}
    total = 0

    for key in sources_to_run:
        sheet_name, scraper = all_scrapers[key]
        print(f'\n>>> {scraper.SOURCE_NAME}')
        print(f"    {'─' * 55}")

        try:
            docs = scraper.scrape(max_pages=max_pages, fetch_detail=fetch_detail)
            docs_by_source[sheet_name] = docs
            total += len(docs)
            print(f'    Ket qua: {len(docs):,} van ban')
        except Exception as e:
            logging.getLogger(__name__).error(f'Lỗi khi cào {key}: {e}')
            docs_by_source[sheet_name] = []
            print(f'    LOI: {e}')

    # Kết quả
    w = 65
    print('\n' + '=' * w)
    print(f"  TONG KET: {total:,} van ban tu {len(sources_to_run)} nguon")
    print('=' * w)

    if total > 0:
        try:
            output_file = save_to_excel(docs_by_source, args.output)
            print(f'\n  File Excel: {output_file}')
            print(f'  Mo file de xem ket qua!\n')
        except Exception as e:
            logging.getLogger(__name__).error(f'Lỗi lưu Excel: {e}')
            print(f'\n  LOI luu Excel: {e}\n')
    else:
        print('\n  Khong co van ban nao duoc cao.\n')
        print('  Goi y: kiem tra ket noi mang va thu lai.\n')


if __name__ == '__main__':
    main()
