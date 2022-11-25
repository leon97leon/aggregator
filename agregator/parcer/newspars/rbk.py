from .parser import *
import json

class RBK(Parser):
    """Класс для работы с сайтом https://www.rbc.ru."""
    
    def __init__(self):
        url_first_part = 'https://www.rbc.ru/v10/ajax/get-news-feed/project/rbcnews.uploaded/lastDate/'
        url_second_part = f'/limit/50?_={int(datetime.timestamp(datetime.now()))*1000}'  # Здесь 50 - количество новостей в выдаче
        self.allow_domens = ["trends.rbc.ru","plus.rbc.ru","pro.rbc.ru","quote.rbc.ru","realty.rbc.ru","marketing.rbc.ru","www.rbc.ru/economics","www.rbc.ru/finances"]
        super().__init__('RBK', 'https://www.rbc.ru', 
                         url_first_part+'{}'+url_second_part)

    def get_article(self, url: str):
        """Функция получения текста новости."""
        soup = BeautifulSoup(self._get_html_page(url).text, "html.parser")
        [item.a.decompose() for item in soup.find_all('p') if item.a]
        article = '\r\n'.join([item.text for item in soup.find_all('p') if not item.find_all('div')])
        if article:
            return article
        else:
            return 'Can not parse'
        # return super().get_article(url, 'div', 'article__text')

    def get_news_urls(self, date_from: str = None, date_to: str = None):
        date_from, date_to = self._set_search_dates(date_from, date_to)
        news_urls = dict()
        next_page = True
        page_number = int(datetime.timestamp(datetime.strptime(date_to.strftime("%Y-%m-%d 23:59:59"), "%Y-%m-%d %H:%M:%S")))
        page = self._get_html_page(self.search_url.format(page_number))
        while page.status_code == 200 and next_page:
            news = json.loads(page.text)
            for item in news['items']:
                html = item['html']
                soup = BeautifulSoup(html, "html.parser")
                date = datetime.fromtimestamp(item['publish_date_t'])
                header = soup.find_all('span', class_='news-feed__item__title')[0].text.strip()
                url = soup.a.get('href')
                page_number = int(datetime.timestamp(date))
                if self._check_news_date(date, date_from, date_to):
                    if all(domen not in url for domen in self.allow_domens):
                        continue
                    self._log_article(date, header)
                    news_urls[url] = (date.strftime('%Y-%m-%d'), header)
                elif date < date_from:
                    next_page = False # если новость вышла раньше, чем указанный диапазон поиска
                    break
            page = self._get_html_page(self.search_url.format(page_number))
        return news_urls