import argparse
import datetime
import csv
import logging
logging.basicConfig(level=logging.INFO)
import re #Módulo de expresiones regulares

from requests.exceptions import HTTPError
from urllib3.exceptions import MaxRetryError #Errores de extracción de ArticlePage

import news_page_objects as news
from common import config #Importando funcion config del módulo common.py

logger = logging.getLogger(__name__) #Se pasa el nombre del archivo con la variable global __name__
is_well_formed_link = re.compile(r'^https?://.+/.+$') #Regex que verifica un buen link formado
is_root_path = re.compile(r'^/.+$') #Regex que verifica si al link le falta el host


def _news_scraper(news_site_uid):
    host = config()['news_sites'][news_site_uid]['url']

    logging.info(f'Beginning scraper for {host}')
    homepage = news.HomePage(news_site_uid, host)

    articles = []
    for link in homepage.article_links:
        article = _fetch_article(news_site_uid, host, link)

        if article: 
            logger.info('Article fetched!')
            articles.append(article)
            print(article.title)
            # break

    _save_articles(news_site_uid, articles)


def _save_articles(news_site_uid, articles):
    now = datetime.datetime.now().strftime('%Y_%m_%d')
    our_file_name = f'{news_site_uid}_{now}_articles.csv'
    csv_headers = list(filter(lambda property: not property.startswith('_'), dir(articles[0])))

    with open(our_file_name, mode ='w+') as f:
        writer = csv.writer(f)
        writer.writerow(csv_headers)

        for article in articles:
            row = [str(getattr(article, prop)) for prop in csv_headers]
            writer.writerow(row)


def _fetch_article(news_site_uid, host, link):
    logger.info(f'Start fetching article at {link}')

    article = None
    try:
        article = news.ArticlePage(news_site_uid, _build_link(host, link))
    except (HTTPError, MaxRetryError) as e:
        logger.warning('Error while fetching the article', exc_info=False)
        
    if article and not article.body:
        logger.warning('Invalid article. There is no body')
        return None

    return article


def _build_link(host, link):
    if is_well_formed_link.match(link):
        return link
    elif is_root_path.match(link):
        return f'{host}{link}'
    else:
        return f'{host}/{link}'


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    news_site_choices = list(config()['news_sites'].keys())
    parser.add_argument('news_site', 
                        help='The news site that you want to scrape',
                        type=str,
                        choices=news_site_choices)

    args = parser.parse_args()
    _news_scraper(args.news_site)

