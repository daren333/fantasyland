import argparse
import uuid
from datetime import date

import boto3
import sqlalchemy
from sqlalchemy import create_engine, select

import config
from scrape_stats import fix_team_abbrev, scrape_playerlist, get_player_name_and_link_from_playerlist, get_player_age_from_playerlist
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
    response = sqs_client.send_message(QueueUrl=config.sqs_queue_url, MessageBody=player_json)
    print(response.get('MessageId'))


def publish_sns_message(sns_client):
    response = sns_client.publish(TopicArn=config.sns_topic_arn, Message=f"queue writer finished")
    print(response)


def main(args):
    engine = create_engine(
        "mysql+pymysql://" + config.mysql_user + ":" + config.mysql_pw + "@" + config.mysql_host + "/" + config.mysql_db)

    sqs_client = boto3.client("sqs")
    sns_client = boto3.client("sns")

    today = date.today()
    # if september or later, get this years data. If January-August we want last years data
    year = str(today.year) if today.month > 9 else str(today.year - 1)
    playerlist_url = f"https://www.pro-football-reference.com/years/{year}/fantasy.htm"

    soup = scrape_playerlist(url=playerlist_url)
    i = 1
    while soup.select(f"#fantasy > tbody > tr:nth-child({i})"):
        # skip header rows
        if not soup.select(f"#fantasy > tbody > tr:nth-child({i}) > th.ranker.sort_default_asc.show_partial_when_sorting.center"):
            player_name, player_link = get_player_name_and_link_from_playerlist(soup.select(f'#fantasy > tbody > tr:nth-child({i}) > td:nth-child(2) > a'))
            player_fn = player_name.split()[0]
            # Get multi last names like St. Brown and combine into one last name
            player_ln = ' '.join([str(elem) for elem in player_name.split()[1:]])
            player_age = get_player_age_from_playerlist(soup.select(f'#fantasy > tbody > tr:nth-child({i}) > td:nth-child(5)'))
            player = Player(fn=player_fn, ln=player_ln, age=player_age, url=player_link)
            print(f"Got playerdata for {player_name}")
            player.pid, full_scrape_enabled = get_pid(engine, player)
            player_json = player.get_sqs_json(str(full_scrape_enabled))
            print(f"creating sqs message for {player_json}")
            if not args.test_mode:
                create_sqs_message(sqs_client, player_json)
        i += 1
    publish_sns_message(sns_client=sns_client)
    engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-t", "--test_mode",
                        action="store_true",
                        help="enable test mode")
    args = parser.parse_args()
    main(args)