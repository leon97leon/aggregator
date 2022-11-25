from .parser import *

class Gaap(Parser):
    """Класс для работы с сайтом https://gaap.ru"""

    def __init__(self):
        super().__init__('Gaap', 'https://gaap.ru',
                         'https://gaap.ru/news/?PAGEN_1={}')

    def get_article(self, url: str):
        attrs = {'class' : 'article-detail-text'}
        return super().get_article(url, 'div', attrs)

    def get_news_urls(self, date_from: str = None, date_to: str = None):
        date_from, date_to = self._set_search_dates(date_from, date_to)
        news_urls = dict()
        next_page = True
        page_number = 1
        page = self._get_html_page(self.search_url.format(page_number))
        while page.status_code == 200 and next_page:
            soup = BeautifulSoup(page.text, "html.parser")
            news = soup.findAll('div', class_="news-blocks")
            news_list = news[0].findChildren(recursive=False)
            date = news_list[0].find_all('span', class_='date')[0]
            date = self._format_date(date.text)
            for item in news_list[1].findChildren(recursive=False):
                if item.a is not None:
                    if self._check_news_date(date, date_from, date_to):
                        self._log_article(date, item.a.text)
                        news_urls[f'{self.base_url}{item.a.get("href")}'] = (date.strftime('%Y-%m-%d'), item.a.text)                       
                elif item.find_all('span', class_='date'):
                    date = self._format_date(item.find_all('span', class_='date')[0].text)
                    if date < date_from:
                        next_page = False
                        break
            page_number += 1
            page = self._get_html_page(self.search_url.format(page_number))
        return news_urls