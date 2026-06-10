# Hướng Dẫn Sử Dụng — Văn bản Giáo dục

> Tài liệu cầm tay chỉ việc — không cần biết code.

---

## 1. Dự án này làm gì?

Công cụ này **tự động thu thập văn bản pháp quy giáo dục Việt Nam** từ 3 cổng chính thức (vanban.chinhphu.vn, vbpl.vn, moet.gov.vn), phân loại, lưu trữ và gửi thông báo qua Telegram khi có văn bản mới.

---

## 2. Chuẩn bị (làm 1 lần)

1. Copy file môi trường: `.env.example` → `.env`
2. Điền Telegram Bot Token và Chat ID vào `.env`
3. Cài thư viện:
   ```
   pip install -r requirements.txt
   ```
Xem `wiki/README_TELEGRAM.txt` để biết cách lấy Telegram token.

---

## 3. Hai nơi thao tác

| Nơi | Là gì |
|---|---|
| **Terminal** | Gõ `python main.py` để thu thập ngay |
| **Khung chat Claude** | Nói tiếng Việt, AI tự làm |

---

## 4. Thu thập văn bản

**Thu thập ngay:**
```
python main.py
```

**Chạy tự động theo lịch:**
```
python scheduler.py
```

---

## 5. Kết quả ở đâu?

| Mục đích | File / Nơi |
|---|---|
| **Văn bản đã thu thập** | `data/` — JSON/text các văn bản |
| **Output nội bộ** | `output/` (tên cũ, giữ nguyên) |
| **Export chính thức** | `outputs/` |

---

## 6. FAQ

- **Không nhận Telegram** → Kiểm tra Bot Token và Chat ID trong `.env`; xem `wiki/README_TELEGRAM.txt`
- **Thêm nguồn văn bản mới** → Nói với AI: *"Thêm nguồn [URL] vào scrapers"*
- **Lọc theo loại văn bản** → Nói với AI: *"Chỉ lấy thông tư, nghị định"*
- **Không biết làm gì** → `python main.py --help` hoặc hỏi AI
