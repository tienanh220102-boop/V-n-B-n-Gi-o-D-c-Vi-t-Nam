# Claude Notes — Văn bản Giáo dục

## Kiến trúc script

- **`scripts/main.py`**: entry point chính — cào văn bản từ chinhphu.vn, vbpl.vn, moet.gov.vn
- **`scripts/scheduler.py`**: chạy liên tục hoặc 1 lần, gửi Telegram khi có văn bản mới
- **`config.py`**: cấu hình ở ROOT (KHÔNG di chuyển vào scripts/) — vì `main.py` và `scheduler.py` import nó qua sys.path
- **Modules không di chuyển**: `scrapers/`, `notifier/`, `utils/` — import theo đường dẫn tương đối từ project root

## sys.path pattern (quan trọng)

```python
# scripts/main.py và scripts/scheduler.py đều dùng:
sys.path.insert(0, str(Path(__file__).parent.parent))
# → Thêm project ROOT vào path → from scrapers.xxx import, from config import hoạt động
```

Đây là lý do `config.py` phải ở root, KHÔNG ở scripts/.

## Output directory

- **`output/`** (singular) — đây là thư mục ACTIVE, được set trong `config.py` (`OUTPUT_DIR = 'output'`)
- **`outputs/`** — folder template, KHÔNG dùng bởi script hiện tại
- `main.py` tự tạo `output/` nếu chưa có: `Path(output_dir).mkdir(parents=True, exist_ok=True)`

## Biến môi trường

- `TELEGRAM_BOT_TOKEN` — dùng trong `scheduler.py` để gửi thông báo văn bản mới

## Quirks quan trọng

- **Không có .bat file** — chạy tay: `python scripts/main.py` hoặc `python scripts/scheduler.py`
- **`output/` vs `outputs/`**: dự án này dùng `output/` (singular) từ trước khi có template — KHÔNG đổi sang `outputs/` vì sẽ phải sửa config.py và tất cả script

## Lịch sử thay đổi

- 2026-06: Chuyển `main.py` và `scheduler.py` từ root → `scripts/`; sửa `sys.path.insert` từ `.parent` → `.parent.parent`
- `config.py` giữ nguyên ở root — nếu chuyển vào scripts/ sẽ phá vỡ `from config import` ở nhiều chỗ
