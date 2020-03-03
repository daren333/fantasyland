import argparse
import csv
from classes import Player, Game
from scrape_stats import craft_url, walk_homepage

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
                    players.append(Player(pid, fn, ln, pos, salary, team, injury_status))

        #for player in players:
        player = players[3]
        soup = craft_url(player)
        print(player.ln)
        print(player.url)
        walk_homepage(player, soup)
        


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-c", "--csv_file", 
                            type = str,
                            default='sample_fanduel_sheet.csv',
                            help="path to csv file containing players")
            
    parser.add_argument("-t", "--test_mode", 
                            action="store_true", 
                            help="enable test mode")
    args = parser.parse_args()
    main(args) 
    
