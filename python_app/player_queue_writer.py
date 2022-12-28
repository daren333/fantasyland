import argparse
import csv
import uuid

import boto3
import sqlalchemy
from sqlalchemy import create_engine, select

from python_app import config
from python_app.scrape_stats import fix_team_abbrev
from python_app.classes.Player import Player


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


def get_pid(player):
    engine = create_engine(
        "mysql+pymysql://" + config.mysql_user + ":" + config.mysql_pw + "@" + config.mysql_host + "/" + config.mysql_db)
    connection = engine.connect()
    player_info = sqlalchemy.Table('player_info', sqlalchemy.MetaData(), autoload=True, autoload_with=engine)

    query = select([player_info.columns.pid])\
        .where(player_info.columns.fn == player.fn and
               player_info.columns.ln == player.ln and
               player_info.columns.pos == player.pos and
               player_info.columns.team == player.curr_team)
    query_result = connection.execute(query).fetchall()

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
    sqs_client = boto3.resource("sqs")
    if args.test_mode:
        players = read_fantasy_pros_rank_sheet(args.input_file)
    else:
        s3_client = boto3.resource("s3")
        obj = s3_client.get_object(bucket=config.s3_bucket, key=config.s3_key)
        players = read_fantasy_pros_rank_sheet(obj)
    for player in players:
        player.pid = get_pid(player)
        player_json = player.get_sqs_json()
        create_sqs_message(sqs_client, player_json)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-i", "--input_file",
                        type = str,
                        default='/Users/dansher/fun_repos/fantasyland/python_app/FantasyPros_2022_Ros_ALL_Rankings.csv',
                        help="path to csv file containing players")
    parser.add_argument("-t", "--test_mode",
                        action="store_true",
                        help="enable test mode")
    args = parser.parse_args()
    main(args)