import argparse
import csv
from ast import literal_eval
from datetime import date

import boto3
from distutils.util import strtobool

import config
from classes.Player import Player
from scrape_stats import craft_url, scrape_playerdata, fix_team_abbrev
from writer import write_to_mysql
from score_convert import calc_dynasty_scoring


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
    players_to_scrape = {}
    with open(sample_path, "r") as file:
        message_str = file.read()
        player_dict = literal_eval(message_str)
        player = Player(pid=player_dict["pid"],
                        fn=player_dict["fn"],
                        ln=player_dict["ln"],
                        age=player_dict["age"],
                        url=player_dict["url"])
        full_scrape_enabled = player_dict["full_scrape_enabled"]
        players_to_scrape[player.pid] = {
            "player_obj": player,
            "full_scrape": bool(strtobool(full_scrape_enabled))
        }

    return players_to_scrape


def get_players_from_sqs():
    sqs_client = boto3.resource("sqs")
    queue = sqs_client.get_queue_by_name(QueueName=config.sqs_queue_name)
    messages = queue.receive_messages(MaxNumberOfMessages=5)

    players_to_scrape = {}
    for message in messages:
        player_dict = literal_eval(message.body)
        player = Player(pid=player_dict["pid"],
                        fn=player_dict["fn"],
                        ln=player_dict["ln"],
                        age=player_dict["age"],
                        url=player_dict["url"])
        full_scrape_enabled = player_dict["full_scrape_enabled"]
        players_to_scrape[player.pid] = {
            "player_obj": player,
            "message": message,
            "full_scrape": bool(strtobool(full_scrape_enabled))
        }

    return players_to_scrape


def get_current_season():
    today = date.today()
    # if september or later, get this years data. If January-August we want last years data
    if today.month > 9:
        return str(today.year)
    else:
        return str(today.year - 1)


def main(args):

    if args.test_mode:
        players = get_test_message_from_sqs_sample(args.sample_sqs_message)
    else:
        players = get_players_from_sqs()

    while len(players) > 0:
        for pid in players:
            player = players[pid]["player_obj"]
            years_to_scrape = [get_current_season()] if not players[pid]["full_scrape"] else None
            scrape_playerdata(player, test_mode=True, years_to_scrape=years_to_scrape)
            calc_dynasty_scoring(player)
            write_to_mysql(player)
            print(f"wrote {player.fn} {player.ln} to mysql db")

            if not args.test_mode:
                message = players[pid]["message"]
                try:
                    message.delete()
                    print(f"Deleted SQS Message for player {player.fn} {player.ln}")
                except Exception as e:
                    print(f"Could not delete SQS Message for player {player.fn} {player.ln}. Error is: {e}")
            else:  # if test mode exit after the first entry read
                return 0

        players = get_players_from_sqs()  # if not test mode refill players from queue
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-sqs", "--sample_sqs_message",
                            type = str,
                            default='sample_sqs_message_body.txt',
                            help="path to sqs sample message")
    parser.add_argument("-t", "--test_mode", 
                            action="store_true", 
                            help="enable test mode")
    parser.add_argument("-l", "--local_mode",
                        action="store_true",
                        help="enable local mode")
    parser.add_argument("-db", "--database",
                        type=str,
                        default="mysql",
                        help="which db to use - options: mysql, mongodb, postgres. Defaults to mysql")
    args = parser.parse_args()
    main(args) 
