# Văn bản Giáo dục — Hướng dẫn vận hành cho Agent

Dự án này: thu thập tự động văn bản pháp quy giáo dục Việt Nam từ các cổng chính thức (vanban.chinhphu.vn, vbpl.vn, moet.gov.vn) → phân loại, lưu trữ, thông báo qua Telegram.

---

## §0. Bảng vận hành nhanh

| User muốn | Agent làm gì |
|---|---|
| "thu thập văn bản mới" | `python scripts/main.py` |
| "chạy tự động theo lịch" | `python scripts/scheduler.py` |
| "xem cấu hình nguồn" | Đọc `config.py` |
| "kết quả ở đâu" | Thư mục `output/` — Excel + log |
| "xem log / lỗi" | `output/scraper.log` hoặc `output/scheduler.log` |
| "chạy test" | `pytest tests/` |
| "hướng dẫn Telegram" | Đọc `wiki/README_TELEGRAM.txt` |
| "permissions Claude Code" | `.claude/settings.json` |

**Quy tắc cho agent:**
- Module nội bộ (`notifier/`, `scrapers/`, `utils/`) — không di chuyển, các script import theo đường dẫn tương đối.
- `main.py`, `scheduler.py`, `config.py` ở root — không chuyển vào `scripts/`, import sẽ hỏng.
- `output/` là thư mục hoạt động thực tế (config: `OUTPUT_DIR = 'output'`). `outputs/` là staging, chưa dùng.
- Secrets (Telegram token, API keys) trong `.env`.

---

## Kiến trúc pipeline

```
vanban.chinhphu.vn / vbpl.vn / moet.gov.vn
  └── scrapers/          → thu thập văn bản
        └── main.py      → điều phối toàn bộ
              ├── utils/ → xử lý, phân loại
              ├── data/  → lưu trữ văn bản
              └── notifier/ → gửi Telegram
  └── scheduler.py       → chạy tự động theo cron
  └── .github/workflows/ → GitHub Actions (send_latest, scheduler)
```

---

## Cấu trúc thư mục

| Thư mục/File | Mục đích |
|---|---|
| `scripts/main.py` | Entry point — chạy toàn bộ pipeline |
| `scripts/scheduler.py` | Scheduler tự động |
| `config.py` | Cấu hình nguồn, bộ lọc, OUTPUT_DIR (ở root, KHÔNG di chuyển) |
| `scrapers/` | Module crawl từng nguồn |
| `notifier/` | Module gửi Telegram |
| `utils/` | Tiện ích dùng chung |
| `data/` | Văn bản đã thu thập, cache (`seen_urls.json`) |
| `output/` | **Thư mục hoạt động**: Excel output + log |
| `outputs/` | Staging export (hiện chưa dùng) |
| `raw/` | Dữ liệu thô gốc (bất biến) |
| `scripts/` | Helper scripts tương lai (hiện rỗng) |
| `prompts/` | Prompt LLM tái sử dụng (hiện rỗng) |
| `review/` | Tài liệu review output (hiện rỗng) |
| `tests/` | Test files pytest (hiện rỗng) |
| `wiki/` | Tài liệu nội bộ (`README_TELEGRAM.txt`) |
| `workshop/` | Thử nghiệm sandbox |
| `.claude/` | Cấu hình Claude Code: permissions, hooks |
| `.github/workflows/` | GitHub Actions: `send_latest.yml`, `scheduler.yml` |
| `.env` | Secrets (Telegram Bot Token, Chat ID) |
| `.env.example` | Template `.env` — an toàn để commit |

---

## Quy tắc làm việc

1. **Không di chuyển module** (`scrapers/`, `notifier/`, `utils/`, `config.py`) — imports sẽ hỏng. `main.py` và `scheduler.py` đã nằm trong `scripts/` và dùng `sys.path.insert(0, Path(__file__).parent.parent)` để import đúng.
2. **Secrets trong `.env`** — đặc biệt Telegram Bot Token và Chat ID.
3. **Workshop trước production** — thử scraper mới trong `workshop/` trước.
4. **Thêm nguồn mới** — sửa `config.py`, thêm module trong `scrapers/`.
5. **Thêm prompt LLM** — đặt vào `prompts/`, không hardcode trong scripts.
6. **Kế thừa, không đập lại** — mọi thay đổi phải build trên code đang chạy, không viết lại từ đầu.
