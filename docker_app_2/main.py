import argparse
import csv
import re
from datetime import date

from classes.Player import Player
from scrape_stats import craft_url, scrape_playerdata, fix_team_abbrev
from writer import write_to_db, write_single_csv_headers_fantasy, write_to_single_csv, \
    write_qb_gamestats_to_csv, write_flex_gamestats_to_csv, read_from_db, write_to_dynamodb, write_to_mysql
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
                players.append(Player(pid, fn, ln, pos, team))
    return players


def main(args):

    players = []
    if args.test_mode:
        players = read_fantasy_pros_rank_sheet(args.csv_file)

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
