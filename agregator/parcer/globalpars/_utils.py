import os
import re
import sys
from datetime import datetime as dt
from pathlib import Path
import glob
import pandas as pd
import pymorphy2
import requests

from ._config import stopwords_path


class Utils:
    __stopwords = None
    __morph = None

    @staticmethod
    def search_files(path: str):
        """Return filenames found in 'path' directory.

        :param path: directory to search for files
        :type path: str

        :rtype: set[str]
        :return: set of discovered 'filename.extension' strings
        """
        try:
            print(os.path.abspath(os.curdir))
            files = glob.glob(path+'*.csv')
            print(files)
            try:
                files.remove('.DS_Store')
            except (KeyError,ValueError):
                pass
            return files
        except Exception as err:
            print('Ошибка при поиске файлов:\n'
                  f'{err}')

    @staticmethod
    def __read_files(path: str):
        """Return lowercase stripped rows
        contained in .csv files from 'path'.

        :param path: directory to pass to Utils.search_files()
        :type path: str

        :rtype: set[str]
        :return: set of rows
        """
        files = Utils.search_files(path)
        if not files:
            print(f'Папка, "{path}", пуста!')
            return set()
        rows = set()
        for filename in files:
            file = Path(filename)
            if not filename.endswith('.csv'):
                print(f'Файл "{file}" не подходит.\n'
                      'Необходимо использовать файлы формата .csv')
            elif file.stat().st_size == 0:
                print(f'Файл "{filename}" пуст!')
            else:
                file_rows = set()
                with open(file, encoding='utf-8-sig') as csv:
                    for row in csv:
                        file_rows.add(row.strip().lower())
                csv.close()
                rows = rows.union(file_rows)
        return rows

    @staticmethod
    def read_keys(keys_df: pd.DataFrame):
        """Return keywords
        contained in .csv files from keys_path dir:
        keys-word forms generated from a single word;
        keys-phrases.

        :rtype: set[str]
        :return: set of keywords
        """
        keys = set(keys_df[keys_df.columns[0]])

        if not keys:
            print('Ключевых слов не обнаружено.')
            sys.exit()
        else:
            new_keys = set()
            for key in keys:
                new_keys = new_keys.union(Utils.__word_forms(key))
            print(new_keys)
            print(f'Обнаружено ключевых слов: {len(new_keys)}')
            return new_keys

    @staticmethod
    def __read_stopwords():
        """Return stopwords contained in
         .csv files from stopwords_path dir.

        :rtype: set[str]
        :return: set of stopwords
        """
        path = stopwords_path
        rows = Utils.__read_files(path)
        stopwords = set()
        for row in rows:
            stopword = ''.join(re.findall(r'[\w+ ]', row))
            stopword = re.sub(r' +', ' ', stopword)
            if stopword:
                stopwords.add(stopword)

        if not stopwords:
            print('Стоп-слов не обнаружено! '
                  'Необходимо использовать файлы формата '
                  '.csv со словами в первой колонке.\n'
                  'Похожие заголовки будут определяться менее точно.')
        return stopwords

    @staticmethod
    def create_session():
        """Return requests.Session() object and check connection.

        :rtype: requests.sessions.Session
        :return: Session object
        """
        s = requests.Session()
        Utils.check_connection(s)
        return s

    @staticmethod
    def check_connection(session: requests.sessions.Session):
        """Check internet connection.

        :param session: session object to be checked
        :type session: requests.sessions.Session
        """
        try:
            session.get('https://yandex.ru/', timeout=15)

        except IOError:
            try:
                session.get('https://www.google.com/', timeout=15)
            except IOError:
                print(f'Проблемы с интернет подключением!')
                sys.exit()

        except Exception as err:
            print(f'Ошибка:\n'
                  f'{err}')
            sys.exit()

    @classmethod
    def normal_str(cls, not_normal: str):
        """Return normalised string.

        :param not_normal: not normalised string
        :type not_normal: str

        :rtype: str
        :return: normalised string
        """
        if not cls.__stopwords:
            cls.__stopwords = Utils.__read_stopwords()
        normal = []
        not_normal = re.sub(r'[^\w\s]', ' ', not_normal)
        not_normal = re.sub(r' +', ' ', not_normal).strip()
        for word in not_normal.split():
            if word not in cls.__stopwords:
                normal_word = cls.__morph.parse(word)[0].normal_form
                normal.append(normal_word)
        normal = ' '.join(normal)
        return normal

    @classmethod
    def __word_forms(cls, word: str):
        """Return word forms for single-word keywords and phrases.

        :param word: set of words to create word forms
        :type word: str

        :rtype: set[str]
        :return: phrases or word forms generated from a single words
        """
        if not cls.__morph:
            cls.__morph = pymorphy2.MorphAnalyzer()
        new_words = set()
        clean_word = ''.join(re.findall(r'[\w+ ]', word))
        if len(clean_word.split()) > 1:
            new_words.add(clean_word)
        elif clean_word:
            forms = cls.__morph.parse(clean_word)[0].lexeme
            for form in forms:
                new_words.add('"' + form[0] + '"')

        return new_words

    @staticmethod
    def get_list_of_dates(
            first_date: dt,
            second_date: dt
    ):

        dates_list = []

        if first_date == second_date:
            dates_list.append(first_date)
            return dates_list

        if first_date > second_date:
            first_date, second_date = second_date, first_date

        dates_list = pd.date_range(first_date, second_date).to_list()

        return dates_list
