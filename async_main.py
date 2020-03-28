import argparse
import asyncio
import aiofiles
from aiohttp import ClientSession, ClientTimeout
import csv
import time
from async_classes import Player, Game
from async_scrape_stats import craft_url, scrape_playerdata, scrape_player
from async_writer import write_to_db


async def main(args):
    if args.test_mode:
        csv_path = args.csv_file
        players = []

        # Create list of players from input csv
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

        start_time = time.time()
        tasks = []
        for player in players:
            tasks.append(scrape_player(player, args.output_dir, test_mode=args.test_mode))
        await asyncio.gather(*tasks)
        end_time = time.time()
        print("Total scrape time: %f" % (end_time - start_time))

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
    asyncio.run(main(args))
