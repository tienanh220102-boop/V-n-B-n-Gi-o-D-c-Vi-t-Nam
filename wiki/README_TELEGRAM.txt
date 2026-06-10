====================================================================
HƯỚNG DẪN TẠO BOT TELEGRAM & CẤU HÌNH HỆ THỐNG
====================================================================

BƯỚC 1 — Tạo bot Telegram (làm 1 lần duy nhất)
────────────────────────────────────────────────
1. Mở Telegram, tìm kiếm @BotFather
2. Gửi lệnh: /newbot
3. Đặt tên bot: VD "Van Ban Giao Duc Bot"
4. Đặt username (phải kết thúc bằng "bot"): VD "vanbangiaoduc_bot"
5. BotFather sẽ trả về TOKEN dạng:
   1234567890:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
6. Lưu lại TOKEN này.


BƯỚC 2 — Lấy Chat ID của bạn
────────────────────────────────────────────────
Cách 1 (đơn giản nhất):
  a. Tìm @userinfobot trên Telegram
  b. Gửi bất kỳ tin nhắn nào cho nó
  c. Nó sẽ trả về "Id: 123456789" — đó là Chat ID của bạn

Cách 2 (dùng API):
  a. Mở trình duyệt, truy cập URL (thay YOUR_TOKEN):
     https://api.telegram.org/botYOUR_TOKEN/getUpdates
  b. Gửi 1 tin nhắn bất kỳ cho bot của bạn trước
  c. Trong JSON trả về, tìm: "chat":{"id":123456789,...}
  d. Số 123456789 chính là Chat ID

Dùng với nhóm (Group):
  a. Thêm bot vào group
  b. Gửi tin nhắn trong group
  c. Dùng API getUpdates, Chat ID của group sẽ là số ÂM, VD: -1001234567890


BƯỚC 3 — Điền thông tin vào config.py
────────────────────────────────────────────────
Mở file config.py, tìm phần TELEGRAM và điền:

  TELEGRAM_BOT_TOKEN = '1234567890:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
  TELEGRAM_CHAT_ID   = '123456789'

Lưu file lại.


BƯỚC 4 — Khởi động bot lần đầu
────────────────────────────────────────────────
Mở terminal (Command Prompt hoặc PowerShell), di chuyển vào thư mục dự án:

  cd "c:\Users\ASUS\Desktop\AI Tiến Anh\Văn bản Giáo dục"

Chạy test trước (không gửi Telegram, kiểm tra kết nối):

  python scheduler.py --test

Nếu mọi thứ OK, chạy chính thức:

  python scheduler.py

Lần đầu chạy: Bot sẽ gửi tin "Hệ thống khởi động" và lưu tất cả văn bản
hiện có làm mốc. Từ giờ sau trở đi, bot chỉ gửi văn bản MỚI xuất hiện.


BƯỚC 5 — Chạy tự động khi khởi động Windows (tùy chọn)
────────────────────────────────────────────────
Thêm vào Windows Task Scheduler:
  1. Mở "Task Scheduler" (tìm trong Start menu)
  2. Tạo task mới:
     - Trigger: "At startup" hoặc "Daily" theo lịch bạn muốn
     - Action: Start a program
       Program: python
       Arguments: scheduler.py
       Start in: c:\Users\ASUS\Desktop\AI Tiến Anh\Văn bản Giáo dục
  3. Tick "Run whether user is logged on or not"


CÁC LỆNH HỮU ÍCH
────────────────────────────────────────────────
  python scheduler.py           # Chạy liên tục (cứ 1 giờ tự cập nhật)
  python scheduler.py --once    # Cập nhật 1 lần rồi thoát
  python scheduler.py --test    # Test kết nối, không gửi Telegram


CẤU TRÚC FILE DATA
────────────────────────────────────────────────
  data/seen_urls.json   — Lưu danh sách URL đã gửi (xóa file này để reset)
  output/scheduler.log  — Log hoạt động của scheduler
  output/*.xlsx         — File Excel kết quả mỗi lần cập nhật


CÂU HỎI THƯỜNG GẶP
────────────────────────────────────────────────
Q: Muốn thay đổi tần suất cập nhật?
A: Sửa SCHEDULE_INTERVAL_HOURS trong config.py (VD: 2 = mỗi 2 giờ)

Q: Muốn dừng bot?
A: Nhấn Ctrl+C trong terminal đang chạy

Q: Muốn reset, gửi lại tất cả văn bản?
A: Xóa file data/seen_urls.json, chạy lại scheduler

Q: Muốn gửi vào group Telegram?
A: Thêm bot vào group, lấy Chat ID của group (số âm), điền vào TELEGRAM_CHAT_ID

====================================================================
