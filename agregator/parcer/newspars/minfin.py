from .parser import *

class Minfin(Parser):
    """Класс для работы с сайтом https://minfin.gov.ru."""
    
    def __init__(self):
        super().__init__('Minfin', 'https://minfin.gov.ru', 
            'https://minfin.gov.ru/ru/press-center/?q_4=&DATE_from_4=&DATE_to_4=&PUB_DATE_from_4=&PUB_DATE_to_4=&page_4={}')

    def get_article(self, url: str):
        attrs = {'class' : 'text_wrapper'}
        return super().get_article(url, 'div', attrs)        

    def get_news_urls(self, date_from: str = None, date_to: str = None):
        date_from, date_to = self._set_search_dates(date_from, date_to)
        news_urls = dict()
        next_page = True
        page_number = 1
        page = self._get_html_page(self.search_url.format(page_number))
        while page.status_code == 200 and next_page:
            soup = BeautifulSoup(page.text, "html.parser")
            news = soup.findAll('div', class_='news_card_min')
            for item in news:
                date = item.find_all('span', class_='news_date')[0].text
                date = self._format_date(date, '%d.%m.%y')
                if self._check_news_date(date, date_from, date_to):
                    url = item.find_all('a', class_='news_title')[0]
                    header = url.get('title')
                    self._log_article(date, header)
                    news_urls[f'{self.base_url}{url.get("href")}'] = (date.strftime('%Y-%m-%d'), header)
                elif date < date_from:
                    next_page = False # если новость вышла раньше, чем указанный диапазон поиска
                    break
            page_number += 1
            page = self._get_html_page(self.search_url.format(page_number))
        return news_urls