# Lệnh Thường Dùng — Văn bản Giáo dục

> **[CMD]** = gõ Terminal | **[AGENT]** = nhờ Claude làm

---

## 1. Thu thập văn bản

| Lệnh | Loại | Làm gì | Khi nào dùng |
|---|---|---|---|
| `python main.py` | [CMD] | Thu thập ngay tất cả nguồn | Thu công |
| `python scheduler.py` | [CMD] | Chạy tự động theo lịch | Để chạy nền liên tục |

## 2. Cấu hình & tùy chỉnh

| Lệnh | Loại | Làm gì |
|---|---|---|
| *"Thêm nguồn [URL/tên cổng]"* | [AGENT] | Thêm scraper mới vào `scrapers/` |
| *"Chỉ lấy thông tư, nghị định"* | [AGENT] | Sửa bộ lọc trong `config.py` |
| *"Xem cấu hình hiện tại"* | [AGENT] | Đọc `config.py` |

## 3. Telegram & thông báo

| Lệnh | Loại | Làm gì |
|---|---|---|
| *"Kiểm tra Telegram"* | [AGENT] | Xem `.env` + test gửi tin |
| Xem `wiki/README_TELEGRAM.txt` | — | Hướng dẫn cấu hình bot |

## 4. Dev & test

| Lệnh | Loại | Làm gì |
|---|---|---|
| `pip install -r requirements.txt` | [CMD] | Cài thư viện |
| `pytest tests/` | [CMD] | Chạy test suite |

---

**Output:** `data/` (văn bản) · `output/` (nội bộ) · `outputs/` (export)
