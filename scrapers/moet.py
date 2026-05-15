"""
Scraper cho moet.gov.vn — Bộ Giáo dục và Đào tạo
Lưu ý: SSL bị reset, phải dùng verify=False
Cấu trúc: div.items.padding-xs chứa từng văn bản với bảng thuộc tính ẩn
"""

import re
import logging
import warnings
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .base import BaseScraper
from utils.helpers import detect_doc_type

warnings.filterwarnings('ignore', message='Unverified HTTPS request')
logger = logging.getLogger(__name__)

BASE_URL = 'https://moet.gov.vn'
SOURCE_NAME = 'Bộ Giáo dục và Đào tạo (moet.gov.vn)'

# Trang danh sách văn bản (van-ban-quy-pham-phap-luat + chi-dao-dieu-hanh)
CATEGORY_URLS = [
    'https://moet.gov.vn/van-ban/van-ban-quy-pham-phap-luat',
    'https://moet.gov.vn/van-ban/van-ban-chi-dao-dieu-hanh',
]


class MoetScraper(BaseScraper):

    SOURCE_NAME = SOURCE_NAME

    def get(self, url, **kwargs):
        """Override để tắt SSL verify cho moet.gov.vn"""
        kwargs.setdefault('verify', False)
        return super().get(url, **kwargs)

    def post(self, url, data=None, **kwargs):
        kwargs.setdefault('verify', False)
        return super().post(url, data=data, **kwargs)

    # ------------------------------------------------------------------ #
    # Parse danh sách văn bản
    # ------------------------------------------------------------------ #

    def _parse_doc_list(self, soup, category_name):
        """Parse các card div.items từ trang danh sách"""
        docs = []
        items = soup.find_all('div', class_='items')

        for item in items:
            # Lấy link và số ký hiệu từ title
            title_div = item.find('div', class_='title')
            if not title_div:
                continue
            link = title_div.find('a', href=True)
            if not link:
                continue

            href = link['href']
            full_url = urljoin(BASE_URL, href) if not href.startswith('http') else href
            so_hieu_raw = self.clean_text(link.get_text())

            # Lấy tên văn bản từ div bên trái (border-right)
            ten_div = item.find('div', class_=re.compile(r'width-col-md-6.*border-right|border-right.*width-col-md-6'))
            ten_van_ban = self.clean_text(ten_div.get_text()) if ten_div else ''

            # Lấy metadata từ bảng thuộc tính ẩn
            props = {}
            prop_table = item.find('div', class_='properties')
            if prop_table:
                for row in prop_table.find_all('tr'):
                    cells = row.find_all(['th', 'td'])
                    # Bảng có 2 hoặc 4 ô mỗi hàng
                    for i in range(0, len(cells) - 1, 2):
                        label = cells[i].get_text(strip=True).lower()
                        value = self.clean_text(cells[i+1].get_text())
                        props[label] = value

            so_hieu = props.get('số ký hiệu', so_hieu_raw)
            loai = props.get('loại văn bản', detect_doc_type(so_hieu_raw or ten_van_ban))
            ngay = props.get('ngày ban hành', '')
            linh_vuc = props.get('lĩnh vực', '')
            hieu_luc = props.get('tình trạng hiệu lực', '')

            # Tên đầy đủ = loại + số + tiêu đề
            if not ten_van_ban and loai:
                ten_van_ban = f"{loai} {so_hieu}"

            doc = self.make_doc(
                so_hieu=so_hieu,
                ten_van_ban=ten_van_ban,
                loai_van_ban=loai,
                co_quan_ban_hanh='Bộ Giáo dục và Đào tạo',
                ngay_ban_hanh=ngay,
                trich_yeu=linh_vuc,
                url_goc=full_url,
                nguon=SOURCE_NAME,
                noi_dung='[Toàn văn trong file đính kèm — xem URL gốc]',
            )
            docs.append(doc)

        return docs

    # ------------------------------------------------------------------ #
    # Lấy file đính kèm từ trang chi tiết
    # ------------------------------------------------------------------ #

    def _get_file_links(self, url):
        """Lấy link file PDF/Word từ trang chi tiết"""
        try:
            resp = self.get(url)
            soup = self.parse(resp)
            files = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                if any(ext in href.lower() for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx']):
                    full = urljoin(BASE_URL, href) if not href.startswith('http') else href
                    files.append(full)
            return ' | '.join(set(files))
        except Exception as e:
            logger.debug(f"[MOET] Lỗi lấy file {url}: {e}")
            return ''

    # ------------------------------------------------------------------ #
    # Entry point
    # ------------------------------------------------------------------ #

    def scrape(self, max_pages=None, fetch_detail=True):
        logger.info(f"[MOET] Bắt đầu cào {SOURCE_NAME}")
        all_docs = []

        categories_to_scrape = CATEGORY_URLS[:max_pages] if max_pages else CATEGORY_URLS

        for cat_url in categories_to_scrape:
            cat_name = cat_url.split('/')[-1]
            logger.info(f"[MOET] Danh mục: {cat_name}")

            try:
                resp = self.get(cat_url)
                if resp.status_code != 200:
                    logger.warning(f"[MOET] {cat_url} trả về {resp.status_code}")
                    continue
            except Exception as e:
                logger.error(f"[MOET] Không kết nối được {cat_url}: {e}")
                continue

            soup = self.parse(resp)
            docs = self._parse_doc_list(soup, cat_name)

            if not docs:
                logger.warning(f"[MOET] Không tìm thấy văn bản trong {cat_name}")
                continue

            logger.info(f"  → {len(docs)} văn bản từ {cat_name}")

            # Lấy file đính kèm từ trang chi tiết
            if fetch_detail:
                for i, doc in enumerate(docs, 1):
                    url = doc.get('url_goc', '')
                    if url:
                        logger.info(f"  [{i}/{len(docs)}] {doc['so_hieu']} — Lấy file...")
                        doc['file_dinh_kem'] = self._get_file_links(url)

            all_docs.extend(docs)
            logger.info(f"[MOET] Tổng tích lũy: {len(all_docs)} văn bản")

        logger.info(f"[MOET] Hoàn thành: {len(all_docs)} văn bản")
        return all_docs
