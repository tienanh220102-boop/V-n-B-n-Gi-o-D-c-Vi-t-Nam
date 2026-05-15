"""
Scraper cho vbpl.vn — Cơ sở dữ liệu quốc gia về pháp luật (phiên bản Next.js)
Chiến lược: đọc Sitemap XML để lấy tất cả URL, lọc giáo dục, trích xuất metadata từ slug
"""

import re
import logging
import xml.etree.ElementTree as ET
from urllib.parse import urljoin

from .base import BaseScraper

logger = logging.getLogger(__name__)

BASE_URL = 'https://vbpl.vn'
SITEMAP_INDEX = 'https://vbpl.vn/sitemap.xml'
SOURCE_NAME = 'CSDL Quốc gia Pháp luật (vbpl.vn)'

# Từ khóa nhận diện URL giáo dục trong slug (tiếng Việt không dấu)
EDU_SLUG_KEYWORDS = [
    'giao-duc', 'dao-tao', 'bgddt', 'giang-day', 'hoc-sinh', 'sinh-vien',
    'giao-vien', 'truong-hoc', 'dai-hoc', 'cao-dang', 'mam-non', 'tieu-hoc',
    'trung-hoc', 'hoc-phi', 'chuong-trinh', 'sach-giao-khoa', 'tuyen-sinh',
    'tot-nghiep', 'kiem-dinh', 'giang-vien', 'lop-hoc', 'nha-giao',
    'pho-thong', 'thu-truong', 'hoc-tap', 'giao-duc-thuong-xuyen',
]

# Map slug prefix → tên loại văn bản
DOC_TYPE_MAP = {
    'thong-tu-lien-tich':   'Thông tư liên tịch',
    'thong-tu':             'Thông tư',
    'nghi-dinh':            'Nghị định',
    'quyet-dinh':           'Quyết định',
    'nghi-quyet':           'Nghị quyết',
    'luat':                 'Luật',
    'bo-luat':              'Bộ luật',
    'chi-thi':              'Chỉ thị',
    'cong-van':             'Công văn',
    'thong-bao':            'Thông báo',
    'huong-dan':            'Hướng dẫn',
    'van-ban-hop-nhat':     'Văn bản hợp nhất',
    'nghi-quyet-lien-tich': 'Nghị quyết liên tịch',
}

# Map tên cơ quan từ mã ký hiệu
AGENCY_MAP = {
    'bgddt': 'Bộ Giáo dục và Đào tạo',
    'bldbxh': 'Bộ Lao động - Thương binh và Xã hội',
    'btp': 'Bộ Tư pháp',
    'btc': 'Bộ Tài chính',
    'byt': 'Bộ Y tế',
    'nd-cp': 'Chính phủ',
    'qh15': 'Quốc hội',
    'ttg': 'Thủ tướng Chính phủ',
    'ubnd': 'UBND',
}


