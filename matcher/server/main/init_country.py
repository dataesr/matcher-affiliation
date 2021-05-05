import json
import os
import pycountry
import requests

from matcher.server.main.logger import get_logger
from matcher.server.main.my_elastic import MyElastic

ES_INDEX = 'country'
FILE_COUNTRY_FORBIDDEN = 'country_forbidden.json'
FILE_COUNTRY_WHITE_LIST = 'country_white_list.json'
QUERY_CITY_POPULATION_LIMIT = 50000
WIKIDATA_SPARQL_URL = 'https://query.wikidata.org/bigdata/namespace/wdq/sparql'

logger = get_logger(__name__)


def get_all_cities() -> dict:
    query = '''
    SELECT DISTINCT ?country_alpha2 ?label_native ?label_official ?label_en ?label_fr ?label_es ?label_it WHERE { 
        ?city wdt:P31/wdt:P279* wd:Q515 ;
            wdt:P1082 ?population ;
            wdt:P17 ?country .
        ?country wdt:P297 ?country_alpha2 .
        OPTIONAL { ?city wdt:P1705 ?label_native . }
        OPTIONAL { ?city wdt:P1448 ?label_official . }
        OPTIONAL { ?city rdfs:label ?label_en FILTER(lang(?label_en) = "en") . }
        OPTIONAL { ?city rdfs:label ?label_fr FILTER(lang(?label_fr) = "fr") . }
        OPTIONAL { ?city rdfs:label ?label_es FILTER(lang(?label_es) = "es") . }
        OPTIONAL { ?city rdfs:label ?label_it FILTER(lang(?label_it) = "it") . }
        FILTER(?population > ''' + str(QUERY_CITY_POPULATION_LIMIT) + ''') .
    }
    '''
    response = requests.get(WIKIDATA_SPARQL_URL, params={'query': query, 'format': 'json'})
    results = {}
    if response.status_code == requests.codes.ok:
        for city in response.json()['results']['bindings']:
            alpha_2 = city['country_alpha2']['value'].lower()
            if alpha_2 not in results.keys():
                results[alpha_2] = {}
                results[alpha_2]['all'] = []
                results[alpha_2]['strict'] = []
                results[alpha_2]['en'] = []
                results[alpha_2]['fr'] = []
                results[alpha_2]['es'] = []
                results[alpha_2]['it'] = []
            if 'label_official' in city.keys():
                results[alpha_2]['strict'].append(city['label_official']['value'])
            elif 'label_en' in city.keys():
                results[alpha_2]['strict'].append(city['label_en']['value'])
            if 'label_native' in city.keys():
                results[alpha_2]['all'].append(city['label_native']['value'])
            if 'label_official' in city.keys():
                results[alpha_2]['all'].append(city['label_official']['value'])
            if 'label_en' in city.keys():
                results[alpha_2]['all'].append(city['label_en']['value'])
                results[alpha_2]['en'].append(city['label_en']['value'])
            if 'label_fr' in city.keys():
                results[alpha_2]['all'].append(city['label_fr']['value'])
                results[alpha_2]['fr'].append(city['label_fr']['value'])
            if 'label_es' in city.keys():
                results[alpha_2]['all'].append(city['label_es']['value'])
                results[alpha_2]['es'].append(city['label_es']['value'])
            if 'label_it' in city.keys():
                results[alpha_2]['all'].append(city['label_it']['value'])
                results[alpha_2]['it'].append(city['label_it']['value'])
    else:
        logger.error('The request returned an error. Code : {code}'.format(code=response.status_code))
    for country in results:
        results[country]['all'] = list(set(results[country]['all']))
        if 'strict' in results[country].keys():
            results[country]['strict'] = list(set(results[country]['strict']))
        if 'en' in results[country].keys():
            results[country]['en'] = list(set(results[country]['en']))
        if 'fr' in results[country].keys():
            results[country]['fr'] = list(set(results[country]['fr']))
        if 'es' in results[country].keys():
            results[country]['es'] = list(set(results[country]['es']))
        if 'it' in results[country].keys():
            results[country]['it'] = list(set(results[country]['it']))
    return results


