import argparse
from newspars import Gaap, Audit_it, Minfin, RBK, SRO, IIA, Consultant, CBR
from theiia import TheIIA
import parserutils as p
import warnings
import pandas as pd
warnings.filterwarnings('ignore')
date_from = '17.11.2022'
date_to = '27.11.2022'

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--date_from', type=str)
    parser.add_argument('-t', '--date_to', type=str)
    parser.add_argument('-r', '--resource', type=str, default='news', choices=['news', 'theiia'])
    parser.add_argument('-k', '--keywords_type', type=str, default='a', choices=['a','m']) # 'a' - слова аналитиков, 'm' - слова модели
    parser.add_argument('-p', '--keywords_filepath', type=str, default='LDA.txt')   # Путь к файлу со словами модели
    args = parser.parse_args()
    
    if args.resource == 'news':
        if date_from is not None and date_to is not None:
            # news = p.get_news([Gaap(), Audit_it(), Minfin(), RBK(), SRO(), IIA(), Consultant(), CBR()], args.date_from, args.date_to)
            news = p.get_news([SRO()], date_from, date_to)
        else:
            news = p.get_news([Gaap(), Audit_it(), Minfin(), RBK(), SRO(), IIA(), Consultant(), CBR()])
        news.to_csv('log_links.csv', sep=';', encoding='utf-8', index=False)
        news = p.filter_headers(news)
        news = p.drop_duplicates(news)
        if args.keywords_type == 'a':
            news = p.check_keywords(news, news_column='Article')
        else:
            news = p.check_keywords_model(news, args.keywords_filepath, news_column='Article')
        news.to_csv('news_result.csv', sep=';', index=False, encoding='utf-8')
    
    elif args.resource == 'theiia':
        articles = TheIIA().get_articles_df(date_from=args.date_from, date_to=args.date_to)
        if args.keywords_type == 'a':
            articles = p.check_keywords(articles, news_column='Article_ru')
        else:
            articles = p.check_keywords_model(articles, args.keywords_filepath, news_column='Article_ru')
        articles.to_csv('theiia_result.csv', sep=';', index=False, encoding='utf-8')