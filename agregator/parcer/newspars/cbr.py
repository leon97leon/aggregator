from .parser import *
import json

class CBR(Parser):
    """Класс для работы с сайтом http://cbr.ru"""
    
    def __init__(self):
        super().__init__('CBR', 'http://cbr.ru',
            'http://cbr.ru/news/eventandpress/?IsEng=false&type=100&dateFrom=&dateTo=&Tid=&vol=&phrase=&_=1651044549112&page={}')
    def get_article(self, url: str):
        attrs = {'class' : 'landing-text'}
        return super().get_article(url, 'div', attrs)

    def get_news_urls(self, date_from: str = None, date_to: str = None):
        date_from, date_to = self._set_search_dates(date_from, date_to)
        news_urls = dict()
        next_page = True
        page_number = 0
        page = self._get_html_page(self.search_url.format(page_number))
        while page.status_code == 200 and next_page:
            soup = BeautifulSoup(page.text, "html.parser")
            news = json.loads(soup.text)
            for item in news:
                if item['TBLType'] not in ['interview', 'performance']:
                    date = datetime.strptime(item['DT'], '%Y-%m-%dT%H:%M:%S')
                    if self._check_news_date(date, date_from, date_to):
                        header = requests.utils.unquote(item['name_doc'])
                        if item['TBLType'] == 'events':
                            url = f"https://www.cbr.ru/press/event/?id={item['doc_htm']}"
                        else:
                            url = f"https://www.cbr.ru/press/pr/?file={item['doc_htm']}"
                        self._log_article(date, header)
                        news_urls[url] = (date.strftime('%Y-%m-%d'), header)
                    elif date < date_from:
                        next_page = False # если новость вышла раньше, чем указанный диапазон поиска
                        break
            page_number += 1
            page = self._get_html_page(self.search_url.format(page_number))
        return news_urls