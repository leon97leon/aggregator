from tqdm import tqdm
from typing import List, Tuple, Dict
import pandas as pd
import re
import time
import pymorphy2
import json

morph = pymorphy2.MorphAnalyzer()
# Регулярные выражения
pattern_word = re.compile("[^а-яА-Яеё-]", re.MULTILINE | re.DOTALL | re.IGNORECASE) # слова
pattern_double = re.compile('[ \n]+', re.MULTILINE | re.DOTALL) # числа
pattern_code = re.compile("\$\(function.*;", re.MULTILINE | re.DOTALL)  # код JavaScript
pattern_anekdot = re.compile("© anekdotov.net", re.MULTILINE | re.DOTALL)  # строки "© anekdotov.net"

def get_news(sites: List[object], date_from: str = None, date_to: str = None) -> pd.DataFrame:
    """Функция получения списка новостей за указанную дату.
    ----
    sites : `List[parsers.WebResource()]` список экземпляров классов сайтов для парсинга (например: [Gaap(), Audit_it()])

    Возвращает pd.DataFrame со столбцами:  
    ```
    | название_сайта | ссылка_на_новость | текст_новости | заголовок_новости |
    ```
    """
    news = list()
    for site in sites:
        print(f'\nParse: {site}')
        urls = site.get_news_urls(date_from, date_to)
        for url, (date, title) in tqdm(urls.items()):
            article = site.get_article(url)
            if 'anekdotov' in article:
                article = pattern_anekdot.sub('', article)
            if 'function' in article:
                article = pattern_code.sub('', article)
            if article:
                article = re.sub(r"[\r\n]{2,}", '\r\n', article, flags=re.I or re.M)
            news.append([site.name, date, title, article.strip(), url])
            time.sleep(1)
    return pd.DataFrame(news, columns=['Source', 'Date', 'Header', 'Article', 'URL'])


def check_keywords(news: pd.DataFrame, words: List[str] = None, 
                   news_column: str = 'Article') -> pd.DataFrame:
    """Функция фильтрации новостей по ключевым словам аналитиков.
    ----
    news: pd.DataFrame c новостями

    Возвращает отфильтрованный pd.DataFrame c дополнительным столбцом: `'Check_word'`
    """
    if words is None:
        with open(r"words.txt", encoding='utf-8') as f:
            words = f.read().split(';')
    one_words = [word for word in words if len(word.split()) == 1]
    two_plus_words = [word for word in words if len(word.split()) != 1]
    lemm_one_words = [lemmatize(i) for i in one_words]
    lemm_two_plus_words = [lemmatize(i) for i in two_plus_words]
    print('Processing keywords')
    def check_article(x):
        try:
            lemm_news = lemmatize(x[news_column] + x['Header'])
            lemm_sep_news = lemmatize_sep(x[news_column] + x['Header'])
            if any(word in lemm_sep_news for word in lemm_one_words):
                return next(word for word in lemm_one_words if word in lemm_sep_news)
            elif any(word in lemm_news for word in lemm_two_plus_words):
                return next(word for word in lemm_two_plus_words if word in lemm_news)
        except:
            return None
    tqdm.pandas()    
    check_words = news[[news_column,'Header']].progress_apply(check_article,axis=1)
    filtered_urls = news[check_words.notna()]['URL']
    filtered_news = news[news['URL'].isin(filtered_urls)]
    filtered_news['Check_word'] = check_words[check_words.notna()]
    return filtered_news


def check_keywords_model(news: List[List[str]], words = None,
                         news_column: str = 'Article') -> pd.DataFrame:
    """Функция фильтрации новостей по ключевым словам модели.

    news: исходный список новостей
    path: путь к файлу со словами модели

    Возвращает отфильтрованный pd.DataFrame c дополнительным столбцом: `'Check_word'`
    """
    if words is None:
        with open(r"words.txt", encoding='utf-8') as f:
            words = f.read().split(';')
    
    print('Processing keywords')
    def check_article(x):
        try:
            lemm_sep_news = lemmatize_sep(x[news_column] + x['Header'])
            for theme in words.items():
                lemm_words = [lemmatize(i) for i in theme[1]]
                if all([word in lemm_sep_news for word in lemm_words]):
                    return theme[0]
        except AttributeError:
            print(x)
            return None
    tqdm.pandas()    
    check_words = news[[news_column,'Header']].progress_apply(check_article,axis=1)
    filtered_urls = news[check_words.notna()]['URL']
    filtered_news = news[news['URL'].isin(filtered_urls)]
    filtered_news['Check_word'] = check_words[check_words.notna()]
    return filtered_news


