import requests
import time
import zipfile
import shutil
from celery import Celery
import os
import datetime
from .parcer import ML, parserutils
from .parcer.newspars import Audit_it, CBR, Gaap, IIA, Minfin, RBK, SRO, Consultant
from .parcer.globalpars import mainparser
from .parcer.theiia import TheIIA
import pandas as pd
from celery.exceptions import SoftTimeLimitExceeded,TimeLimitExceeded
from django.core.files import File
from lxml import etree
from django.contrib.auth.models import User
from datetime import datetime
from django.db.models import Max
from .models import BaseWord,BaseParsingResult
from my_site.celery import app

from django.core.cache import cache


DICT_SITE_PARSER = {'consultant.ru' :   Consultant(), 
                    'gaap.ru' :         Gaap(), 
                    'rbc.ru' :          RBK(), 
                    'minfin.gov.ru' :   Minfin(), 
                    'sroaas.ru' :       SRO(), 
                    'iia-ru.ru' :       IIA(), 
                    'cbr.ru' :          CBR(), 
                    'audit-it.ru' :     Audit_it()}
def unpack_zipfile(filename, extract_dir, encoding='cp437'):
    with zipfile.ZipFile(filename) as archive:
        for entry in archive.infolist():
            name = entry.filename  # reencode!!!

            # don't extract absolute paths or ones with .. in them
            if name.startswith('/') or '..' in name:
                continue

            target = os.path.join(extract_dir, *name.split('/'))
            os.makedirs(os.path.dirname(target), exist_ok=True)
            if not entry.is_dir():  # file
                with archive.open(entry) as source, open(target, 'wb') as dest:
                    shutil.copyfileobj(source, dest)

