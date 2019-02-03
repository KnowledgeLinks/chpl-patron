"""
Simple postal_code lookup implementation
"""
__author__ = "Jeremy Nelson, Mike Stabile"

import os
import sqlite3


from chplpatron.exceptions import RegisteredEmailError
from chplpatron.utilities.baseutilities import hash_email


DB_NAME = "tracking-db.sqlite"
TRACKING_DB_SETUP = None
CURRENT_DIR = os.path.dirname(__file__)
DB_PATH = ""
REG_TBL = "LibraryCardRequest"


def setup(func):
    """
    decorator ensuring that the database is setup prior to any calls
    :param func:
    :return: None
    """
    global TRACKING_DB_SETUP
    global DB_PATH
    if TRACKING_DB_SETUP:
        return func
    DB_PATH = str(os.path.join(CURRENT_DIR, DB_NAME))
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    # Create table
    cur.execute("CREATE TABLE IF NOT EXISTS  {} "
                "("
                "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,"
                "date DATETIME DEFAULT CURRENT_TIMESTAMP," 
                "date_retrieved DATETIME,"
                "patron_id VARCHAR NOT NULL UNIQUE,"
                "email VARCHAR NOT NULL UNIQUE,"
                "location VARCHAR NOT NULL DEFAULT 'unknown',"
                "boundary INTEGER NOT NULL DEFAULT -1"
                ");".format(REG_TBL))
    con.commit()
    cur.close()
    con.close()
    TRACKING_DB_SETUP = True
    return func


@setup
def add_registration(patron_id, email, location="unknown", boundary=-1):
    """
    Adds a registration to the database

    :param patron_id: the id from sierra
    :param email: email addreess
    :param location: internal for in-house reg and external for non
    :param boundary: -1 = unknown, 1 = within, 0 = not within
    :return:
    """
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    qry = ("INSERT INTO {} "
           "(email, patron_id, location, boundary) " 
           "VALUES (?,?,?,?);").format(REG_TBL)

    try:
        if boundary is None:
            boundary = -1
        cur.execute(qry, (hash_email(email),
                          patron_id,
                          location,
                          int(boundary),))
        con.commit()
    except sqlite3.IntegrityError:
        # pass
        cur.close()
        con.close()
        raise RegisteredEmailError(email)
    cur.close()
    con.close()
    return True


@setup
def lookup_email(email):
    """
    searches the database for the email
    :param email:
    :return: row of data
    """
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    qry = ("SELECT * "
           "FROM {tbl} "
           "WHERE email=?;").format(tbl=REG_TBL)
    cur.execute(qry, (hash_email(email),))
    data = cur.fetchone()
    cur.close()
    con.close()
    return data


@setup
def check_email(email):
    """
    Checks to see if the email was previously registered
    :param email: email address to check
    :return: True if email has not been registered
    :raises: RegisteredEmailError if registered
    """
    if lookup_email(email):
        raise RegisteredEmailError(email)
    return True


@setup
def lookup_card_number(card_number):
    """
    searches the database for the card_number
    :param card_number:
    :return:
    """
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT * "
                "FROM {tbl} "
                "WHERE patron_id=?".format(tbl=REG_TBL),
                (card_number,))
    data = cur.fetchone()
    cur.close()
    con.close()
    return data


@setup
def print_table(table):
    """
    prints all records in a table
    :param table: name of the table
    :return: None
    """
    print("Data for table '{}'".format(table))
    print("----------------------------------------------------")
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT * FROM {}".format(table))
    print([description[0] for description in cur.description])
    rows = cur.fetchall()
    for row in rows:
        print(row)
    cur.close()
    con.close()


def load_old_data(old_db_path):
    """
    loads data from old database into new database
    :param old_db_path: file path to database
    :return:
    """
    old_con = sqlite3.connect(old_db_path)
    con = sqlite3.connect(DB_PATH)
    old_cur = old_con.cursor()
    old_cur.execute("SELECT * FROM LibraryCardRequest;")
    old_data = old_cur.fetchall()
    old_data = [tuple(i for i in item[1:]) for item in old_data]
    # pprint.pprint(old_data[:10])
    qry = ("INSERT INTO {} "
           "(date, date_retrieved, patron_id, email) "
           "VALUES (?,?,?,?);").format(REG_TBL)
    cur = con.cursor()
    cur.executemany(qry, old_data)
    con.commit()
    cur.close()
    con.close()


def columns():
    """
    list column names
    :return list: of column names
    """
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT * "
                "FROM {tbl} "
                "LIMIT 1".format(tbl=REG_TBL))
    names = [description[0] for description in cur.description]
    cur.close()
    con.close()
    return names


def get_data():
    """
    list column names
    :return list: of column names
    """
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT * "
                "FROM {tbl} ".format(tbl=REG_TBL))
    data = cur.fetchall()
    cur.close()
    con.close()
    return data


def registration_by_month():
    """
    :return: a list of number of registrations for month and year
    """
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT time, count(time) "
                "FROM (SELECT strftime('%Y-%m', date) as time "
                "FROM {tbl}) GROUP BY time;".format(tbl=REG_TBL))
    data = cur.fetchall()
    cur.close()
    con.close()
    return data


if __name__ == '__main__':
    print_table(REG_TBL)
