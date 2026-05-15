import time
import random
import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class BaseScraper:
    HEADERS = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/124.0.0.0 Safari/537.36'
        ),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

    def __init__(self, delay=2, max_retries=3, timeout=30):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self.delay = delay
        self.max_retries = max_retries
        self.timeout = timeout

    def _wait(self):
        time.sleep(self.delay + random.uniform(0.3, 1.2))

    def get(self, url, **kwargs):
        for attempt in range(self.max_retries):
            try:
                self._wait()
                resp = self.session.get(url, timeout=self.timeout, **kwargs)
                resp.raise_for_status()
                return resp
            except requests.exceptions.RequestException as e:
                logger.warning(f"GET lần {attempt + 1}/{self.max_retries} | {url} | {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise

    def post(self, url, data=None, **kwargs):
        for attempt in range(self.max_retries):
            try:
                self._wait()
                resp = self.session.post(url, data=data, timeout=self.timeout, **kwargs)
                resp.raise_for_status()
                return resp
            except requests.exceptions.RequestException as e:
                logger.warning(f"POST lần {attempt + 1}/{self.max_retries} | {url} | {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise

    def parse(self, response):
        return BeautifulSoup(response.content, 'lxml')

    def clean_text(self, text):
        if not text:
            return ''
        return ' '.join(str(text).split()).strip()

    def make_doc(self, **kwargs):
        """Tạo dict chuẩn cho một văn bản"""
        template = {
            'so_hieu': '',
            'ten_van_ban': '',
            'loai_van_ban': '',
            'co_quan_ban_hanh': '',
            'nguoi_ky': '',
            'ngay_ban_hanh': '',
            'ngay_hieu_luc': '',
            'trich_yeu': '',
            'noi_dung': '',
            'file_dinh_kem': '',
            'url_goc': '',
            'nguon': '',
        }
        template.update(kwargs)
        return template
