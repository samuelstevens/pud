import multiprocessing as mp
from typing import List, Tuple

import json

from bs4 import BeautifulSoup
import requests

from .constants import BASE_URL
from .constants import DEF_BASE_URL
from .db import initialize_db

CON = initialize_db()


def define_word(word: str) -> List[str]:
    if not word:
        raise ValueError('Must pass a word.')

    url = f'{BASE_URL}/define.php'

    req = requests.get(url, params={'term': word})

    soup = BeautifulSoup(req.text, features="html.parser")

    meaning_tags = soup.find_all('div', {'class': 'meaning'})

    definitions: List[str] = [t.text for t in meaning_tags]

    return definitions

def define_word_by_api(word: str) -> List[dict]:
    if not word:
        raise ValueError('Must pass a word.')

    url = f'{DEF_BASE_URL}/define'

    response = requests.get(url, params={'term': word, 'page': 1, 'per_page':100})

    data = json.loads(response.text)
    return data.get('list', [])

def write_definition(word_t: Tuple[str]) -> List[str]:
    # word will always be a tuple when this function is called from define_all_words().
    # so in `cli.py`, we make word a tuple to match the type signature.
    word = word_t[0]

    # Note: this code will always make a network request.
    # If offline support for definitions was required, it
    # could check the local db for any definitions.
    defs: List[str] = define_word(word)
    formatted_defs: List[Tuple[str, str]] = [(d, word) for d in defs]

    CON.executemany(
        'INSERT INTO definition(definition, word_id) VALUES (?, ?)', formatted_defs)
    CON.execute('UPDATE word SET complete = 1 WHERE word = ?', word_t)
    CON.commit()

    return defs

def write_definition_by_api(word_t: Tuple[str]) -> List[dict]:
    # word will always be a tuple when this function is called from define_all_words().
    # so in `cli.py`, we make word a tuple to match the type signature.
    word = word_t[0]

    # Note: this code will always make a network request.
    # If offline support for definitions was required, it
    # could check the local db for any definitions.
    defs: List[dict] = define_word_by_api(word)
    formatted_defs: List[Tuple[str, str, str, str, str, str, str, str, str]] = [(res["defid"], res["word"],res["definition"],res["permalink"],res["thumbs_up"],res["author"],res["written_on"],res["example"],res["thumbs_down"]) for res in defs]

    CON.executemany(
        'INSERT OR IGNORE INTO definition(id, word_id, definition, permalink, thumbs_up, author, written_on, example, thumbs_down) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', formatted_defs)
    CON.execute('UPDATE word SET complete = 1 WHERE word = ?', word_t)
    CON.commit()
    print(f'Defined : {word}')
    return defs


def define_all_words():
    pool = mp.Pool(mp.cpu_count())

    words = CON.execute(
        'SELECT word FROM word WHERE complete = 0').fetchall()

    # pool.map(write_definition, words, chunksize=200)
    pool.map(write_definition_by_api, words, chunksize=200)
