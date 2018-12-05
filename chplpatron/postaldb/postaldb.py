"""Chapel Hill Public Library Patron Self-Registration"""
__author__ = "Jeremy Nelson, Mike Stabile"

import csv
import os
import sqlite3

from chplpatron.chplexceptions import InvalidPostalCode

POSTAL_DB_SETUP = None
CURRENT_DIR = os.path.abspath(os.curdir)
DB_PATH = os.path.join(CURRENT_DIR, "postal-db.sqlite")
POSTAL_CSV = os.path.join(CURRENT_DIR, "resources", "US.txt")


def setup():
    global POSTAL_DB_SETUP
    if POSTAL_DB_SETUP:
        return

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    # --- test row count --------------------------------------------
    qry = ("SELECT name "
           "FROM sqlite_master "
           "WHERE type='table' AND name='resources';")
    count = [0]
    if bool(len(cur.execute(qry).fetchall())):
        count = cur.execute("SELECT count(*) FROM resources;").fetchone()
    if count[0] > 1000:
        POSTAL_DB_SETUP = True
        return

    # --- row count was too small --> reload ------------------------
    # Drop table
    cur.execute("DROP TABLE IF EXISTS resources")
    con.commit()
    # Create table
    cur.execute("CREATE TABLE IF NOT EXISTS resources ("
                "id integer PRIMARY KEY AUTOINCREMENT NOT NULL, "
                "postal_code text NOT NULL, "
                "city text NOT NULL, "
                "state_long text NOT NULL, "
                "state_short text, "
                "lat text, "
                "long text) ;")
    con.commit()
    # load data
    ins_qry = ("INSERT INTO resources ("
               "postal_code, "
               "city, "
               "state_long, "
               "state_short, "
               "lat, "
               "long) "
               "VALUES (?,?,?,?,?,?)")
    with open(POSTAL_CSV,
              "r") as data:
        postal_data = list(csv.reader(data, delimiter='\t'))
        for ln in postal_data:
            cur.execute(ins_qry,
                        (ln[1], ln[2], ln[3], ln[4], ln[9], ln[10]))
    con.commit()
    cur.close()
    con.close()
    POSTAL_DB_SETUP = True


def get_locale_from_postal_code(postal_value):
    """ Checks to see if the email address as has already been registered
        request args:
            g587-email: the email address to check
    """
    setup()
    postal = postal_value
    if len(postal) > 5:
        postal = postal[:5]
    if len(postal) == 5:
        con = sqlite3.connect(DB_PATH)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cities = cur.execute("SELECT state_long as state, "
                             "postal_code, "
                             "city "
                             "FROM resources WHERE postal_code = ?",
                             (postal_value,)).fetchall()
        if len(cities) > 0:
            return [dict(city) for city in cities]
    raise InvalidPostalCode(postal_value)


if __name__ == '__main__':
    print(get_locale_from_postal_code('81137'))