def parse_data(celery_task_id: str,file_word,type_word,user,date_from,date_to,site_pars):
    new_word = BaseWord.objects.create(
        name=celery_task_id,
        user=user,
        type=type_word

    )
    new_word.save()
    if len(file_word)==1:
        new_word.file = file_word[0]
    elif len(file_word)==2:
        new_word.file_state = file_word[0]
        new_word.file_acrhiv = file_word[1]
    uid = BaseWord.objects.filter(user=user).order_by('-uid').first().uid
    print(uid)
    if uid == None:
        new_word.uid = 0
        test_uid = 0
    else:
        test_uid = int(uid)+1
        new_word.uid = test_uid
    # uid = max(BaseWord.objects.get(user=user)['uid'])
    # print(uid)
    # new_word.uid = uid
    new_word.save()
    cur_parsing_res = BaseParsingResult.objects.create(
        task_id=new_word,
        sites=r'<br>'.join(site_pars),
        user=user,
        uid=test_uid,
        date_ot=date_from,
        date_do=date_to,
        result_text='Loading'
    )
    cur_parsing_res.save()
    if type_word == 'Ручные':
        df = pd.read_excel('media/'+file_word[0], header=None)
        print(df)
        words = df[df.columns[-1]].unique().tolist()
        cur_parsing_res.file_word = file_word[0]
    elif type_word == 'Модель' and len(file_word)==2:
        try:
            path_archive = 'media/'+os.path.splitext(file_word[1])[0]+'/'
            unpack_zipfile('media/' + file_word[1],path_archive)
            model = ML.ML()
            word_model = model.run('media/' + file_word[0],path_archive)
            shutil.rmtree(path_archive)
            path_archive='media/'+'user_{0}/word_model_{1}.xlsx'.format(user, datetime.now().strftime('%m_%d_%Y_%H_%M_%S'))
            #words = list(set(', '.join(word_model['keywords'].tolist()).split(', ')))
            #word_model = pd.DataFrame(words)
            word_model=word_model.drop_duplicates()
            word_model.to_excel(path_archive,index=False)
            cur_parsing_res.file_word = path_archive.replace('media/','')
        except Exception as e:
            cur_parsing_res.result_text = "Ошибка в файлах модели"
            cur_parsing_res.save()
    elif type_word == 'Модель' and len(file_word) == 1:
        word_model = pd.read_excel('media/'+file_word[0])
        cur_parsing_res.file_word = file_word[0]
    cur_parsing_res.save()
    #for site in site_pars:
    print(site_pars)
    try:
        path = 'user_{0}/result_{1}.xlsx'.format(user, datetime.now().strftime('%m_%d_%Y_%H_%M_%S'))
        writer = pd.ExcelWriter('media/'+path, engine='xlsxwriter')
        if 'Глобальный поиск' in site_pars:
            pars_global=mainparser.MainParser()
            if type_word == 'Ручные':
                news_global, news_end = pars_global.main(datetime.strptime(date_from, '%Y-%m-%d'),datetime.strptime(date_to, '%Y-%m-%d'),pd.DataFrame(words))
            elif type_word == 'Модель':
                news_global, news_end = pars_global.main(datetime.strptime(date_from, '%Y-%m-%d'),
                                                         datetime.strptime(date_to, '%Y-%m-%d'), word_model)
            news_global.to_excel(writer, sheet_name='Глобальный поиск')
            news_end.to_excel(writer, sheet_name='Не выгрузилось')
            writer.sheets['Не выгрузилось'].set_tab_color('orange')
        # print(site_pars)
        site_8 = [DICT_SITE_PARSER[x] for x in site_pars if x in DICT_SITE_PARSER.keys()]
        if site_8 != []:
        #path = 'user_{0}/result_{1}.xlsx'.format(user, datetime.now().strftime('%m_%d_%Y_%H_%M_%S'))
        # writer = pd.ExcelWriter('media/'+path, engine='xlsxwriter')
            date_from = datetime.strptime(date_from, '%Y-%m-%d').strftime('%d.%m.%Y')
            date_to = datetime.strptime(date_to, '%Y-%m-%d').strftime('%d.%m.%Y')
            news = parserutils.get_news(site_8, date_from,date_to)
            pd.DataFrame(news).to_excel(user+''.join([str(x) for x in site_8])+str(date_from)+'.xlsx')
            print(type_word)
            if type_word == 'Ручные':
                news = parserutils.check_keywords(news,words)
            elif type_word == 'Модель':
                news = parserutils.check_keywords_model(news, word_model['keywords'].to_dict())
            news = parserutils.filter_headers(news)
            news = parserutils.drop_duplicates(news)
            news.columns=['Сайт','Дата новости','Заголовок статьи','Текст статьи','Ссылка на статью','Ключевое слово']
            news.to_excel(writer, sheet_name='8 Парсеров',index=False)
        # #
        # TODO добавить theiia.org
        if 'theiia.org' in site_pars:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').strftime('%d.%m.%Y')
            date_to = datetime.strptime(date_to, '%Y-%m-%d').strftime('%d.%m.%Y')
            articles = TheIIA().get_articles_df(date_from=date_from, date_to=date_to)
            if type_word == 'Ручные':
                articles = parserutils.check_keywords(articles, news_column='Article_ru')
            elif type_word == 'Модель':
                articles = parserutils.check_keywords_model(articles, word_model['keywords'].to_dict(), news_column='Article_ru')
            articles.columns=['Дата','Заголовок статьи','Ссылка на статью','Ссылка на PDF', 'Текст статьи', 'Перевод статьи', 'Ключевое слово']
            articles.to_excel(writer, sheet_name='TheIIA',index=False)

        cur_parsing_res.result = path
        cur_parsing_res.result_text = 'Success'
        cur_parsing_res.save()
        writer.save()
    except SoftTimeLimitExceeded:
        cur_parsing_res.result_text = "Ошибка. Слишком долго. Попробуйте изменить запрос либо запустите позже"
        cur_parsing_res.save()
    except TimeLimitExceeded:
        cur_parsing_res.result_text = "Ошибка. Слишком долго. Попробуйте изменить запрос либо запустите позже"
        cur_parsing_res.save()
    except Exception as e:
        cur_parsing_res.result_text = e
        cur_parsing_res.save()

    return True


@app.task(name='create_task', bind=True,time_limit=60*60)
def create_task(self,file,type_word,user,date_from,date_to,site_pars):
    parse_data(self.request.id,file,type_word,user,date_from,date_to,site_pars)
    return True
