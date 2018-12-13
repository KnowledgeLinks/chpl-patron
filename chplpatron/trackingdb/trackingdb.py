"""
Simple postal_code lookup implementation
"""
__author__ = "Jeremy Nelson, Mike Stabile"

import os
import sqlite3

from hashlib import sha512

from chplpatron.exceptions import RegisteredEmailError

DB_NAME = "tracking-db.sqlite"
TRACKING_DB_SETUP = None
CURRENT_DIR = os.path.dirname(__file__)
DB_PATH = None
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
    DB_PATH = os.path.join(CURRENT_DIR, DB_NAME)
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    # Create table
    cur.execute("CREATE TABLE IF NOT EXISTS  {} "
                "("
                "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,"
                "date DATETIME DEFAULT CURRENT_TIMESTAMP," 
                "date_retrieved DATETIME,"
                "card_number INTEGER,"
                "email VARCHAR NOT NULL UNIQUE"
                ");".format(REG_TBL))
    con.commit()
    cur.close()
    con.close()
    TRACKING_DB_SETUP = True
    return func


def hash_email(email):
    """
    hashes the email for storing in the database

    :param email:
    :return: hashed email
    """
    return sha512(email.lower().strip().encode()).hexdigest()


@setup
def add_registration(card_number, email):
    """ Checks to see if the email address as has already been registered
        request args:
            g587-email: the email address to check
    """
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    qry = ("INSERT INTO {} "
           "(email, card_number) " 
           "VALUES (?,?);").format(REG_TBL)

    try:
        cur.execute(qry, (hash_email(email), card_number,))
        con.commit()
    except sqlite3.IntegrityError:
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
                "WHERE card_number=?".format(tbl=REG_TBL),
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


if __name__ == '__main__':
    print("Main method not implemented")
