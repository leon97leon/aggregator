from .parser import *

class Consultant(Parser):
    """Класс для работы с сайтом http://www.consultant.ru"""
    
    def __init__(self):
        super().__init__('Consultant', 'http://www.consultant.ru',
            'http://www.consultant.ru/legalnews/?utm_source=homePage&utm_medium=direct&utm_campaign=centralBlock&utm_content=allNews&page={}')

    def get_article(self, url: str):
        attrs = {'class' : 'news-page__text'}
        return super().get_article(url, 'div', attrs)

    def get_news_urls(self, date_from: str = None, date_to: str = None):
        date_from, date_to = self._set_search_dates(date_from, date_to)
        news_urls = dict()
        next_page = True
        page_number = 1
        page = self._get_html_page(self.search_url.format(page_number))
        while page.status_code == 200 and next_page:
            soup = BeautifulSoup(page.text, "html.parser")
            news = soup.findAll('div', class_="listing-news__item")
            dates = [date.text for item in news for date in item.find_all('div', class_='listing-news__item-date')]
            links = [f'{self.base_url}{link.get("href")}' for item in news for link in item.find_all('a', class_='listing-news__item-title')]
            headers = [link.text for item in news for link in item.find_all('a', class_='listing-news__item-title')]
            for d, url, header in zip(dates, links, headers):
                date = self._format_date(d)
                if self._check_news_date(date, date_from, date_to):
                    self._log_article(date, header)
                    news_urls[url] = (date.strftime('%Y-%m-%d'), header)
                elif date < date_from:
                    next_page = False # если новость вышла раньше, чем указанный диапазон поиска
                    break
            page_number += 1
            page = self._get_html_page(self.search_url.format(page_number))
        return news_urls

    def _format_date(self, date_: str, fmt: str='%d.%m.%Y') -> datetime:
        """Функция приведения даты к унифицированному формату."""    
        current_date = datetime.now()
        if date_ == 'Сегодня':
            return datetime.strptime(f"{current_date.day:02}.{current_date.month:02}.{current_date.year}", fmt)
        else:
            if len(date_.split()) < 3:  # Если не указан год публикации
                date_ += ' ' + str(current_date.year)
            return super()._format_date(date_, fmt)