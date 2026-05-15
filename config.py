# =============================================================
# CẤU HÌNH DỰ ÁN CÀO VĂN BẢN GIÁO DỤC VIỆT NAM
# =============================================================

SOURCES = {
    'chinhphu': {
        'name': 'Cổng TTĐT Chính phủ (vanban.chinhphu.vn)',
        'search_url': 'https://vanban.chinhphu.vn/?groups=1',
        'base_url': 'https://vanban.chinhphu.vn',
        'enabled': True,
    },
    'vbpl': {
        'name': 'CSDL Quốc gia Pháp luật (vbpl.vn)',
        'search_url': 'https://vbpl.vn/pages/vbpq-timkiem.aspx',
        'base_url': 'https://vbpl.vn',
        'bgddt_urls': [
            'https://vbpl.vn/bogiaoducdaotao/Pages/vanban.aspx',
            'https://vbpl.vn/TW/Pages/vbpq-timkiem.aspx',
            'https://vbpl.vn/pages/vbpq-timkiem.aspx',
        ],
        'enabled': True,
    },
    'moet': {
        'name': 'Bộ Giáo dục và Đào tạo (moet.gov.vn)',
        'search_urls': [
            'https://moet.gov.vn/van-ban/van-ban-phap-ly/Pages/default.aspx',
            'https://moet.gov.vn/van-ban/Pages/home.aspx',
            'https://moet.gov.vn/Pages/vanban.aspx',
        ],
        'base_url': 'https://moet.gov.vn',
        'enabled': True,
    },
}

# Loại văn bản cần thu thập
DOC_TYPES = [
    'Thông tư',
    'Nghị định',
    'Quyết định',
    'Nghị quyết',
    'Luật',
    'Thông tư liên tịch',
    'Chỉ thị',
    'Quy định',
    'Thông báo',
    'Công văn',
]

# Từ khóa nhận diện văn bản giáo dục
EDUCATION_KEYWORDS = [
    'giáo dục', 'đào tạo', 'trường học', 'đại học', 'cao đẳng',
    'phổ thông', 'mầm non', 'tiểu học', 'trung học', 'học sinh',
    'sinh viên', 'giáo viên', 'học phí', 'chương trình', 'bgdđt',
    'sách giáo khoa', 'tuyển sinh', 'tốt nghiệp', 'kiểm định',
]

# Cài đặt kỹ thuật
REQUEST_DELAY = 2       # Giây chờ giữa các request (tôn trọng server)
MAX_RETRIES = 3         # Số lần thử lại khi lỗi
TIMEOUT = 30            # Timeout mỗi request (giây)
MAX_PAGES = None        # None = cào hết; đặt số nguyên để giới hạn
OUTPUT_DIR = 'output'   # Thư mục lưu kết quả

# =============================================================
# CẤU HÌNH TELEGRAM BOT
# =============================================================
# Khi chạy LOCAL: điền trực tiếp vào đây
# Khi chạy GitHub Actions: để trống, hệ thống tự đọc từ GitHub Secrets
import os as _os

TELEGRAM_BOT_TOKEN = _os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID   = _os.environ.get('TELEGRAM_CHAT_ID', '')

# Cài đặt scheduler
SCHEDULE_INTERVAL_HOURS = 1    # Cập nhật mỗi N giờ (chỉ dùng khi chạy local)
SAVE_EXCEL_ON_UPDATE    = False  # Tắt lưu Excel khi chạy trên GitHub Actions