class VbplScraper(BaseScraper):

    SOURCE_NAME = SOURCE_NAME

    # ------------------------------------------------------------------ #
    # Đọc danh sách sitemap files từ sitemap index
    # ------------------------------------------------------------------ #

    def _get_sitemap_urls(self):
        """Lấy danh sách tất cả file sitemap từ sitemap index"""
        try:
            resp = self.get(SITEMAP_INDEX)
            root = ET.fromstring(resp.content)
            ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            urls = []
            for sitemap in root.findall('sm:sitemap', ns):
                loc = sitemap.find('sm:loc', ns)
                if loc is not None and loc.text:
                    # Chỉ lấy sitemap trung ương (có văn bản của bộ, ngành TW)
                    if 'trung-uong' in loc.text or 'static' in loc.text:
                        urls.append(loc.text.strip())
            logger.info(f"[VBPL] Tìm thấy {len(urls)} file sitemap trung ương")
            return urls
        except Exception as e:
            logger.error(f"[VBPL] Lỗi đọc sitemap index: {e}")
            return []

    # ------------------------------------------------------------------ #
    # Đọc 1 file sitemap và lọc URL giáo dục
    # ------------------------------------------------------------------ #

    def _parse_sitemap_file(self, sitemap_url):
        """Parse 1 file sitemap XML, trả về list dict {url, lastmod}"""
        try:
            resp = self.get(sitemap_url)
            root = ET.fromstring(resp.content)
            ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            results = []
            for url_elem in root.findall('sm:url', ns):
                loc = url_elem.find('sm:loc', ns)
                lastmod = url_elem.find('sm:lastmod', ns)
                if loc is None or not loc.text:
                    continue
                url = loc.text.strip()
                # Chỉ lấy trang chi tiết văn bản
                if '/van-ban/chi-tiet/' not in url:
                    continue
                # Lọc URL có liên quan giáo dục
                if self._is_edu_url(url):
                    results.append({
                        'url': url,
                        'lastmod': lastmod.text.strip() if lastmod is not None and lastmod.text else '',
                    })
            return results
        except Exception as e:
            logger.error(f"[VBPL] Lỗi parse {sitemap_url}: {e}")
            return []

    def _is_edu_url(self, url):
        """Kiểm tra URL slug có chứa từ khóa giáo dục không"""
        url_lower = url.lower()
        return any(kw in url_lower for kw in EDU_SLUG_KEYWORDS)

    # ------------------------------------------------------------------ #
    # Trích xuất metadata từ URL slug
    # ------------------------------------------------------------------ #

    def _extract_from_slug(self, url, lastmod=''):
        """Trích xuất số hiệu, loại văn bản, cơ quan từ URL slug"""
        # URL dạng: https://vbpl.vn/van-ban/chi-tiet/[slug]--[ID]
        slug_match = re.search(r'/van-ban/chi-tiet/(.+?)(?:--(\d+))?$', url)
        if not slug_match:
            return self.make_doc(url_goc=url, nguon=SOURCE_NAME)

        slug = slug_match.group(1)
        doc_id = slug_match.group(2) or ''

        # Xác định loại văn bản từ đầu slug
        loai_van_ban = ''
        for prefix, name in DOC_TYPE_MAP.items():
            if slug.startswith(prefix):
                loai_van_ban = name
                break

        # Tìm số ký hiệu (e.g., 04-2026-tt-bgddt → 04/2026/TT-BGDĐT)
        so_hieu = self._extract_doc_number(slug)

        # Xác định cơ quan ban hành từ mã trong số ký hiệu
        co_quan = self._extract_agency(so_hieu or slug)

        # Tạo tên văn bản dễ đọc từ slug (bỏ phần số ký hiệu ở đầu)
        ten_van_ban = self._slug_to_title(slug, loai_van_ban, so_hieu)

        # Ngày ban hành từ lastmod hoặc năm trong số ký hiệu
        ngay = self._parse_lastmod(lastmod) or self._year_from_slug(slug)

        return self.make_doc(
            so_hieu=so_hieu,
            ten_van_ban=ten_van_ban,
            loai_van_ban=loai_van_ban,
            co_quan_ban_hanh=co_quan,
            ngay_ban_hanh=ngay,
            url_goc=url,
            nguon=SOURCE_NAME,
            noi_dung='[Xem toàn văn tại URL gốc]',
        )

    def _extract_doc_number(self, slug):
        """Trích xuất số ký hiệu văn bản từ slug

        Các mã ký hiệu điển hình: tt-bgddt, nd-cp, qd-ttg, qh15, ubtvqh
        Giới hạn 1-3 thành phần mã để không lấy phần tiêu đề
        """
        # Các mã cơ quan ban hành thường gặp (viết thường theo slug)
        BODY = r'(?:bgddt|bldtbxh|bldbxh|byt|btc|btp|bca|bqp|bkhdt|bkhcn|bnnptnt|bgtvt|bnv|btttt|cp|ttg|ubtvqh|qh\d*)'

        # Mã loại văn bản (type code) + tối đa 1 mã cơ quan ban hành
        CODE_PATTERN = (
            r'(?:so-)?(\d+)-(\d{4})-'
            r'((?:ttlt|tt|nd|qd|ct|vbhn|cong-van|thong-bao|luat|bo-luat|nghi-quyet)'
            r'(?:-' + BODY + r'(?:-' + BODY + r')?)?'
            r'|ubtvqh|qh\d*|ttg)'
        )
        m = re.search(CODE_PATTERN, slug, re.I)
        if m:
            num = m.group(1)
            year = m.group(2)
            code = m.group(3).upper()
            code = self._normalize_code(code)
            return f"{num}/{year}/{code}"

        # Fallback đơn giản: số-năm-type(-body)?
        m2 = re.search(r'(?:so-)?(\d+)-(\d{4})-([a-z]{1,6})(?:-([a-z]{2,8}))?(?=[^a-z]|$)', slug, re.I)
        if m2:
            num = m2.group(1)
            year = m2.group(2)
            code = m2.group(3).upper()
            if m2.group(4):
                code += '-' + m2.group(4).upper()
            code = self._normalize_code(code)
            return f"{num}/{year}/{code}"
        return ''

    def _normalize_code(self, code):
        """Chuẩn hóa mã ký hiệu: bgddt→BGDĐT, nd-cp→NĐ-CP, qd→QĐ, ttg→TTg"""
        replacements = {
            'BGDDT': 'BGDĐT',
            'BLDBXH': 'BLĐTBXH',
            'BLDTBXH': 'BLĐTBXH',
            'BNNPTNT': 'BNNPTNT',
            'ND-CP': 'NĐ-CP',
            'QD-': 'QĐ-',
            'TTG': 'TTg',
            'TTLT': 'TTLT',
        }
        for old, new in replacements.items():
            code = code.replace(old, new)
        # QĐ khi đứng một mình (không có dấu gạch tiếp theo)
        if code == 'QD':
            code = 'QĐ'
        return code

    def _extract_agency(self, text):
        """Xác định cơ quan ban hành từ mã ký hiệu"""
        text_lower = text.lower()
        for code, name in AGENCY_MAP.items():
            if code in text_lower:
                return name
        return ''

    def _slug_to_title(self, slug, loai, so_hieu):
        """Tạo tên văn bản dễ đọc từ slug (loại bỏ phần số ký hiệu)"""
        # Bỏ phần loại VB ở đầu
        title = slug
        for prefix in DOC_TYPE_MAP.keys():
            if title.startswith(prefix):
                title = title[len(prefix):]
                break
        # Bỏ phần số ký hiệu (so-04-2026-tt-bgddt-)
        title = re.sub(r'^[- ]?(?:so-)?[\d]+-\d{4}-[a-z]+(?:-[a-z]+)*[- ]?', '', title, flags=re.I)
        # Thay dấu gạch ngang bằng khoảng trắng và viết hoa chữ đầu
        title = title.replace('-', ' ').strip().capitalize()
        if so_hieu and loai:
            return f"{loai} {so_hieu}: {title}"
        return title or slug

    def _parse_lastmod(self, lastmod):
        """Chuyển lastmod yyyy-mm-dd → dd/mm/yyyy"""
        m = re.match(r'(\d{4})-(\d{2})-(\d{2})', lastmod or '')
        if m:
            return f"{m.group(3)}/{m.group(2)}/{m.group(1)}"
        return ''

    def _year_from_slug(self, slug):
        """Lấy năm từ slug nếu không có lastmod"""
        m = re.search(r'\b(20\d{2})\b', slug)
        return m.group(1) if m else ''

    # ------------------------------------------------------------------ #
    # Entry point
    # ------------------------------------------------------------------ #

    def scrape(self, max_pages=None, fetch_detail=False):
        """
        Cào vbpl.vn qua Sitemap XML.
        fetch_detail bị bỏ qua (trang dùng React SPA, cần JavaScript để render).
        """
        logger.info(f"[VBPL] Bắt đầu cào {SOURCE_NAME} qua Sitemap XML")
        all_docs = []

        sitemap_files = self._get_sitemap_urls()
        if not sitemap_files:
            logger.error("[VBPL] Không lấy được danh sách sitemap")
            return []

        # Giới hạn số file sitemap nếu có max_pages (mỗi file = 1 "trang")
        if max_pages:
            sitemap_files = sitemap_files[:max_pages]

        for i, smap_url in enumerate(sitemap_files, 1):
            logger.info(f"[VBPL] Đọc sitemap {i}/{len(sitemap_files)}: {smap_url}")
            entries = self._parse_sitemap_file(smap_url)
            logger.info(f"  → {len(entries)} URL giáo dục")

            for entry in entries:
                doc = self._extract_from_slug(entry['url'], entry['lastmod'])
                all_docs.append(doc)

            logger.info(f"[VBPL] Tổng tích lũy: {len(all_docs)} văn bản")

        logger.info(f"[VBPL] Hoàn thành: {len(all_docs)} văn bản")
        return all_docs
