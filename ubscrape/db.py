import sqlite3

from .jsonwriter import JsonWriter
from .csvwriter import CsvWriter

DB_FILE_NAME = 'urban-dict.db'


def get_connection():
    return sqlite3.connect(DB_FILE_NAME)


def initialize_db():
    con = get_connection()

    con.execute('''CREATE TABLE IF NOT EXISTS word (
    word text PRIMARY KEY,
    letter text NOT NULL,
    complete integer NOT NULL,
    page_num integer NOT NULL
    );''')

    con.execute('''CREATE TABLE IF NOT EXISTS definition (
    id INTEGER PRIMARY KEY,
    word_id TEXT NOT NULL,
    definition TEXT NOT NULL,
    author TEXT,
    example TEXT,
    thumbs_up INTEGER,
    thumbs_down INTEGER,
    permalink TEXT,
    written_on TEXT,
    FOREIGN KEY (word_id) REFERENCES word (word)
    );''')

    con.commit()

    return con


def clear_database():
    con = get_connection()

    con.execute('DROP TABLE definition')
    con.execute('DROP TABLE word')

    con.commit()

    con.close()


def dump_database(arg, csv=False):
    con = get_connection()

    if csv:
        writer = CsvWriter()

        if isinstance(arg, str):
            writer = CsvWriter(out=arg)
    else:
        writer = JsonWriter()

        if isinstance(arg, str):
            writer = JsonWriter(out=arg)

    print(f'Dumping to: {writer.path}')

    prev_word = ''
    definition_set = set()

    query = 'SELECT word.word, definition.definition FROM definition INNER JOIN word ON definition.word_id=word.word ORDER BY word.word ASC;'

    for (word, definition) in con.execute(query).fetchall():
        if word == prev_word:
            # add to the same set
            definition_set.add(definition)

        if word != prev_word:
            # dump this definition and start a new set
            writer.write_word(prev_word, definition_set)

            prev_word = word
            definition_set = set([definition])

    writer.write_word(prev_word, definition_set)
    writer.dump_pool()
