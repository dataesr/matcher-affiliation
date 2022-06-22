import os
import pandas as pd
import re
import requests
import shutil
import string
import unicodedata

from tempfile import mkdtemp
from zipfile import ZipFile

from project.server.main.config import CHUNK_SIZE, ZONE_EMPLOI_INSEE_DUMP

ENGLISH_STOP = ['a', 'an', 'and', 'are', 'as', 'at', 'be', 'but', 'by', 'for', 'if', 'in', 'into', 'is', 'it', 'no',
                'not', 'of', 'on', 'or', 'such', 'that', 'the', 'their', 'then', 'there', 'these', 'they', 'this',
                'to', 'was', 'will', 'with']

FRENCH_STOP = ["au","aux","avec","ce","ces","dans","de","des","du","elle","en","et","eux","il","je","la","le","leur","lui","ma","mais","me","même","mes","moi","mon","ne","nos","notre","nous","on","ou","par","pas","pour","qu","que","qui","sa","se","ses","sur","ta","te","tes","toi","ton","tu","un","une","vos","votre","vous","c","d","j","l","à","m","n","s","t","y","étée","étées","étant","suis","es","êtes","sont","serai","seras","sera","serons","serez","seront","serais","serait","serions","seriez","seraient","étais","était","étions","étiez","étaient","fus","fut","fûmes","fûtes","furent","sois","soit","soyons","soyez","soient","fusse","fusses","fussions","fussiez","fussent","ayant","eu","eue","eues","eus","ai","avons","avez","ont","aurai","aurons","aurez","auront","aurais","aurait","aurions","auriez","auraient","avais","avait","aviez","avaient","eut","eûmes","eûtes","eurent","aie","aies","ait","ayons","ayez","aient","eusse","eusses","eût","eussions","eussiez","eussent","ceci","cela","celà","cet","cette","ici","ils","les","leurs","quel","quels","quelle","quelles","sans","soi"]

GEO_IGNORED = ['union'] + FRENCH_STOP + ENGLISH_STOP

ACRONYM_IGNORED = ['usa', 'pasteur', 'cedex', 'paris', 'ea', 'team', 'innovation', 'sphere', 'st', 'and', 'gu', 'care', 'medecine', 'unite'] + FRENCH_STOP + ENGLISH_STOP

def remove_stop(text: str, stopwords: list) -> str:
    pattern = re.compile(r'\b(' + r'|'.join(stopwords) + r')\b\s*', re.IGNORECASE)
    return pattern.sub('', text)

def remove_parenthesis(x):
    if isinstance(x, str):
        return re.sub("[\(\[].*?[\)\]]", "", x)
    return x

def clean_list(data: list, stopwords = [], ignored = [], remove_inside_parenthesis = True, min_token = 1) -> list:
    # Cast data into list if needed
    if not isinstance(data, list):
        data = [data]
    data = list(filter(None, data))
    # Remove duplicates
    data = [k for k in list(set(data)) if k and isinstance(k, str)]
    for ix, e in enumerate(data):
        if remove_inside_parenthesis:
            e = remove_parenthesis(e)
        if stopwords:
            e = remove_stop(e, stopwords)
        data[ix] = e
    data = [k for k in data if k.lower() not in ignored]
    data = [k for k in data if len(get_token_basic(k)) >= min_token]
    return data

def chunks(lst: list, n: int) -> list:
    """Yield successive n-sized chunks from list."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def get_token_basic(x):
    return x.split(' ')

def get_tokens(indices_client, analyzer: str, index: str, text: str) -> list:
    try:
        tokens = indices_client.analyze(body={'analyzer': analyzer, 'text': text}, index=index)['tokens']
    except:
        return [{'token': t} for t in text.split(' ')]
    return tokens


def remove_ref_index(query: str) -> str:
    """Remove the first 2 digits of a string if any."""
    if len(query.split(' '))> 5:
        rgx = re.compile(r"^(\d){1,2}([A-Za-z])(.*)")
        return rgx.sub("\\2\\3", query).strip()
    return query.strip()


def strip_accents(text: str) -> str:
    """Normalize accents and stuff in string."""
    text = text.replace('’', ' ')
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')


def delete_punctuation(text: str) -> str:
    """Delete all punctuation in a string."""
    return text.lower().translate(str.maketrans(string.punctuation, len(string.punctuation) * ' '))


def normalize_text(text: str = None, remove_separator: bool = True) -> str:
    """Normalize string. Delete punctuation and accents."""
    if isinstance(text, str):
        text = text.replace('\xa0', ' ').replace('\n', ' ')
        text = delete_punctuation(text)
        text = strip_accents(text)
        sep = '' if remove_separator else ' '
        text = sep.join(text.split())
    return text or ''


def get_alpha2_from_french(user_input):
    ref = {
        'Afrique du Sud': 'za',
        'Argentine': 'ar',
        'Autriche': 'at',
        'Brésil': 'br',
        'Canada': 'ca',
        'Chili': 'cl',
        'Chine': 'cn',
        'Corée du Sud': 'kr',
        'Etats-Unis': 'us',
        'Ethiopie': 'et',
        'France': 'fr',
        'Inde': 'in',
        'Israël': 'il',
        'Italie': 'it',
        'Japon': 'jp',
        'Mexique': 'mx',
        'Pays-Bas': 'nl',
        'Russie': 'ru',
        'Sénégal': 'sn',
        'Singapour': 'sg'
    }
    return ref.get(user_input)


def download_insee_data() -> dict:
    insee_downloaded_file = 'insee_data_dump.zip'
    insee_unzipped_folder = mkdtemp()
    response = requests.get(url=ZONE_EMPLOI_INSEE_DUMP, stream=True)
    with open(insee_downloaded_file, 'wb') as file:
        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
            file.write(chunk)
    with ZipFile(insee_downloaded_file, 'r') as file:
        file.extractall(insee_unzipped_folder)
    data = pd.read_excel(f'{insee_unzipped_folder}/ZE2020_au_01-01-2021.xlsx', sheet_name='Composition_communale',
                         skiprows=5).to_dict(orient='records')
    os.remove(path=insee_downloaded_file)
    shutil.rmtree(path=insee_unzipped_folder)
    return data


def has_a_digit(text: str = '') -> bool:
    for char in text:
        if char.isdigit():
            return True
    return False


def get_common_words(objects: list, field: string, split: bool = True, threshold: int = 10) -> list:
    dictionary = {}
    for obj in objects:
        for text in obj.get(field, []):
            if split:
                words = normalize_text(text=text, remove_separator=False).split(' ')
            else:
                words = [normalize_text(text=text, remove_separator=False)]
            for word in words:
                if word not in dictionary:
                    dictionary[word] = 0
                dictionary[word] += 1
    result = []
    for entry in dictionary:
        if dictionary[entry] >= threshold:
            result.append(entry)
    return result