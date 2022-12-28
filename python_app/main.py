import argparse
import csv
from ast import literal_eval
from datetime import date

import boto3

from python_app import config
from python_app.classes.Player import Player
from python_app.scrape_stats import craft_url, scrape_playerdata, fix_team_abbrev
from python_app.writer import write_to_db, write_single_csv_headers_fantasy, write_to_single_csv, \
    write_qb_gamestats_to_csv, write_flex_gamestats_to_csv, read_from_db, write_to_dynamodb, write_to_mysql
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


def get_players_from_sqs():
    sqs_client = boto3.resource("sqs")
    queue = sqs_client.get_queue_by_name(QueueName=config.sqs_queue_name)
    messages = queue.receive_messages(MaxNumberOfMessages=1)

    players = []
    for message in messages:
        player_dict = literal_eval(message.body)
        player = Player(pid=player_dict["pid"],
                        fn=player_dict["fn"],
                        ln=player_dict["ln"],
                        pos=player_dict["pos"],
                        curr_team=player_dict["curr_team"])
        players.append(player)
        message.delete()

    return players


def main(args):

    players = []
    if args.test_mode:
        players = read_fantasy_pros_rank_sheet(args.csv_file)
    else:
        players = get_players_from_sqs()

    # only scrape current year's data if not in full scrape mode
    years_to_scrape = None
    if not args.full_scrape_mode:
        today = date.today()
        # if september or later, get this years data. If January-August we want last years data
        if today.month > 9:
            years_to_scrape = [str(today.year)]
        else:
            years_to_scrape = [str(today.year - 1)]

    first_player = True
    for player in players:
        soup = craft_url(player, test_mode=True)
        scrape_playerdata(player, soup, test_mode=True, years_to_scrape=years_to_scrape)
        calc_dynasty_scoring(player)
        if first_player:
            write_to_mysql(player, args.init_db)
            first_player = False
        else:
            write_to_mysql(player, False)
        print("finit")





if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-i", "--in_dir",
                        type = str,
                        default='/Users/dansher/fun_repos/fantasyland/UDK_2020/',
                        help="path to csv file containing players")
    parser.add_argument("-c", "--csv_file",
                            type = str,
                            default='Sample_FantasyPros_2022_Ros_ALL_Rankings.csv',
                            help="path to csv file containing players")
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
