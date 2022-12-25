import argparse
import json

import mysql.connector
import pandas as pd
from mysql.connector import errorcode
from bs4 import BeautifulSoup, SoupStrainer
import requests

def main(args):

    url = "https://www.fantasypros.com/nfl/rankings/ros-overall.php"
    with requests.Session() as session:
        r = session.get(url)
        strainer = SoupStrainer(id='ranking-table')
        soup = BeautifulSoup(r.text, features='lxml', parse_only=strainer)

        i = 1
        while soup.select("#ranking-table > tbody > tr:nth-child(%d)" % i):
            row = soup.select("#ranking-table > tbody > tr:nth-child(%d)" % i)
            name_soup = soup.select("#ranking-table > tbody > tr:nth-child(1) > td:nth-child(3) > div > a:nth-child(1)")
            team_soup = soup.select("#ranking-table > tbody > tr:nth-child(1) > td:nth-child(3) > div > span")
            pos_soup = soup.select("#ranking-table > tbody > tr:nth-child(1) > td:nth-child(4)")
            print("done")

    #connect_to_db()




def connect_to_db():
    try:
        cnx = mysql.connector.connect(user='root',
                                      password="example",
                                      database="nfl")
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
    else:
        #create_database(cnx, "nfl")
        #create_tables(cnx.cursor())
        #insert_player(cnx, "1", "turd", "ferguson")
        get_player(cnx, "1")
        cnx.close()


def insert_player(cnx, pid, fn, ln):
    cursor = cnx.cursor()
    cursor.execute("USE nfl")

    add_player = ("INSERT INTO test2 "
                  "(pid, fn, ln) "
                  "VALUES (%s, %s, %s)")
    player_to_add = (pid, fn, ln)

    try:
        cursor.execute(add_player, player_to_add)
        cnx.commit()
    except mysql.connector.Error as err:
        print(err)
    cursor.close()


def get_player(cnx, pid):
    cursor = cnx.cursor()
    cursor.execute("USE {}".format("nfl"))

    query = ("SELECT * FROM test2"
             "WHERE pid=%s")

    cursor.execute(query, [pid])

    for (fn, ln, pid) in cursor:
        print(f"{fn} {ln} has pid: {pid}")

    cursor.close()


def create_database(cnx, db_name):
    cursor = cnx.cursor()
    try:
        cursor.execute(
            "CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(db_name))
    except mysql.connector.Error as err:
        print("Failed creating database: {}".format(err))
        exit(1)

    try:
        cursor.execute("USE {}".format(db_name))
    except mysql.connector.Error as err:
        print("Database {} does not exists.".format(db_name))
        if err.errno == errorcode.ER_BAD_DB_ERROR:
            create_database(cursor)
            print("Database {} created successfully.".format(db_name))
            cnx.database = db_name
        else:
            print(err)
            exit(1)


def create_tables(cursor):
    cursor.execute("USE {}".format("nfl"))

    tables = {}
    # tables['test'] = (
    #     "CREATE TABLE `test` ("
    #     "   `pid` varchar(14) NOT NULL,"
    #     "   `fn` varchar(14) NOT NULL,"
    #     "   `ln` varchar(14) NOT NULL,"
    #     "   PRIMARY_KEY (`pid`)"
    #     ") ENGINE=InnoDB")

    tables['test2'] = (
        "CREATE TABLE `test2` ("
        "  `pid` char(14) NOT NULL,"
        "  `fn` varchar(14) NOT NULL,"
        "  `ln` varchar(14) NOT NULL,"
        "  PRIMARY KEY (`pid`), UNIQUE KEY `pid` (`pid`)"
        ") ENGINE=InnoDB")

    for table_name in tables:
        table_description = tables[table_name]
        try:
            print("Creating table {}: ".format(table_name), end='')
            cursor.execute(table_description)
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                print("already exists.")
            else:
                print(err.msg)
        else:
            print("OK")

    cursor.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-i", "--init_db",
                    type = bool,
                    default=False,
                    help="create a new db before processing")
    args = parser.parse_args()
    main(args)
