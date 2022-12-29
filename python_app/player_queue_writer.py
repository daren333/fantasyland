import argparse
import csv
import uuid
from datetime import date

import boto3
import sqlalchemy
from sqlalchemy import create_engine, select

from python_app import config
from python_app.scrape_stats import fix_team_abbrev, scrape_playerlist
from python_app.classes.Player import Player
from bs4 import BeautifulSoup, SoupStrainer
import requests

from python_app.writer import init_mysql_db


def read_fantasy_pros_rank_sheet(csv_path):
    players = []
    with open(csv_path) as csv_file:
        reader = csv.reader(csv_file)
        for row in reader:
            # Skip header row
            if row[0] and row[0] != 'RK':
                fn = row[1].split()[0]
                ln = row[1].split()[1]
                team = fix_team_abbrev(row[2])
                pos = row[3][:2]
                players.append(Player(fn, ln, pos, team))
    return players


def get_pid(engine, player):
    connection = engine.connect()
    player_info = sqlalchemy.Table('player_info_table', sqlalchemy.MetaData(), autoload=True, autoload_with=engine)

    query = select([player_info.columns.pid])\
        .where(player_info.columns.url == player.url)
    query_result = connection.execute(query).fetchall()
    connection.close()

    # if no result, create a pid for that player
    if len(query_result) == 0:
        return str(uuid.uuid1())
    # if one result return pid
    elif len(query_result) == 1:
        return query_result[0][0]
    # if more than one result throw an exception
    else:
        raise Exception(f"More than one pid found for player {player.fn} {player.ln} at position {player.pos} and team {player.curr_team}")


def create_sqs_message(sqs_client, player_json):
    queue = sqs_client.get_queue_by_name(QueueName=config.sqs_queue_name)
    response = queue.send_message(MessageBody=player_json)
    print(response.get('MessageId'))


def main(args):
    engine = create_engine(
        "mysql+pymysql://" + config.mysql_user + ":" + config.mysql_pw + "@" + config.mysql_host + "/" + config.mysql_db)

    sqs_client = boto3.resource("sqs")
    today = date.today()
    # if september or later, get this years data. If January-August we want last years data
    year = str(today.year) if today.month > 9 else str(today.year - 1)
    playerlist_url = f"https://www.pro-football-reference.com/years/{year}/fantasy.htm"

    players = scrape_playerlist(url=playerlist_url, max_rows=34) if args.test_mode else scrape_playerlist(url=playerlist_url)

    for player in players:
        player.pid = get_pid(engine, player)
        player_json = player.get_sqs_json()
        print(f"creating sqs message for {player_json}")
        create_sqs_message(sqs_client, player_json)
    engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-t", "--test_mode",
                        action="store_true",
                        help="enable test mode")
    args = parser.parse_args()
    main(args)