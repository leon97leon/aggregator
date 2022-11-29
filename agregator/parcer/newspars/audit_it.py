from .parser import *

class Audit_it(Parser):
    """Класс для работы с сайтом https://www.audit-it.ru"""

    def __init__(self):
        super().__init__('Audit-it', 'https://www.audit-it.ru',
                         'https://www.audit-it.ru/news/{}')

    def get_article(self, url: str):
        attrs = {'class' : 'block-p-mb30 article-text news-text js-mediator-article'}
        return super().get_article(url, 'div', attrs)

    def get_news_urls(self, date_from: str = None, date_to: str = None):
        date_from, date_to = self._set_search_dates(date_from, date_to)
        news_urls = dict()
        next_page = True
        page_number = 1
        page = self._get_html_page(self.search_url.format(page_number))
        while page.status_code == 200 and next_page:
            soup = BeautifulSoup(page.text, "html.parser")
            news = soup.findAll('div', class_="news-list")
            news_list = news[0].findChildren(recursive=False)
            date = news_list[0].text
            date = self._format_date(date)
            for list_for_date in news_list[1:]:
                for item in list_for_date.findChildren(recursive=False):
                    if item.a is not None:
                        if self._check_news_date(date, date_from, date_to):
                            self._log_article(date, item.a.text)
                            news_urls[f'{self.base_url}{item.a.get("href")}'] = (date.strftime('%Y-%m-%d'), item.a.text)
                    elif 'date-news' in item.attrs['class']:
                        date = self._format_date(item.text)
                        if date < date_from:
                            next_page = False
                            break
            page_number += 1
            page = self._get_html_page(self.search_url.format(page_number))
        return news_urls