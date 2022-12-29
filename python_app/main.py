import argparse
import csv
from ast import literal_eval
from datetime import date

import boto3

from python_app import config
from python_app.classes.Player import Player
from python_app.scrape_stats import craft_url, scrape_playerdata, fix_team_abbrev
from python_app.writer import write_to_mysql
from python_app.score_convert import calc_dynasty_scoring


def read_fantasy_pros_rank_sheet(csv_path):
    players = []
    with open(csv_path) as csv_file:
        reader = csv.reader(csv_file)
        for row in reader:
            # Skip header row
            if row[0] != 'RK':
                pid = row[0]
                fn = row[1].split()[0]
                ln = row[1].split()[1]
                team = fix_team_abbrev(row[2])
                pos = row[3][:2]
                players.append(Player(fn, ln, pos, team))
    return players


def get_test_message_from_sqs_sample(sample_path):
    players = []
    with open(sample_path, "r") as file:
        message_str = file.read()
        player_dict = literal_eval(message_str)
        player = Player(pid=player_dict["pid"],
                        fn=player_dict["fn"],
                        ln=player_dict["ln"],
                        age=player_dict["age"],
                        url=player_dict["url"])
        players.append(player)
    return players


def get_players_from_sqs():
    sqs_client = boto3.resource("sqs")
    queue = sqs_client.get_queue_by_name(QueueName=config.sqs_queue_name)
    messages = queue.receive_messages(MaxNumberOfMessages=1)

    players = []
    player_messages = {}
    for message in messages:
        player_dict = literal_eval(message.body)
        player = Player(pid=player_dict["pid"],
                        fn=player_dict["fn"],
                        ln=player_dict["ln"],
                        age=player_dict["age"],
                        url=player_dict["url"])
        players.append(player)
        player_messages[player.url] = message

    return players, player_messages


def main(args):

    players = []
    sqs_messages = {}
    if args.test_mode:
        players = get_test_message_from_sqs_sample(args.sample_sqs_message)
    else:
        players, sqs_messages = get_players_from_sqs()

    # only scrape current year's data if not in full scrape mode
    years_to_scrape = None
    if not args.full_scrape_mode:
        today = date.today()
        # if september or later, get this years data. If January-August we want last years data
        if today.month > 9:
            years_to_scrape = [str(today.year)]
        else:
            years_to_scrape = [str(today.year - 1)]

    for player in players:
        scrape_playerdata(player, test_mode=True, years_to_scrape=years_to_scrape)
        calc_dynasty_scoring(player)
        write_to_mysql(player)
        message = sqs_messages.get(player.url)
        if not args.test_mode:
            try:
                message.delete()
                print(f"Deleted SQS Message for player {player.fn} {player.ln}")
            except Exception as e:
                print(f"Could not delete SQS Message for player {player.fn} {player.ln}. Error is: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-i", "--in_dir",
                        type = str,
                        default='/Users/dansher/fun_repos/fantasyland/UDK_2020/',
                        help="path to csv file containing players")
    parser.add_argument("-sqs", "--sample_sqs_message",
                            type = str,
                            default='sample_sqs_message_body.txt',
                            help="path to sqs sample message")
    parser.add_argument("-t", "--test_mode", 
                            action="store_true", 
                            help="enable test mode")
    parser.add_argument("-d", "--dynasty_mode",
                        action="store_true",
                        help="enable test mode")
    parser.add_argument("-db", "--database",
                        type=str,
                        default="mysql",
                        help="which db to use - options: mysql, mongodb, postgres. Defaults to mysql")
    parser.add_argument("-fs", "--full_scrape_mode",
                        action="store_true",
                        help="enable full scrape mode - gets all data from all years for that player (default is to only get the current year)")
    parser.add_argument("-init_db", "--init_db",
                        action="store_true",
                        help="create all the initial tables for the DB before writing stats (only use this option if starting from a blank mysql instance")
    args = parser.parse_args()
    main(args) 
