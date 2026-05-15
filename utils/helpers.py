import re

# Từ điển nhận diện loại văn bản
_DOC_TYPE_PATTERNS = [
    ('Thông tư liên tịch', r'th[ôo]ng t[ưu] li[eê]n t[ịi]ch'),
    ('Thông tư',           r'th[ôo]ng t[ưu](?! li[eê]n)'),
    ('Nghị định',          r'ngh[ịi] [dđ][iị]nh'),
    ('Quyết định',         r'quy[eế]t [dđ][iị]nh'),
    ('Nghị quyết',         r'ngh[ịi] quy[eế]t'),
    ('Luật',               r'^lu[aậ]t\s'),
    ('Chỉ thị',            r'ch[iỉ] th[iị]'),
    ('Công văn',           r'c[ôo]ng v[aă]n'),
    ('Thông báo',          r'th[ôo]ng b[aá]o'),
    ('Quy định',           r'quy [dđ][iị]nh'),
]


def detect_doc_type(text):
    """Nhận diện loại văn bản từ tiêu đề"""
    if not text:
        return ''
    text_lower = text.lower()
    for doc_type, pattern in _DOC_TYPE_PATTERNS:
        if re.search(pattern, text_lower):
            return doc_type
    return ''


_EDUCATION_KEYWORDS = [
    'giáo dục', 'đào tạo', 'học sinh', 'sinh viên', 'giáo viên',
    'trường học', 'đại học', 'cao đẳng', 'mầm non', 'tiểu học',
    'trung học', 'học phí', 'chương trình', 'bgdđt', 'bộ gd',
    'sách giáo khoa', 'tuyển sinh', 'tốt nghiệp', 'kiểm định',
    'phổ thông', 'dạy học', 'giảng dạy', 'nhà trường', 'lớp học',
]


def is_education_related(text):
    """Kiểm tra văn bản có liên quan đến giáo dục không"""
    if not text:
        return False
    text_lower = text.lower()
    return any(kw in text_lower for kw in _EDUCATION_KEYWORDS)


def parse_date(date_str):
    """Chuẩn hóa chuỗi ngày tháng Việt Nam"""
    if not date_str:
        return ''
    # dd/mm/yyyy hoặc dd-mm-yyyy
    m = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', str(date_str))
    if m:
        d, mo, y = m.group(1), m.group(2), m.group(3)
        return f"{d.zfill(2)}/{mo.zfill(2)}/{y}"
    # yyyy-mm-dd
    m = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', str(date_str))
    if m:
        y, mo, d = m.group(1), m.group(2), m.group(3)
        return f"{d.zfill(2)}/{mo.zfill(2)}/{y}"
    # "ngày DD tháng MM năm YYYY"
    m = re.search(r'ng[aà]y\s+(\d{1,2})\s+th[aá]ng\s+(\d{1,2})\s+n[aă]m\s+(\d{4})', str(date_str), re.I)
    if m:
        return f"{m.group(1).zfill(2)}/{m.group(2).zfill(2)}/{m.group(3)}"
    return str(date_str).strip()
