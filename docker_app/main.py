import argparse
import csv
import re


from docker_app.classes.Player import Player
from docker_app.scrape_stats import craft_url, scrape_playerdata, fix_team_abbrev
from docker_app.writer import write_to_db, write_single_csv_headers_fantasy, write_to_single_csv, \
    write_qb_gamestats_to_csv, write_flex_gamestats_to_csv, read_from_db
from docker_app.score_convert import calc_dynasty_scoring


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
                    players.append(Player(pid, fn, ln, pos, team, salary))

        for player in players:
            soup = craft_url(player, test_mode=True)
            scrape_playerdata(player, soup, test_mode=True)
            calc_dynasty_scoring(player)
            write_to_db(player)
            print("finit")


    if args.dynasty_mode:
        scrape_years = ['2015', '2016', '2017', '2018', '2019']
        positions = ['QB', 'RB', 'WR', 'TE']
        players = []

        udk_path = '/Users/dansher/fun_repos/fantasyland/UDK_2020'
        for pos in positions:
            csv_path = '%s/UDK_dynasty_%s.csv' % (udk_path, pos)

            with open(csv_path) as f:
                pid = 0
                reader = csv.reader(f)
                for row in reader:
                    # Skip header row
                    if 'Player' not in row[0]:
                        pid += 1
                        data = row[0].split(' ')
                        fn = data[0]
                        ln = data[1][:-1]  # Last name has trailing comma
                        team = fix_team_abbrev(data[2])
                        s = re.search(r'\((\d{2}\.\d{1,2})yo\)', data[3])
                        if s:
                            age = s.group(1)
                        else:
                            age = data[3]
                        players.append(Player(pid, fn, ln, pos, team, age))

        #[[write_csv_headers(args.output_dir, pos, year) for year in scrape_years] for pos in positions]

        csv_path = '%s/all_player_fantasy_stats.csv' % args.output_dir
        for position in positions:
            write_single_csv_headers_fantasy(csv_path)

        first_of_pos = True
        for i in range(0, len(players)):
            player = players[i]
            soup = craft_url(player, test_mode=True)
            if soup:
                scrape_playerdata(player, soup, test_mode=True)
                    #replace_empties(player)
                if len(player.years) > 0:
                    calc_dynasty_scoring(player)
                    write_to_single_csv(player, csv_path)
                    print('Number %d finished' % i)
            else:
                print('Could not get scrape data for %s %s' % (player.fn, player.ln))
        write_qb_gamestats_to_csv(players[:59], args.output_dir)
        write_flex_gamestats_to_csv(players[59:], args.output_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-i", "--in_dir",
                        type = str,
                        default='/Users/dansher/fun_repos/fantasyland/UDK_2020/',
                        help="path to csv file containing players")
    parser.add_argument("-c", "--csv_file",
                            type = str,
                            default='sample_one_player_sheet.csv',
                            help="path to csv file containing players")
    
    parser.add_argument("-o", "--output_dir",
                            type = str,
                            default="sample_dbs",
                            help="path to output directory containing stats files")
            
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
    args = parser.parse_args()
    main(args) 
