from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime, date

import warnings
warnings.filterwarnings('ignore')

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'

class Parser:
    '''Базовый класс для извлечения статей из новостных ресурсов'''
    def __init__(self, name:str, base_url: str, search_url: str = ''):
        self.name = name
        self.base_url = base_url
        self.search_url = search_url

    def __repr__(self):
        return f"{self.name} {self.base_url.split('//')[1].replace('www.','')}"


    def get_article(self, url: str, element: str, attrs: dict={}):
        """Функция получения текста новости."""
        soup = BeautifulSoup(self._get_html_page(url).text, "html.parser")
        article = soup.findAll(element, attrs)
        if article:
            return article[0].text
        else:
            return 'Can not parse'


    def get_news_urls(self, query: str, date_from: str, date_to: str):
        """Функция получения словаря с ссылками, датами и заголовками новостей.
        ----
        Возвращает словаль, который содержит ссылку на новость как ключ и кортеж из
        даты и заголовка новости в качестве элемента:
        ```
        { 'ссылка_на_новость' : ('дата_новости', 'заголовок_новости') }
        ```
        """
        raise NotImplementedError("Please Implement this method")

    def _get_html_page(self, url) -> requests.models.Response:
        """Функция получения html кода страницы."""
        headers = {'User-Agent': USER_AGENT}
        session = requests.Session()
        adapter = HTTPAdapter(max_retries=Retry(connect=3, backoff_factor=0.5))
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        try:
            page = session.get(url, verify=False, headers=headers)
        except requests.exceptions.RequestException as e:
            page = requests.models.Response()
        return page

    def _set_search_dates(self, date_from:str=None, date_to:str=None, fmt:str='%d.%m.%Y'):
        """Функция для установки временного интервала поиска статей."""
        if date_from is None:
            date_from = self._get_current_date()
        else:
            date_from = datetime.strptime(date_from, fmt)
        if date_to is None:
            date_to = self._get_current_date()
        else:
            date_to = datetime.strptime(date_to, fmt)
        
        return date_from, date_to

    def _get_current_date(self):
        """Функция получения текущей даты для поиска."""
        current_date = datetime.now()
        return datetime.strptime(f"{current_date.day:02}.{current_date.month:02}.{current_date.year}", '%d.%m.%Y')

    def _check_news_date(self, post_date: str, date_from: str = None, date_to: str = None) -> bool:
        """Функция проверяет, входит ли дата публикации новости в интересуемый интервал."""
        if date_from is None:
            date_from = self._get_current_date()
        if date_to is None:
            date_to = self._get_current_date()
        return date_from <= post_date <= date_to

    def _format_date(self, date_: str, fmt: str='%d.%m.%Y') -> datetime:
        """Функция приведения даты к унифицированному формату."""
        month_dict = {
            ' января '  : '.01.',
            ' февраля ' : '.02.',
            ' марта '   : '.03.',
            ' апреля '  : '.04.',
            ' мая '     : '.05.',
            ' июня '    : '.06.',
            ' июля '    : '.07.',
            ' августа ' : '.08.',
            ' сентября ': '.09.',
            ' октября ' : '.10.',
            ' ноября '  : '.11.',
            ' декабря ' : '.12.'
        }
        for key in month_dict.keys():
            date_ = date_.replace(key, month_dict[key])
        return datetime.strptime(date_, fmt)

    def _log_article(self, date:date, header:str):
        print(date.strftime('%Y-%m-%d'), header[:100] + ('...' if len(header) > 100 else ''))