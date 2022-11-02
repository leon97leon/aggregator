from .Parser import Parser
from bs4 import BeautifulSoup
from bs4.element import Tag, NavigableString
import requests
from requests_html import HTMLSession

import urllib.parse
from datetime import datetime, timedelta, date
from dataclasses import dataclass
from tqdm import tqdm
from typing import List, Tuple, Dict
import re
import time
import pymorphy2


class SRO(Parser):
    """Класс для работы с сайтом https://sroaas.ru."""

    def __init__(self):
        self.url = 'https://sroaas.ru/pc/novosti/'
        self.page_number = 2    # Номер страницы, которая будет возвращена функцией _next_page
        self.session = HTMLSession()

    def __repr__(self):
        return 'SRO'

    def _get_article(self, url: str) -> str:
        """Функция получения текста новости."""
        article = []
        for _ in range(1, 19):
            try:
                page = requests.get(url, verify=False)
                soup = BeautifulSoup(page.text, "html.parser")
                article = soup.findAll('div', class_='b-news-detail ph-block')
                if page.status_code != 200:
                    time.sleep(_)
                else:
                    break
            except requests.exceptions.RequestException as e:
                print(e)
        if article:
            return article[0].text
        else:
            return 'Can not parse'

    def _get_news_urls(self, date_from: str = None, date_to: str = None) -> List[str]:
        """Функция получения списка ссылок на новости.
        
        Возвращает список, который содержит пары - ссылка на новость и заголовок новости:
        [
            [ссылка, заголовок], 
            ... 
            [ссылка, заголовок]
        ]
        """
        if date_from is None:
            date_from = self._get_current_date()
        else:
            date_from = datetime.strptime(date_from, '%Y-%m-%d')
        if date_to is None:
            date_to = self._get_current_date()
        else:
            date_to = datetime.strptime(date_to, '%Y-%m-%d')
        urls = list()
        next_page = True
        for _ in range(1, 19):
            try:
                page = requests.get(self.url, verify=False)
                if page.status_code != 200:
                    time.sleep(_)
                else:
                    break
            except requests.exceptions.RequestException as e:
                page = requests.models.Response()
        if page.status_code == 200:
            soup = BeautifulSoup(page.text, "html.parser")
            news = soup.findAll('div', class_="b-news__item")
            while next_page:
                links = [f'{self.url[:17]}{item.a.get("href")}' for item in news]
                dates = [item.div.text.strip() for item in news]
                dates = [' '.join(d.split()[-4:]) for d in dates]
                headers = [item.p.text.strip() for item in news]
                for triple in zip(dates, links, headers):
                    if self._check_news_date(self._format_date(triple[0]), date_from, date_to):
                        print(self._format_date(triple[0]), triple[2])
                        urls.append([triple[1], triple[2]])
                    else:
                        # Проверка на случай, если новость вышла раньше, чем указанный диапазон поиска
                        if self._format_date(triple[0]) < date_from:
                            next_page = False
                            break
                if next_page:
                    page = self._next_page()
                    if page.status_code == 200:
                        soup = BeautifulSoup(page.text, "html.parser")
                        news = soup.findAll('div', class_="b-news__item")
                    else:
                        next_page = False
        else:
            print(self, page.status_code)
        return urls

    def _next_page(self) -> requests.models.Response:
        """Функция получения html кода следующей страницы с опубликованными новостями."""
        for _ in range(1, 19):
            try:
                page = requests.get(f"{self.url}&PAGEN_1={self.page_number}", verify=False)
                if page.status_code != 200:
                    time.sleep(_)
                else:
                    break
            except requests.exceptions.RequestException as e:
                page = requests.models.Response()
        self.page_number += 1
        return page

    def _format_date(self, date: str) -> datetime:
        """Функция приведения даты к унифицированному формату."""
        month_dict = {
            ' января ': '.01.',
            ' февраля ': '.02.',
            ' марта ': '.03.',
            ' апреля ': '.04.',
            ' мая ': '.05.',
            ' июня ': '.06.',
            ' июля ': '.07.',
            ' августа ': '.08.',
            ' сентября ': '.09.',
            ' октября ': '.10.',
            ' ноября ': '.11.',
            ' декабря ': '.12.'
        }
        for key in month_dict.keys():
            date = date.replace(key, month_dict[key])
        return datetime.strptime(date, '%d.%m.%Y %H:%M')