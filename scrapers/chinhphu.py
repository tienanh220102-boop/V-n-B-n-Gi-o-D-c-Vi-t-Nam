"""
Scraper cho vanban.chinhphu.vn — Cổng Thông tin điện tử Chính phủ
Trang dùng ASP.NET WebForms: cần xử lý __VIEWSTATE và __doPostBack
"""

import re
import logging
from urllib.parse import urljoin

from .base import BaseScraper
from utils.helpers import detect_doc_type, is_education_related

logger = logging.getLogger(__name__)

SEARCH_URL = 'https://vanban.chinhphu.vn/?groups=1'
BASE_URL = 'https://vanban.chinhphu.vn'
SOURCE_NAME = 'Cổng TTĐT Chính phủ'


class ChinhPhuScraper(BaseScraper):

    SOURCE_NAME = SOURCE_NAME

    # ------------------------------------------------------------------ #
    # Lấy form data từ trang ASP.NET
    # ------------------------------------------------------------------ #

    def _extract_form_data(self, soup):
        """Copy tất cả input hidden/text của form ASP.NET"""
        data = {}
        for inp in soup.find_all('input'):
            name = inp.get('name', '').strip()
            value = inp.get('value', '')
            if name:
                data[name] = value
        # Đặt mặc định cho ASP.NET event
        data.setdefault('__EVENTTARGET', '')
        data.setdefault('__EVENTARGUMENT', '')
        return data

    def _set_education_filter(self, soup, form_data):
        """Tìm dropdown Lĩnh vực và chọn Giáo dục - Đào tạo"""
        for select in soup.find_all('select'):
            options = select.find_all('option')
            for opt in options:
                text = opt.get_text(strip=True)
                if 'Giáo dục' in text or 'giáo dục' in text:
                    field_name = select.get('name', '')
                    if field_name:
                        form_data[field_name] = opt.get('value') or text
                        logger.info(f"Đặt filter lĩnh vực: {field_name} = '{opt.get('value') or text}'")
                        return form_data
        logger.warning("Không tìm thấy dropdown Lĩnh vực — cào tất cả văn bản")
        return form_data

    # ------------------------------------------------------------------ #
    # Tách số hiệu và ngày từ link text chinhphu.vn
    # VD: "807/QĐ-TTg 06/05/2026" → ("807/QĐ-TTg", "06/05/2026")
    # ------------------------------------------------------------------ #

    def _split_link_text(self, text):
        """Tách số ký hiệu và ngày ban hành từ link text chinhphu.vn"""
        if not text:
            return '', ''
        # Tìm ngày ở cuối: dd/mm/yyyy hoặc dd-mm-yyyy
        date_m = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})$', text.strip())
        if date_m:
            ngay = date_m.group(1).replace('-', '/')
            so_hieu = text[:date_m.start()].strip()
            return so_hieu, ngay
        # Tìm ngày bất kỳ vị trí
        date_m = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', text)
        if date_m:
            ngay = date_m.group(1)
            so_hieu = text.replace(date_m.group(0), '').strip()
            return so_hieu, ngay
        return text, ''

    # ------------------------------------------------------------------ #
    # Parse danh sách văn bản từ bảng grvDocument
    # ------------------------------------------------------------------ #

    def _parse_doc_list(self, soup):
        """
        Parse danh sách văn bản từ chinhphu.vn.
        Cấu trúc HTML: các row <tr> chứa:
          span.code        → số ký hiệu
          span.issue-v2    → ngày ban hành
          span.substract   → tên/trích yếu văn bản
          a[download]      → file đính kèm
        """
        docs = []
        seen_urls = set()

        # Tìm tất cả row có chứa span.code (= dòng văn bản)
        rows = soup.find_all('tr')
        data_rows = [r for r in rows if r.find('span', class_='code')]

        if not data_rows:
            # Fallback nếu cấu trúc thay đổi
            logger.debug("Không tìm thấy span.code, dùng fallback links")
            return self._parse_links_fallback(soup)

        for row in data_rows:
            # Số ký hiệu
            code_span = row.find('span', class_='code')
            so_hieu = self.clean_text(code_span.get_text()) if code_span else ''

            # Ngày ban hành
            ngay_span = (
                row.find('span', class_='issue-v2') or
                row.find('span', class_='issued-date')
            )
            ngay = self.clean_text(ngay_span.get_text()) if ngay_span else ''

            # Tên văn bản (trích yếu)
            substract = row.find('span', class_='substract')
            ten = self.clean_text(substract.get_text()) if substract else so_hieu

            # URL gốc — link chứa docid
            doc_link = row.find('a', href=lambda h: h and 'docid=' in h)
            if not doc_link:
                continue
            href = doc_link['href']
            full_url = urljoin(BASE_URL, href) if href.startswith('/') else href

            # Bỏ qua nếu đã thấy URL này (tránh duplicate row cùng văn bản)
            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)

            # File đính kèm
            files = []
            for a in row.find_all('a', href=True):
                if 'datafiles.chinhphu.vn' in a['href'] or a.get('download') is not None:
                    files.append(a['href'])

            doc = self.make_doc(
                so_hieu=so_hieu,
                ten_van_ban=ten,
                ngay_ban_hanh=ngay,
                loai_van_ban=detect_doc_type(ten),
                url_goc=full_url,
                nguon=SOURCE_NAME,
            )
            docs.append(doc)

        return docs

    def _parse_links_fallback(self, soup):
        """Fallback: tìm tất cả links có pattern văn bản"""
        docs = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if 'docid=' not in href and 'chitiet' not in href:
                continue
            full_url = urljoin(BASE_URL, href) if href.startswith('/') else href
            ten = self.clean_text(a.get_text())
            if not ten or len(ten) < 5:
                continue
            docs.append(self.make_doc(
                ten_van_ban=ten,
                loai_van_ban=detect_doc_type(ten),
                url_goc=full_url,
                nguon=SOURCE_NAME,
            ))
        return docs

    # ------------------------------------------------------------------ #
    # Lấy chi tiết văn bản
    # ------------------------------------------------------------------ #

    def _get_doc_detail(self, url):
        """Fetch trang chi tiết và trích xuất đầy đủ thông tin"""
        detail = {}
        try:
            resp = self.get(url)
            soup = self.parse(resp)

            # --- Metadata từ bảng key-value ---
            label_map = {
                'số': 'so_hieu',
                'ký hiệu': 'so_hieu',
                'loại': 'loai_van_ban',
                'cơ quan ban hành': 'co_quan_ban_hanh',
                'cơ quan': 'co_quan_ban_hanh',
                'người ký': 'nguoi_ky',
                'ký bởi': 'nguoi_ky',
                'ngày ban hành': 'ngay_ban_hanh',
                'ngày hiệu lực': 'ngay_hieu_luc',
                'hiệu lực': 'ngay_hieu_luc',
                'trích yếu': 'trich_yeu',
                'tóm tắt': 'trich_yeu',
            }
            for row in soup.find_all('tr'):
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).lower()
                    value = self.clean_text(cells[1].get_text())
                    for key, field in label_map.items():
                        if key in label and not detail.get(field):
                            detail[field] = value
                            break

            # --- Nội dung toàn văn ---
            content_div = (
                soup.find('div', class_=re.compile(r'(box-content|detail|content|toanvan)', re.I)) or
                soup.find('div', id=re.compile(r'(content|main|toanvan)', re.I)) or
                soup.find('article') or
                soup.find('main')
            )
            if content_div:
                detail['noi_dung'] = self.clean_text(content_div.get_text(separator='\n'))

            # --- File đính kèm ---
            files = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                if any(ext in href.lower() for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx']):
                    full = urljoin(BASE_URL, href) if href.startswith('/') else href
                    files.append(full)
                elif 'datafiles.chinhphu.vn' in href:
                    files.append(href)
            detail['file_dinh_kem'] = ' | '.join(set(files))

        except Exception as e:
            logger.error(f"Lỗi chi tiết {url}: {e}")

        return detail

    # ------------------------------------------------------------------ #
    # Phân trang ASP.NET
    # ------------------------------------------------------------------ #

    def _get_control_id(self, soup):
        """Trích xuất control ID dùng trong __doPostBack"""
        pattern = re.compile(r"__doPostBack\('([^']*grvDocument[^']*)'", re.I)
        for script in soup.find_all('script'):
            m = pattern.search(script.get_text())
            if m:
                return m.group(1)
        for tag in soup.find_all(attrs={'onclick': True}):
            m = pattern.search(tag['onclick'])
            if m:
                return m.group(1)
        for a in soup.find_all('a', href=True):
            m = pattern.search(a['href'])
            if m:
                return m.group(1)
        return None

    def _build_page_form(self, soup, base_form, page_num):
        """Tạo form data POST cho trang tiếp theo"""
        ctrl_id = self._get_control_id(soup)
        if not ctrl_id:
            logger.warning("Không tìm thấy control ID phân trang")
            return None

        new_form = dict(base_form)
        # Cập nhật VIEWSTATE từ trang hiện tại
        vs = soup.find('input', id='__VIEWSTATE')
        if vs:
            new_form['__VIEWSTATE'] = vs.get('value', '')
        ev = soup.find('input', id='__EVENTVALIDATION')
        if ev:
            new_form['__EVENTVALIDATION'] = ev.get('value', '')
        vsg = soup.find('input', id='__VIEWSTATEGENERATOR')
        if vsg:
            new_form['__VIEWSTATEGENERATOR'] = vsg.get('value', '')

        new_form['__EVENTTARGET'] = ctrl_id
        new_form['__EVENTARGUMENT'] = f'Page${page_num}'
        return new_form

    def _parse_total_info(self, soup):
        """Lấy tổng số văn bản từ text phân trang"""
        text = soup.get_text()
        m = re.search(r'(\d[\d,\.]*)\s*[-–]\s*(\d[\d,\.]*)\s*[|/]\s*(\d[\d,\.]+)', text)
        if m:
            per_page = int(m.group(2).replace(',', '').replace('.', ''))
            total = int(m.group(3).replace(',', '').replace('.', ''))
            pages = (total + per_page - 1) // per_page
            return pages, total
        return None, None

    # ------------------------------------------------------------------ #
    # Entry point
    # ------------------------------------------------------------------ #

    def scrape(self, max_pages=None, fetch_detail=True):
        logger.info(f"[ChinhPhu] Bắt đầu cào {SOURCE_NAME}")
        all_docs = []

        # Bước 1: GET trang tìm kiếm
        try:
            resp = self.get(SEARCH_URL)
            soup = self.parse(resp)
        except Exception as e:
            logger.error(f"[ChinhPhu] Không tải được trang tìm kiếm: {e}")
            return []

        # Bước 2: Chuẩn bị form + set filter
        form_data = self._extract_form_data(soup)
        form_data = self._set_education_filter(soup, form_data)

        # Bước 3: POST filter để lọc kết quả
        try:
            resp = self.post(SEARCH_URL, data=form_data)
            soup = self.parse(resp)
        except Exception as e:
            logger.warning(f"[ChinhPhu] POST filter thất bại, thử GET: {e}")
            try:
                resp = self.get(SEARCH_URL)
                soup = self.parse(resp)
            except Exception:
                return []

        form_data = self._extract_form_data(soup)
        total_pages, total_docs = self._parse_total_info(soup)
        if total_docs:
            logger.info(f"[ChinhPhu] Tổng số văn bản giáo dục: {total_docs:,} | {total_pages} trang")

        page_num = 1
        prev_urls = set()

        while True:
            if max_pages and page_num > max_pages:
                break

            logger.info(f"[ChinhPhu] Trang {page_num}/{total_pages or '?'}...")
            docs = self._parse_doc_list(soup)

            if not docs:
                logger.info("[ChinhPhu] Không còn văn bản — dừng")
                break

            # Kiểm tra lặp vô tận (trang không thay đổi)
            urls_this_page = {d['url_goc'] for d in docs}
            if urls_this_page and urls_this_page.issubset(prev_urls):
                logger.info("[ChinhPhu] Trang bị lặp — dừng")
                break
            prev_urls.update(urls_this_page)

            if fetch_detail:
                for i, doc in enumerate(docs, 1):
                    url = doc.get('url_goc', '')
                    if url:
                        logger.info(f"  [{i}/{len(docs)}] {doc['ten_van_ban'][:55]}...")
                        detail = self._get_doc_detail(url)
                        for k, v in detail.items():
                            if v and not doc.get(k):
                                doc[k] = v

            all_docs.extend(docs)
            logger.info(f"[ChinhPhu] Đã cào: {len(all_docs)} văn bản")

            # Sang trang tiếp theo
            page_num += 1
            next_form = self._build_page_form(soup, form_data, page_num)
            if not next_form:
                break

            try:
                resp = self.post(SEARCH_URL, data=next_form)
                soup = self.parse(resp)
                form_data = self._extract_form_data(soup)
            except Exception as e:
                logger.error(f"[ChinhPhu] Lỗi trang {page_num}: {e}")
                break

        logger.info(f"[ChinhPhu] Hoàn thành: {len(all_docs)} văn bản")
        return all_docs
