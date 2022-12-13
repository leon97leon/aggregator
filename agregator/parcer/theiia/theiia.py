from typing import List, Tuple, Dict
from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime
from tqdm import tqdm
import pandas as pd
import re
import fitz
import os
from googletrans import Translator
t = Translator()

import warnings
warnings.filterwarnings('ignore')

PATTERN_DATE = r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)((.?){6})\ ((([0-9])|([0-2][0-9])|([3][0-1])),\ \d{4})|(T\+[0-9]+)$'
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"
TRANS_LIM = 5000    # Bytes limit for text lenght to pass to Google Translator
EXCEL_LIM = 32000   # Bytes limit for text lenght to save in a single cell of Excell

class TheIIA:
    """Сlass for parsing articles from  https://www.theiia.org"""

    def __init__(self, saved_articles_path:str=''):
        self.data_dir = f'{os.path.dirname(__file__)}/data'
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        self.name = 'TheIIA'
        self.base_url = 'https://www.theiia.org'
        self.search_url = 'https://www.theiia.org/en/search/?rpp=100&filters=78743|2345|2344|76607|2348|67448|46552|46554|2347|2359|2355|2356|2358|2360|2361|2362|10826|2371|52839&page={}'
        # 'https://www.theiia.org/en/search/?rpp=100&page={}' # поиск без фильтров
        # self.search_recources_url = 'https://www.theiia.org/en/search/?rpp=100&page={}',
        # self.search_magazine_url = 'https://internalauditor.theiia.org/en/search/?rpp=100&page={}'
        self.recources_url = 'https://www.theiia.org/en/resources/topics'
        self.magazine_url = 'https://internalauditor.theiia.org'
        self.sections = ['audit-practice', 'governance', 'leadership', 'risk', 'technology']
        if not saved_articles_path:
            self.saved_articles_path = os.path.normpath(f'{os.path.dirname(__file__)}/TheIIA.csv')
            print(self.saved_articles_path)
        else:
            self.saved_articles_path = saved_articles_path    
        try:
            self.saved_articles = pd.read_csv(self.saved_articles_path, sep=';', parse_dates=['Date'])
            self.saved_articles.columns = ['Date', 'Header_ru', 'Article_ru', 'Header', 'Article', 'URL']
            self.saved_urls = dict(zip(self.saved_articles['URL'], self.saved_articles['Header']))
        except:
            self.saved_articles = pd.DataFrame(columns=['Date', 'Header_ru', 'Article_ru', 'Header', 'Article', 'URL'])
            self.saved_urls = dict()
        print('Saved urls count:', len(self.saved_urls))
    
    def __repr__(self):
        return f"{self.name} {self.base_url.split('//')[1].replace('www.','')}"
    
        
    def get_article(self, url: str):
        """Function to get the text of the article, the link to the pdf, its date
        
        Returns `tuple(article_text, pdf_url, article_date)`
        """
        soup = BeautifulSoup(self._get_html_page(url).text, "html.parser")
        
        date_elem = soup.find('p', class_='article-details')
        if date_elem:
            date = date_elem.text.strip().split('\n')[-1]
            date = self._format_date(date)
        else:
            try:
                date_elem = soup.find('p', class_='intro')                
                date = re.search(PATTERN_DATE, date_elem.text.strip()).group(0)
                date = self._format_date(date, '%b. %d, %Y')
                if not date:
                    date = self._format_date(date.group(0), '%B %d, %Y')
                if not date:
                    date = self._format_date(date.group(0), '%b %d, %Y')
            except:
                date = None
        
        article_elem = soup.find('article')
        if article_elem:
            [elem.decompose() for elem in article_elem.find_all('ul', {'class':'tags'})]
            article_text = article_elem.text.strip() 
        else:
            article_text = ''
        
        content_elem = soup.find('div', class_='sectionblock')
        if not content_elem:
            content_elem = soup.find('div', class_='contentblock')
        content_text = content_elem.text.strip() if content_elem else ''
        
        pdf_url = soup.find('div', class_='resource-info')
        try:
            pdf_url = pdf_url.find('a', class_='btn-primary')
            pdf_url = pdf_url.get('href')
        except:
            pdf_url = None
                    
        return '\n'.join([article_text, content_text]), pdf_url, date
    
    
    def get_articles_df(self, date_from:str = None, date_to:str = None, 
                        from_=['search','recent'], update_saved=True) -> pd.DataFrame:   
        """Function to get pd.DataFrame with articles from theiia.org
        
        Returns pd.DataFrame with columns
        ```
        | Date | Header_ru | Article_ru | Header | Article | URL |
        ```
        """
        date_from, date_to = self._set_search_dates(date_from, date_to)
        
        urls = self.saved_urls.copy()
        if 'search' in from_:
            urls = self.get_urls_from_search(add_urls_to=urls)
        if 'recent' in from_:
            urls = self.get_recent_urls(add_urls_to=urls)
        new_articles = list()
                
        for url, header in tqdm(urls.items()):
            if not url in self.saved_urls:# or self.saved_articles.loc[self.saved_articles['URL']==url,'PDF URL'].any(): 
                article, pdf_url, date = self.get_article(url)
                if pdf_url:
                    article = article +' \nТЕКСТ PDF\n '+ self._get_pdf_text(pdf_url)
                article = re.sub(r"[\r\n]{2,}", '\r\n', article, flags=re.I or re.M)
                
                header_ru = t.translate(header, dest='ru').text
                article_parts = self.get_article_translation(article.strip())
                for (orig_part, trans_part) in article_parts:
                    new_articles.append([date, header_ru, trans_part, header, orig_part, url])
        print('    new articles: %i' % len(new_articles))
        print('Filtering by date')
        new_articles = pd.DataFrame(new_articles, 
                                    columns=self.saved_articles.columns)

        self.saved_articles = pd.concat(
            [self.saved_articles, new_articles], ignore_index=True
        ).sort_values(by='Date', ascending=False).reset_index(drop=True)
        
        if update_saved:
            self.saved_articles['Date'] = pd.to_datetime(self.saved_articles['Date'])
            self.saved_articles.to_csv(self.saved_articles_path, sep=';', 
                                       date_format='%Y-%m-%d', index=False)
        
        result = self.saved_articles.query("@date_from <= Date <= @date_to").copy() 
        result['Date'] = result['Date'].dt.strftime('%Y-%m-%d')
        return result
    
    
    def get_recent_urls(self, add_urls_to:dict=dict()) -> dict:
        """Function to get the dictionary with links and news headers 
        from every theiia.org section pages.
        
        Returns a dictionary that contains article url as a key and article header as an element:
        ```
        { 'url' : 'header' }
        ```
        """
        articles_count = 0
        article_urls = add_urls_to
        print("Getting URLs for recent articles")
        for s in self.sections:
            page = self._get_html_page(f'{self.recources_url}/{s}')
            soup = BeautifulSoup(page.text, "html.parser")
            article_wraps = soup.findAll('div', class_='article-wrap')
            for awrap in article_wraps:
                link = awrap.find('a').get('href')
                if link[:4] != 'http':
                    link = f"{self.base_url}{link}"
                if not link in article_urls:
                    articles_count += 1 
                    header = awrap.find('div', class_='res-article-sub-title').text.strip()
                    article_urls[link] = header
                    print("    articles found: %i" % articles_count, end='\r')
        # Recent articles from internalauditor.theiia.org              
        for s in self.sections:
            page = self._get_html_page(f'{self.magazine_url}/en/{s}')
            soup = BeautifulSoup(page.text, "html.parser")
            article_wraps = soup.findAll('div', class_='content-list-item')
            for awrap in article_wraps:
                link_elem = awrap.find('a')
                link = link_elem.get('href')
                if link[:4] != 'http':
                    link = f"{self.magazine_url}{link}"
                if not link in article_urls:
                    article_urls[link] = link_elem.text.strip()
                    articles_count += 1
                print("    articles found: %i" % articles_count, end='\r')
        print("    articles found: %i" % articles_count)
        
        return article_urls 
                    

    def get_urls_from_search(self, search_url:str=None, 
                             add_urls_to:dict=dict()) -> dict:
        """Function to get the dictionary with links and news headers 
        from theiia.org search page.
        
        Returns a dictionary that contains article url as a key and article header as an element:
        ```
        { 'url' : 'header' }
        ```
        """
        if not search_url:
            search_url = self.search_url
        article_urls = add_urls_to
        page_number = 1
        articles_count = 0
        print("Getting URLs from search")
        page = self._get_html_page(search_url.format(page_number))
        while page.status_code==200:
        # for page_number in range(1,5):
            soup = BeautifulSoup(page.text, "html.parser")
            article_elems = soup.find_all('article')
            if not article_elems:
                break
            for article_elem in article_elems:
                link_elem = article_elem.find('a', class_='btn-secondary')
                link = link_elem.get('href').split('?')[0]
                if not link in article_urls:
                    article_urls[link] = link_elem.text.strip()
                    articles_count += 1
                print("    page: %i, articles found: %i" % (page_number-1, articles_count), end='\r')      
            page = self._get_html_page(search_url.format(page_number))
            page_number += 1
        print("    pages: %i, articles found: %i" % (page_number-2, articles_count))  
            
        return article_urls
    
    
    def _get_html_page(self, url) -> requests.models.Response:
        """Returns the html code of the page from its url"""
        
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
    
    def _get_pdf_text(self, url) -> str:
        """Returns text of pdf from its url"""
        
        response = requests.get(url, headers={'user_agent': f'{USER_AGENT}'})
        with open(os.path.join(self.data_dir,url.split('/')[-1]), 'wb') as f:
            f.write(response.content)
        with fitz.open(os.path.join(self.data_dir,url.split('/')[-1])) as doc:
            pdf_text = ""
            for page in doc:
                pdf_text += page.get_text()
        pdf_text = re.sub(r'\n\s*\n', '\n\n', pdf_text)
        pdf_text = re.sub(r'\.\.\.\.', '', pdf_text)
        return pdf_text
    
    def _set_search_dates(self, date_from:str=None, date_to:str=None, fmt:str='%d.%m.%Y'):
        """Function for setting the time interval for searching articles."""
        if date_from is None:
            date_from = self._get_current_date()
        else:
            date_from = datetime.strptime(date_from, fmt)
        if date_to is None:
            date_to = self._get_current_date()
        else:
            date_to = datetime.strptime(date_to, fmt)
        
        return date_from, date_to
    
    def _get_current_date(self) -> datetime     :
        """Function to get the current date for the search"""
        current_date = datetime.now()
        return datetime.strptime(f"{current_date.day:02}.{current_date.month:02}.{current_date.year}", '%d.%m.%Y')
    
    def _format_date(self, date_: str, fmt: str='%b %d, %Y') -> datetime:
        """Function for converting the date to a unified format"""
        try:
            fmt_date = datetime.strptime(date_.strip(), fmt)
        except:
            fmt_date = None
        return fmt_date
    
    @staticmethod
    def get_article_translation(txt:str, excel_lim:int=EXCEL_LIM, trans_lim:int=TRANS_LIM):
        '''Function to get the translation of an text `txt` divided into parts not exceeding EXCEL_LIM characters'''
        
        if txt == '':
            return [('','')]
        text = txt + '\r\n'
        parts = list()
        original = ''
        translated = ''
        right = 0
        while right < len(text):
            left = right
            
            end_pos = -1
            for splitter in ['\r\n', '. ', ' ']:
                end_pos = text[right:right+trans_lim].rfind(splitter)
                if end_pos != -1:
                    end_pos += len(splitter)
                    break
            if end_pos == -1:
                end_pos = trans_lim - 1
            
            right += end_pos
            orig_chunk = text[left:right]
            try:
                tran_chunk = t.translate(orig_chunk, dest='ru').text
                
                if (len(original) + len(orig_chunk) > excel_lim or 
                    len(translated) + len(tran_chunk) > excel_lim ):
                    parts.append((original, translated))
                    original = orig_chunk
                    translated = tran_chunk
                else:
                    original += orig_chunk
                    translated += tran_chunk
            except:
                tran_chunk = ''
        parts.append((original, translated))
        return(parts)