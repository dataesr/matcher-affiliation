import json
import os
import pycountry

from elasticsearch import Elasticsearch
from matcher.server.main.config import config

ES_INDEX = 'country'
FILE_COUNTRY_KEYWORDS = 'country_keywords.json'
FILE_COUNTRY_FORBIDDEN = 'country_forbidden.json'
FILE_FRENCH_CITIES = 'insee_2020_cities.json'


def get_info_from_country(alpha_2: str = None) -> dict:
    country = pycountry.countries.get(alpha_2=alpha_2)
    info = [country.name]
    language = pycountry.languages.get(alpha_2=alpha_2)
    if language is not None:
        info.append(language.name)
    return {'alpha_2': country.alpha_2, 'alpha_3': country.alpha_3,
            'info': info}


def get_cities_from_country(alpha_2: str = None) -> dict:
    if alpha_2 == 'fr':
        dirname = os.path.dirname(__file__)
        with open(os.path.join(dirname, FILE_FRENCH_CITIES), 'r') as file:
            cities = json.load(file)['cities']
            cities = [city.lower() for city in cities]
    else:
        cities = []
    return {'cities': cities}


def get_stop_words_from_country(alpha_2: str = None) -> dict:
    alpha_2 = alpha_2.upper()
    dirname = os.path.dirname(__file__)
    with open(os.path.join(dirname, FILE_COUNTRY_FORBIDDEN), 'r') as file:
        country_keywords = json.load(file)
        if alpha_2 in country_keywords.keys():
            stop_words = country_keywords[alpha_2]
        else:
            stop_words = []
    return {'stop_words': stop_words}


# TODO: Add logger
def init_country() -> None:
    es = Elasticsearch(config['ELASTICSEARCH_HOST'])
    es.indices.create(index=ES_INDEX, ignore=400)
    es.delete_by_query(index=ES_INDEX, body={'query': {'match_all': {}}}, refresh=True)
    # TODO: use helpers.parallel_bulk
    for country in pycountry.countries:
        country = country.alpha_2.lower()
        body = {}
        info = get_info_from_country(country)
        body.update(info)
        cities = get_cities_from_country(country)
        body.update(cities)
        stop_words = get_stop_words_from_country(country)
        body.update(stop_words)
        es.index(index=ES_INDEX, id=country, body=body, refresh=True)


if __name__ == '__main__':
    init_country()