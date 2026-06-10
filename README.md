# Văn bản Giáo dục

Thu thập văn bản pháp quy giáo dục VN từ vanban.chinhphu.vn, vbpl.vn, moet.gov.vn → phân loại → Telegram.

> Mới bắt đầu? Đọc [HUONG-DAN.md](HUONG-DAN.md). Tra lệnh? Xem [LENH.md](LENH.md).

---

## Bắt đầu trong 30 giây

```bash
cp .env.example .env      # điền Telegram token vào .env
pip install -r requirements.txt
python main.py            # thu thập ngay
# hoặc python scheduler.py  # chạy tự động
```

---

## Hai loại bước

| Loại | Ví dụ |
|---|---|
| **[CMD]** Lệnh Terminal | `python main.py` |
| **[AGENT]** Nhờ Claude | *"Thêm nguồn văn bản mới"* |

---

## Bản đồ thư mục

```
raw/              dữ liệu gốc bất biến
scrapers/         module crawl từng nguồn  ← KHÔNG di chuyển
notifier/         module Telegram          ← KHÔNG di chuyển
utils/            tiện ích dùng chung      ← KHÔNG di chuyển
data/             văn bản đã thu thập
output/           output nội bộ (tên cũ)
outputs/          export chính thức
wiki/             tài liệu (có README_TELEGRAM.txt)
workshop/         thử nghiệm scraper mới
main.py           entry point
scheduler.py      chạy tự động
config.py         cấu hình nguồn & bộ lọc
.env              Telegram token (không commit)
```
