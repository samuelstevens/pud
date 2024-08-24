# internal to python
import re
from urllib.parse import unquote
from string import ascii_uppercase
from sqlite3 import IntegrityError
from typing import List, Tuple

# external
import requests
from bs4 import BeautifulSoup


from .constants import BASE_URL
from .db import initialize_db

CON = initialize_db()


def write_words_for_letter(prefix: str):
    if not prefix:
        raise ValueError(f'Prefix {prefix} needs to be at least one letter.')

    def make_url():
        if page_num > 1:
            return f'{BASE_URL}/browse.php?character={letter}&page={page_num}'
        return f'{BASE_URL}/browse.php?character={letter}'

    letter = prefix.upper()

    page_num: int = CON.execute(
        'SELECT max(page_num) FROM word WHERE letter = ?', (letter,)).fetchone()[0]

    if not page_num:
        page_num = 1

    url = make_url()
    req = requests.get(url)
    last_page_size = 1
    while last_page_size != 0:
        soup = BeautifulSoup(req.text, features="html.parser")
        a_tags = soup.find_all('a', href=re.compile(r'/define.php'))

        pattern = re.compile(
            r'\/define\.php\?term=(.*)')

        links = [l['href'] for l in a_tags]

        encoded_words: List[str] = [pattern.search(l).group(1)
                                    for l in links if pattern.search(l)]

        words: List[str] = [unquote(w) for w in encoded_words]

        last_page_size = len(words)

        formatted_words: List[Tuple[str, int, int, str]] = [
            (w, 0, page_num, letter) for w in words]
        try:
            CON.executemany(
                'INSERT INTO word(word, complete, page_num, letter) VALUES (?, ?, ?, ?)',
                formatted_words)
            CON.commit()
        except IntegrityError:
            # IntegrityError normally occurs when we try to
            # insert words that are already in the database.
            pass
        first_word = ""
        if len(words) >0 :
            first_word = words[0]
        print(
            f'Working on page {page_num} for {letter}. Total {140 * (page_num - 1) + len(words)} {letter} words. first word of page is {first_word}')

        page_num += 1
        url = make_url()
        req = requests.get(url)


def write_all_words():
    for letter in ascii_uppercase + '*':
        write_words_for_letter(letter)