def get_all_universities() -> dict:
    query = '''
    SELECT DISTINCT ?country_alpha2 ?label_native ?label_en ?label_fr ?label_es ?label_it WHERE {
        ?university wdt:P31/wdt:P279* wd:Q38723 ;
                  wdt:P17 ?country .
        ?country wdt:P297 ?country_alpha2 .
        OPTIONAL { ?university wdt:P1705 ?label_native . }
        OPTIONAL { ?university rdfs:label ?label_en FILTER(lang(?label_en) = "en") . }
        OPTIONAL { ?university rdfs:label ?label_fr FILTER(lang(?label_fr) = "fr") . }
        OPTIONAL { ?university rdfs:label ?label_es FILTER(lang(?label_es) = "es") . }
        OPTIONAL { ?university rdfs:label ?label_it FILTER(lang(?label_it) = "it") . }
    }
    '''
    response = requests.get(WIKIDATA_SPARQL_URL, params={'query': query, 'format': 'json'})
    results = {}
    if response.status_code == requests.codes.ok:
        for university in response.json()['results']['bindings']:
            alpha_2 = university['country_alpha2']['value'].lower()
            if alpha_2 not in results.keys():
                results[alpha_2] = {}
                results[alpha_2]['all'] = []
                results[alpha_2]['en'] = []
                results[alpha_2]['fr'] = []
                results[alpha_2]['es'] = []
                results[alpha_2]['it'] = []
            if 'label_native' in university.keys():
                results[alpha_2]['all'].append(university['label_native']['value'])
            if 'label_en' in university.keys():
                results[alpha_2]['all'].append(university['label_en']['value'])
                results[alpha_2]['en'].append(university['label_en']['value'])
            if 'label_fr' in university.keys():
                results[alpha_2]['all'].append(university['label_fr']['value'])
                results[alpha_2]['fr'].append(university['label_fr']['value'])
            if 'label_es' in university.keys():
                results[alpha_2]['all'].append(university['label_es']['value'])
                results[alpha_2]['es'].append(university['label_es']['value'])
            if 'label_it' in university.keys():
                results[alpha_2]['all'].append(university['label_it']['value'])
                results[alpha_2]['it'].append(university['label_it']['value'])
    else:
        logger.error('The request returned an error. Code : {code}'.format(code=response.status_code))
    for country in results:
        results[country]['all'] = list(set(results[country]['all']))
        if 'en' in results[country].keys():
            results[country]['en'] = list(set(results[country]['en']))
        if 'fr' in results[country].keys():
            results[country]['fr'] = list(set(results[country]['fr']))
        if 'es' in results[country].keys():
            results[country]['es'] = list(set(results[country]['es']))
        if 'it' in results[country].keys():
            results[country]['it'] = list(set(results[country]['it']))
    return results


def get_all_hospitals() -> dict:
    query = '''
    SELECT DISTINCT ?country_alpha2 ?label_native ?label_en ?label_fr ?label_es ?label_it WHERE {
        ?hospital wdt:P31/wdt:P279* wd:Q16917 ;
                wdt:P17 ?country .
        ?country wdt:P297 ?country_alpha2 .
        OPTIONAL { ?hospital wdt:P1705 ?label_native . }
        OPTIONAL { ?hospital rdfs:label ?label_en FILTER(lang(?label_en) = "en") . }
        OPTIONAL { ?hospital rdfs:label ?label_fr FILTER(lang(?label_fr) = "fr") . }
        OPTIONAL { ?hospital rdfs:label ?label_es FILTER(lang(?label_es) = "es") . }
        OPTIONAL { ?hospital rdfs:label ?label_it FILTER(lang(?label_it) = "it") . }
    }
    '''
    response = requests.get(WIKIDATA_SPARQL_URL, params={'query': query, 'format': 'json'})
    results = {}
    if response.status_code == requests.codes.ok:
        for hospital in response.json()['results']['bindings']:
            alpha_2 = hospital['country_alpha2']['value'].lower()
            if alpha_2 not in results.keys():
                results[alpha_2] = {}
                results[alpha_2]['all'] = []
                results[alpha_2]['en'] = []
                results[alpha_2]['fr'] = []
                results[alpha_2]['es'] = []
                results[alpha_2]['it'] = []
            if 'label_native' in hospital.keys():
                results[alpha_2]['all'].append(hospital['label_native']['value'])
            if 'label_en' in hospital.keys():
                results[alpha_2]['all'].append(hospital['label_en']['value'])
                results[alpha_2]['en'].append(hospital['label_en']['value'])
            if 'label_fr' in hospital.keys():
                results[alpha_2]['all'].append(hospital['label_fr']['value'])
                results[alpha_2]['fr'].append(hospital['label_fr']['value'])
            if 'label_es' in hospital.keys():
                results[alpha_2]['all'].append(hospital['label_es']['value'])
                results[alpha_2]['es'].append(hospital['label_es']['value'])
            if 'label_it' in hospital.keys():
                results[alpha_2]['all'].append(hospital['label_it']['value'])
                results[alpha_2]['it'].append(hospital['label_it']['value'])
    else:
        logger.error('The request returned an error. Code : {code}'.format(code=response.status_code))
    for country in results:
        results[country]['all'] = list(set(results[country]['all']))
        if 'en' in results[country].keys():
            results[country]['en'] = list(set(results[country]['en']))
        if 'fr' in results[country].keys():
            results[country]['fr'] = list(set(results[country]['fr']))
        if 'es' in results[country].keys():
            results[country]['es'] = list(set(results[country]['es']))
        if 'it' in results[country].keys():
            results[country]['it'] = list(set(results[country]['it']))
    return results


