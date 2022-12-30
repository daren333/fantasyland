import argparse
import csv
import uuid
from datetime import date

import boto3
import sqlalchemy
from sqlalchemy import create_engine, select

import config
from scrape_stats import fix_team_abbrev, scrape_playerlist
from classes.Player import Player


def get_pid(engine, player):
    connection = engine.connect()
    player_info = sqlalchemy.Table('player_info_table', sqlalchemy.MetaData(), autoload=True, autoload_with=engine)

    query = select([player_info.columns.pid])\
        .where(player_info.columns.url == player.url)
    query_result = connection.execute(query).fetchall()
    connection.close()

    # if player not in db yet, create a pid for that player and enable full scrape mode
    if len(query_result) == 0:
        pid = str(uuid.uuid1())
        full_scrape_mode = True
    # if player in db return pid and do not enable full scrape mode (we already have their past stats)
    elif len(query_result) == 1:
        pid = query_result[0][0]
        full_scrape_mode = False
    # if more than one result throw an exception
    else:
        raise Exception(f"More than one pid found for player {player.fn} {player.ln} at position {player.pos} and team {player.curr_team}")

    return (pid, full_scrape_mode)


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

    if args.test_mode:
        players = scrape_playerlist(url=playerlist_url, max_rows=34)
    else:
        scrape_playerlist(url=playerlist_url)

    for player in players:
        player.pid, full_scrape_enabled = get_pid(engine, player)
        player_json = player.get_sqs_json(full_scrape_enabled)
        print(f"creating sqs message for {player_json}")
        if not args.test_mode:
            create_sqs_message(sqs_client, player_json)
    engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-t", "--test_mode",
                        action="store_true",
                        help="enable test mode")
    args = parser.parse_args()
    main(args)