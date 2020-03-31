import argparse
import csv
import requests
from classes import Player, Game
from scrape_stats import craft_url, scrape_playerdata
from writer import write_to_db


def main(args):
    if args.test_mode:
        csv_path = args.csv_file
        players = []

        with open(csv_path) as csv_file:
            reader = csv.reader(csv_file)
            for row in reader:
                # Skip header row
                if row[0] != 'Id':
                    pid = row[0]
                    pos = row[1]
                    fn = row[2]
                    ln = row[4]
                    salary = row[6]
                    team = row[9]
                    injury_status = row[11]
                    players.append(Player(pid, fn, ln, pos, salary, team))

        for player in players:
            soup = craft_url(player, test_mode=True)
            scrape_playerdata(player, soup, test_mode=True)
            write_to_db(players, args.output_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-c", "--csv_file",
                            type = str,
                            default='sample_fanduel_sheet.csv',
                            help="path to csv file containing players")
    
    parser.add_argument("-o", "--output_dir",
                            type = str,
                            default="sample_dbs",
                            help="path to output directory containing stats files")
            
    parser.add_argument("-t", "--test_mode", 
                            action="store_true", 
                            help="enable test mode")
    args = parser.parse_args()
    main(args) 