def get_info_from_country(alpha_2: str = None) -> dict:
    country = pycountry.countries.get(alpha_2=alpha_2)
    info = []
    if hasattr(country, 'name'):
        info.append(country.name)
    if hasattr(country, 'official_name'):
        info.append(country.official_name)
    if hasattr(country, 'common_name'):
        info.append(country.common_name)
    return {'alpha_2': country.alpha_2, 'alpha_3': country.alpha_3,
            'info': info}


def get_white_list_from_country(alpha_2: str = None) -> dict:
    alpha_2 = alpha_2.upper()
    dirname = os.path.dirname(__file__)
    with open(os.path.join(dirname, FILE_COUNTRY_WHITE_LIST), 'r') as file:
        country_white_list = json.load(file)
        if alpha_2 in country_white_list.keys():
            white_list = country_white_list[alpha_2]
        else:
            white_list = []
    return {'white_list': white_list}


def get_stop_words_from_country(alpha_2: str = None) -> dict:
    alpha_2 = alpha_2.upper()
    dirname = os.path.dirname(__file__)
    with open(os.path.join(dirname, FILE_COUNTRY_FORBIDDEN), 'r') as file:
        country_stop_words = json.load(file)
        if alpha_2 in country_stop_words.keys():
            stop_words = country_stop_words[alpha_2]
        else:
            stop_words = []
    return {'stop_words': stop_words}


def init_country() -> None:
    es = MyElastic()
    mapping = {'mappings': {'properties': {'universities': {'type': 'text'}}}}
    es.create_index(index=ES_INDEX, mapping=mapping)
    all_cities = get_all_cities()
    all_universities = get_all_universities()
    all_hospitals = get_all_hospitals()
    # TODO: use helpers.parallel_bulk
    for country in pycountry.countries:
        country = country.alpha_2.lower()
        body = {}
        info = get_info_from_country(country)
        body.update(info)
        cities_all = all_cities[country]['all'] if country in all_cities.keys() and 'all' in \
            all_cities[country].keys() else []
        cities_strict = all_cities[country]['strict'] if country in all_cities.keys() and 'strict' in \
            all_cities[country].keys() else []
        cities_en = all_cities[country]['en'] if country in all_cities.keys() and 'en' in all_cities[country].keys() \
            else []
        cities_fr = all_cities[country]['fr'] if country in all_cities.keys() and 'fr' in all_cities[country].keys() \
            else []
        cities_es = all_cities[country]['es'] if country in all_cities.keys() and 'es' in all_cities[country].keys() \
            else []
        cities_it = all_cities[country]['it'] if country in all_cities.keys() and 'it' in all_cities[country].keys() \
            else []
        body.update({'cities': cities_all, 'cities_strict': cities_strict, 'cities_en': cities_en,
                     'cities_fr': cities_fr, 'cities_es': cities_es, 'cities_it': cities_it})
        universities_all = all_universities[country]['all'] if country in all_universities.keys() and 'all' in \
            all_universities[country].keys() else []
        universities_en = all_universities[country]['en'] if country in all_universities.keys() and 'en' in \
            all_universities[country].keys() else []
        universities_fr = all_universities[country]['fr'] if country in all_universities.keys() and 'fr' in \
            all_universities[country].keys() else []
        universities_es = all_universities[country]['es'] if country in all_universities.keys() and 'es' in \
            all_universities[country].keys() else []
        universities_it = all_universities[country]['it'] if country in all_universities.keys() and 'it' in \
            all_universities[country].keys() else []
        body.update({'universities': universities_all, 'universities_en': universities_en, 'universities_fr':
                    universities_fr, 'universities_es': universities_es, 'universities_it': universities_it})
        hospitals_all = all_hospitals[country]['all'] if country in all_hospitals.keys() and 'all' in \
            all_hospitals[country].keys() else []
        hospitals_en = all_hospitals[country]['en'] if country in all_hospitals.keys() and 'en' in \
            all_hospitals[country].keys() else []
        hospitals_fr = all_hospitals[country]['fr'] if country in all_hospitals.keys() and 'fr' in \
            all_hospitals[country].keys() else []
        hospitals_es = all_hospitals[country]['es'] if country in all_hospitals.keys() and 'es' in \
            all_hospitals[country].keys() else []
        hospitals_it = all_hospitals[country]['it'] if country in all_hospitals.keys() and 'it' in \
            all_hospitals[country].keys() else []
        body.update({'hospitals': hospitals_all, 'hospitals_en': hospitals_en, 'hospitals_fr': hospitals_fr,
                     'hospitals_es': hospitals_es, 'hospitals_it': hospitals_it})
        white_list = get_white_list_from_country(country)
        body.update(white_list)
        stop_words = get_stop_words_from_country(country)
        body.update(stop_words)
        es.index(index=ES_INDEX, body=body, refresh=True)


if __name__ == '__main__':
    init_country()