def filter_headers(news: pd.DataFrame) -> pd.DataFrame:
    """Функция фильтрации новостей по заголовкам из черного списка.

    news: исходный список новостей

    Возвращает отфильтрованный pd.DataFrame:
    """
    try:
        with open('filter_headers.txt', 'r', encoding='utf8') as fh:
            filter_headers = list(map(str.strip, fh.readlines()))
    except:
        # TODO пока не разбирался, что это за костыль
        filter_headers = '''состоялась встреча регцентра,мастер-класс ИВА для студентов,состоялся круглый стол, представители ассоциации «ИВА» вошли в состав,«Внутренний аудит по Сойеру: сохранение и повышение стоимости организации»,IIA и ACCA укрепляют сотрудничество,IIA обновил программу CRMA,IIA приглашает выступить,IIA приглашает выступить на Международной конференции,Важные изменения для членов ИВА,Внутренний аудит по Сойеру,Выступление представителей ИВА,Директор ИВА выступил,Для обладателей профессиональных сертификатов IIA,Запуск новой системы CCMS,Запуск новой системы CCMS и обновленный Справочник кандидата,Изменение логотипа ИВА,Институт внутренних аудиторов включен в состав,Институт внутренних аудиторов включен в состав технического комитета по стандартизации,Компания стала партнером ИВА,На сайте Института внутренних аудиторов появился новый раздел,Награждение по итогам,начинается бета-тестирование обновленной программы CRMA,Новое Положение о Премии «Внутренний аудитор года»,Новые книги в библиотеке Института внутренних аудиторов,Новые книги издательств в библиотеке Института внутренних аудиторов,О Региональном центре Института внутренних аудиторов,Обновление подраздела на сайте ИВА,Обязательное обучение  для обладателей профессиональных сертификатов IIA,Обязательное обучение по,Опубликован обновленный Справочник кандидата,Открытые вакансии в Совете IIA,Отмена регистрационного взноса,Отмена регистрационного взноса на получение CRMA,Очередное Общее собрание членов Ассоциации «ИВА»,Пополнение в библиотеке Института внутренних аудиторов,Представитель ИВА принял участие в заседании,Премия «Внутренний аудитор года»,Развитие вместе с ИВА,Состоится бесплатный вебинар,состоялась встреча регионального центра Института внутренних аудиторов,состоялась онлайн-встреча,состоялась онлайн-встреча Клуба страховых аудиторов при Институте внутренних аудиторов,Состоялась Региональная конференция Института внутренних аудиторов,состоялось Общее собрание членов Ассоциации «Институт внутренних аудиторов»,Состоялся бизнес-завтрак Института внутренних аудиторов,состоялся вебинар,состоялся вебинар «Диалоги о внутреннем аудите»,Состоялся открытый совместный онлайн круглый стол ИВА,Старт глобального исследования IIA,Старт глобального исследования IIA по оценке практики внутреннего аудита,Сформирован Экспертный совет Национальной Премии «Внутренний аудитор года»,Член ИВА вошел в состав комитета IIA,члены ACCA смогут получить диплом CIA,члены ACCA смогут получить диплом CIA в упрощенном порядке,Экзамен на получение сертификации IAP,состоялась встреча регионального центра,Национальной премии «Внутренний аудитор года»,Лекция ИВА,состоялась онлайн-встреча регионального центра,Временная приостановка экзаменов на получение сертификаций,Национальная конференция Института внутренних аудиторов'''
        filter_headers = filter_headers.split(',')
    a = set()
    for header in filter_headers:
        for row_number in news[news['Source'] == 'IIA'].index:
            if header.lower().strip() in news.loc[row_number, 'Header'].lower():
                a.add(row_number)
    a = list(a)
    filtered_news = news.drop(a).reset_index().drop(columns=['index'])
    return filtered_news


def drop_duplicates(news: pd.DataFrame) -> pd.DataFrame:
    """Функция удаления дубликатов новостей."""
    news.drop_duplicates(subset=['Header'], inplace=True)
    return news


def lemmatize_sep(text: str) -> List[str]:
    """Функция лемматизации.

    Возвращает список лемматизированных слов.
    """
    lemmatized = []
    text = re.sub(pattern_double, ' ', re.sub(pattern_word, ' ', text))
    for word in text.split():
        p = morph.parse(word)[0]
        lemmatized.append(p.normal_form)
    return lemmatized


def lemmatize(text: str) -> str:
    """Функция лемматизации.

    Возвращает лемматизированный текст с разделитем - пробелом.
    """
    return ' '.join(lemmatize_sep(text))