from .parser import *

class IIA(Parser):
    """Класс для работы с сайтом https://www.iia-ru.ru"""
    
    def __init__(self):
        super().__init__('IIA', 'https://www.iia-ru',
                         'https://www.iia-ru.ru/news/?PAGEN_1={}')

    def get_article(self, url: str):
        attrs = {'class' : 'novost_contain'}
        return super().get_article(url, 'div', attrs)        

    def get_news_urls(self, date_from: str = None, date_to: str = None):
        date_from, date_to = self._set_search_dates(date_from, date_to)
        news_urls = dict()
        next_page = True
        page_number = 1
        page = self._get_html_page(self.search_url.format(page_number))
        while page.status_code == 200 and next_page:
            soup = BeautifulSoup(page.text, "html.parser")
            news = soup.findAll('div', class_="novosti_box_text")
            links = [item.a.get('href') for item in news]
            dates = [item.h4.text.strip() for item in news]
            headers = [item.a.text for item in news]
            for d, link, header in zip(dates, links, headers):
                date = self._format_date(d)
                if self._check_news_date(date, date_from, date_to):
                    self._log_article(date, header)
                    news_urls[f"{self.base_url}{link}"] = (date.strftime('%Y-%m-%d'), header)
                elif date < date_from: 
                    next_page = False # если новость вышла раньше, чем указанный диапазон поиска
                    break
            page_number += 1
            page = self._get_html_page(self.search_url.format(page_number))
        return news_urls