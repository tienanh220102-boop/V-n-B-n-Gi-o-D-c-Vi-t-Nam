"""
Gửi thông báo văn bản mới lên Telegram qua Bot API.
Không cần thư viện ngoài — chỉ dùng requests (đã có sẵn).
"""

import logging
import requests

logger = logging.getLogger(__name__)

TELEGRAM_API = 'https://api.telegram.org/bot{token}/{method}'
MAX_MSG_LEN = 4096  # Giới hạn Telegram


class TelegramNotifier:

    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id

    # ------------------------------------------------------------------ #
    # Gửi 1 tin nhắn thô (text)
    # ------------------------------------------------------------------ #

    def send(self, text: str) -> bool:
        """Gửi text lên Telegram, trả về True nếu thành công."""
        url = TELEGRAM_API.format(token=self.token, method='sendMessage')
        # Cắt nếu quá dài
        if len(text) > MAX_MSG_LEN:
            text = text[:MAX_MSG_LEN - 20] + '\n...[xem link gốc]'
        try:
            resp = requests.post(url, json={
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True,
            }, timeout=15)
            resp.raise_for_status()
            return True
        except Exception as e:
            logger.error(f'[Telegram] Lỗi gửi tin: {e}')
            return False

    # ------------------------------------------------------------------ #
    # Format 1 văn bản thành tin nhắn đẹp
    # ------------------------------------------------------------------ #

    def _format_doc(self, doc: dict, idx: int, total: int) -> str:
        loai  = doc.get('loai_van_ban', '')
        so    = doc.get('so_hieu', '')
        ten   = doc.get('ten_van_ban', '')
        co_quan = doc.get('co_quan_ban_hanh', '')
        ngay  = doc.get('ngay_ban_hanh', '')
        url   = doc.get('url_goc', '')
        nguon = doc.get('nguon', '')

        lines = [f'📄 <b>Văn bản mới {idx}/{total}</b>']
        if loai:
            lines.append(f'📋 <b>Loại:</b> {loai}')
        if so:
            lines.append(f'🔢 <b>Số hiệu:</b> {so}')
        if ten:
            preview = ten[:120] + ('...' if len(ten) > 120 else '')
            lines.append(f'📌 <b>Nội dung:</b> {preview}')
        if co_quan:
            lines.append(f'🏛 <b>Cơ quan:</b> {co_quan}')
        if ngay:
            lines.append(f'📅 <b>Ngày ban hành:</b> {ngay}')
        if url:
            lines.append(f'🔗 <a href="{url}">Xem văn bản gốc</a>')
        if nguon:
            lines.append(f'📡 <i>Nguồn: {nguon}</i>')

        return '\n'.join(lines)

    # ------------------------------------------------------------------ #
    # Gửi danh sách văn bản mới
    # ------------------------------------------------------------------ #

    def notify_new_docs(self, docs: list) -> int:
        """
        Gửi thông báo cho danh sách văn bản mới.
        Trả về số tin nhắn gửi thành công.
        """
        if not docs:
            return 0

        sent = 0

        # Gửi banner tổng hợp trước
        banner = (
            f'🔔 <b>CẬP NHẬT VĂN BẢN GIÁO DỤC</b>\n'
            f'Tìm thấy <b>{len(docs)}</b> văn bản mới\n'
            f'━━━━━━━━━━━━━━━━━━━━━━━━'
        )
        self.send(banner)

        # Gửi từng văn bản (nhóm tối đa 5 văn bản/tin để tránh flood)
        BATCH = 5
        for i in range(0, len(docs), BATCH):
            batch = docs[i:i + BATCH]
            parts = []
            for j, doc in enumerate(batch, i + 1):
                parts.append(self._format_doc(doc, j, len(docs)))
            msg = '\n\n─────────────────────\n\n'.join(parts)
            if self.send(msg):
                sent += len(batch)

        return sent

    # ------------------------------------------------------------------ #
    # Gửi tin hệ thống (khởi động, lỗi, heartbeat)
    # ------------------------------------------------------------------ #

    def notify_startup(self, total_known: int):
        self.send(
            f'🟢 <b>Hệ thống khởi động</b>\n'
            f'Bot theo dõi văn bản pháp lý giáo dục Việt Nam đã sẵn sàng.\n'
            f'📊 Đang theo dõi <b>{total_known}</b> văn bản hiện có.\n'
            f'⏰ Cập nhật tự động mỗi <b>1 giờ</b>.\n'
            f'━━━━━━━━━━━━━━━━━━━━━━━━\n'
            f'Nguồn: vanban.chinhphu.vn | vbpl.vn | moet.gov.vn'
        )

    def notify_error(self, message: str):
        self.send(f'🔴 <b>Lỗi hệ thống</b>\n<code>{message[:500]}</code>')

    def notify_no_new(self):
        self.send(
            '✅ <b>Kiểm tra hoàn tất</b>\n'
            'Không có văn bản giáo dục mới trong giờ qua.'
        )

    # ------------------------------------------------------------------ #
    # Kiểm tra kết nối bot
    # ------------------------------------------------------------------ #

    def test_connection(self) -> bool:
        """Gọi getMe để xác nhận token hợp lệ."""
        url = TELEGRAM_API.format(token=self.token, method='getMe')
        try:
            resp = requests.get(url, timeout=10)
            data = resp.json()
            if data.get('ok'):
                name = data['result'].get('first_name', '')
                logger.info(f'[Telegram] Kết nối OK — Bot: {name}')
                return True
            logger.error(f'[Telegram] Token lỗi: {data.get("description")}')
            return False
        except Exception as e:
            logger.error(f'[Telegram] Không kết nối được: {e}')
            return False
