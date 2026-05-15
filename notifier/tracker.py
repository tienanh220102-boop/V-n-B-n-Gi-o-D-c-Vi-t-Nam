"""
Theo dõi văn bản đã gửi để tránh gửi lại.
Lưu state vào data/seen_urls.json.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

STATE_FILE = Path(__file__).parent.parent / 'data' / 'seen_urls.json'


class DocTracker:

    def __init__(self, state_file: Path = STATE_FILE):
        self.state_file = Path(state_file)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self._state = self._load()

    # ------------------------------------------------------------------ #
    # Load / Save
    # ------------------------------------------------------------------ #

    def _load(self) -> dict:
        if self.state_file.exists():
            try:
                with open(self.state_file, encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f'[Tracker] Không đọc được state file: {e} — tạo mới')
        return {'seen_urls': {}, 'last_run': None, 'total_sent': 0}

    def _save(self):
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self._state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f'[Tracker] Không lưu được state: {e}')

    # ------------------------------------------------------------------ #
    # API công khai
    # ------------------------------------------------------------------ #

    def is_new(self, doc: dict) -> bool:
        """Trả về True nếu văn bản này chưa từng được gửi."""
        url = doc.get('url_goc', '')
        so_hieu = doc.get('so_hieu', '')
        # Nhận diện qua URL (ưu tiên) hoặc số hiệu
        key = url or so_hieu
        return bool(key) and key not in self._state['seen_urls']

    def filter_new(self, docs: list) -> list:
        """Lọc ra chỉ những văn bản chưa gửi."""
        return [d for d in docs if self.is_new(d)]

    def mark_seen(self, docs: list):
        """Đánh dấu các văn bản đã gửi."""
        for doc in docs:
            url = doc.get('url_goc', '')
            so_hieu = doc.get('so_hieu', '')
            key = url or so_hieu
            if key:
                self._state['seen_urls'][key] = {
                    'so_hieu': so_hieu,
                    'ten': doc.get('ten_van_ban', '')[:80],
                    'marked_at': datetime.now().isoformat(timespec='seconds'),
                }
        self._state['total_sent'] = self._state.get('total_sent', 0) + len(docs)
        self._save()

    def mark_all_seen(self, docs: list):
        """Đánh dấu hàng loạt (dùng khi khởi động lần đầu)."""
        self.mark_seen(docs)

    def update_last_run(self):
        self._state['last_run'] = datetime.now().isoformat(timespec='seconds')
        self._save()

    @property
    def total_known(self) -> int:
        return len(self._state['seen_urls'])

    @property
    def total_sent(self) -> int:
        return self._state.get('total_sent', 0)

    @property
    def last_run(self) -> str:
        return self._state.get('last_run') or 'Chưa chạy lần nào'

    def is_first_run(self) -> bool:
        return self._state.get('last_run') is None
