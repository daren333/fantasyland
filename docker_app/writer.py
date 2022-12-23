from marshmallow import pprint

from pymongo import MongoClient

from classes.Player import PlayerSchema


def write_gamelogs(stat_val):
    gamelog_str = ""
    for week, v in stat_val.items():
        gamelog_str += '\"%s\": {' % week
        for header, stat in v.items():
            gamelog_str += '\"%s\": \"%s\",' % (header, stat)
        # Remove trailing comma from stats
        gamelog_str = gamelog_str[:-1]
        # Close week
        gamelog_str += '},'
        # Remove trailing comma from weeks
    gamelog_str = gamelog_str[:-1]
    gamelog_str += '},'

    return gamelog_str


def write_fantasy(stat_val):
    fantasy_str = ""
    for week, v in stat_val.items():
        fantasy_str += '\"%s\": {' % week
        for header, stat in v.items():
            fantasy_str += '\"%s\": \"%s\",' % (header, stat)
        # Remove trailing comma from stats
        fantasy_str = fantasy_str[:-1]
        # Close week
        fantasy_str += '},'
        # Remove trailing comma from weeks
    fantasy_str = fantasy_str[:-1]
    fantasy_str += '},'

    return fantasy_str


def write_splits(stat_val):
    splits_str = ""
    for week, v in stat_val.items():
        splits_str += '\"%s\": {' % week
        for split_type, splits in v.items():
            splits_str += '\"%s\": {' % split_type
            for header, stat in splits.items():
                splits_str += '\"%s\": \"%s\",' % (header, stat)
            # Remove trailing comma from split type
            splits_str = splits_str[:-1]
            splits_str += '},'
        # Remove trailing comma from stats
        splits_str = splits_str[:-1]
        # Close week
        splits_str += '},'
    # Remove trailing comma from weeks
    splits_str = splits_str[:-1]
    splits_str += '},'

    return splits_str


def write_season_stats_to_json_str(player):
    """
    Takes in PlayerSeason and returns a string in JSON format to write to file.
    Main purpose is to deal with the fact that JSON won't allow trailing commas.
    :param player: Player whose stats to write
    :return: String to write to file
    """
    write_str = ""
    write_str += '\"%s\" : {\"pid\": \"%s\", \"ln\": \"%s\", \"fn\": \"%s\", \"pos\": \"%s\", \"curr_team\": \"%s\",' \
                  % (player.pid, player.pid, player.ln, player.fn, player.pos, player.curr_team)
    write_str += '\"seasons\": ['
    for year in player.years:
        season = player.get_year(year.year)
        write_str += '{ \"year:\": \"%s\",\"teams\": [' % season.year
        # Write teams list
        for team in season.teams:
            write_str += '\"%s\",' % team
        # Get rid of trailing comma
        write_str = write_str[:-1]
        write_str += '], \"stats\": {'

        # Write stats
        for stat_type, stat_val in season.stats.items():
            write_str += '\"%s\": {' % stat_type
            if stat_type == 'gamelogs':
                write_str += write_gamelogs(stat_val)
            elif stat_type == 'fantasy':
                write_str += write_fantasy(stat_val)
            else:
                write_str += write_splits(stat_val)
        # Remove trailing comma from stat_type
        write_str = write_str[:-1]
        write_str += '}},'
    # Remove trailing comma from seasons
    write_str = write_str[:-1]
    write_str += ']},'

    return write_str


def write_to_db(player):
    #filepath = '%s/%s.json' % (db, 'test')

    # with open(filepath, 'w') as f:
    #     f.write('{')
    #     # Write all but last player with trailing commas
    #     for player in players[:-1]:
    #         f.write(write_season_stats_to_json_str(player))
    #     # Write last player without trailing comma
    #     f.write(write_season_stats_to_json_str(players[-1]) + '}')

    client = MongoClient("mongodb://root:example@localhost:27017/")
    #client = MongoClient("mongodb://root:example@mongodb:27017/")
    db = client["nfl"]
    players_db = db["players"]
    #for player in players:
    serialized_player = PlayerSchema().dump(player)
    players_db.update_one({'_id': player.pid}, {"$set": serialized_player}, upsert=True)


def read_from_db(pid):
    client = MongoClient("mongodb://root:example@mongodb:27017/")

    db = client["nfl"]
    players_db = db["players"]
    player_json = players_db.find_one({"pid": pid})
    deserialized_player = PlayerSchema().load(player_json)
    pprint(deserialized_player)



def write_single_csv_headers_fantasy(csv_path):
    with open(csv_path, 'w') as f:
        f.write('Last, First, Position, Year, Team, Year Total, ')
        [f.write('Week %d, ' % week) for week in range(1, 17)]
        f.write('\n')


def write_to_single_csv(player, csv_path):
    with open(csv_path, 'a') as f:
        for year in player.years:
            curr_year = year.year
            f.write('%s, %s, %s, %s, %s, %.2f, ' % (player.ln, player.fn, player.pos, curr_year, player.curr_team, player.fantasy[curr_year]['year_total']))
            for i in range(1, 17):
                if str(i) in player.fantasy[curr_year]['weekly'].keys():
                    week_stat = player.fantasy[curr_year]['weekly'][str(i)]
                    f.write(' %.2f,' % week_stat)
                else:
                    f.write(' 0.0,')

            #for week_stat in player.fantasy[curr_year]['weekly'].values():
            #    f.write(' %.2f,' % week_stat)
            f.write('\n')


def write_csv_headers(output_dir, pos, year):
    filepath = '%s/%s_%s_test.csv' % (output_dir, pos, year)
    with open(filepath, 'w') as f:
        f.write('Last, First, Year, Team, Year Total, ')
        [f.write('%s, ' % week) for week in range(1, 17)]
        f.write('\n')


def write_to_csv(players, csv):
    for player in players:
        for year in player.years:
            curr_year = year.year
            filepath = '%s/%s_%s_test.csv' % (csv, curr_year, player.pos)
            with open(filepath, 'a') as f:
                f.write('%s, %s, %s, %.2f,' % (player.ln, player.fn, player.curr_team, player.fantasy[curr_year]['year_total']))
                #for i in range(len(player.fantasy[curr_year]['weekly'])):
                    #week_stat = player.fantasy[curr_year]['weekly'].values()
                    #if not player.fantasy[curr_year][i]:
                    #    f.write('0.0')
                for week_stat in player.fantasy[curr_year]['weekly'].values():
                    f.write(' %.2f,' % week_stat)
                f.write('\n')


def write_csv_gamestat_headers(output_dir, player):
    filepath = '%s%s_gamelog_test.csv' % (output_dir, player.pos)
    with open(filepath, 'w') as f:
        f.write('Last, First, Year, Team, ')
        week = next(iter(player.years[0].stats['gamelogs'].keys()))
            #[f.write('%s, ' % stat) for stat in player.years[0].stats['gamelogs'].keys()]
            #[f.write('%s, ' % stat) for stat in player.years[0].stats['fantasy'].keys()]
        [f.write('%s, ' % stat) for stat in player.years[0].stats['gamelogs'][week].keys()]
        [f.write('%s, ' % stat) for stat in player.years[0].stats['fantasy'][week].keys()]
        f.write('\n')


def write_gamestats_to_csv(players, csv):
    for player in players:
        for year in player.years:
            curr_year = year.year
            filepath = '%s%s_gamelog_test.csv' % (csv, player.pos)
            with open(filepath, 'a') as f:
                for week in year.stats['gamelogs'].keys():
                    f.write('%s, %s, %s, %s, ' % (player.ln, player.fn, curr_year, player.curr_team))
                    f.write('Week %s, ' % week)
                    [f.write('%s, ' % stat) for stat in year.stats['gamelogs'][week].values()]
                    [f.write('%s, ' % stat) for stat in year.stats['fantasy'][week].values()]
                    f.write('\n')


def write_qb_gamestats_to_csv(players, csv):
    filepath = '%s/QB_gamelog.csv' % csv
    with open(filepath, 'w') as f:
        f.write('Last, First, Year, Team, Week, Age, Pass Completions, Pass Attempts, Pass Yards, Pass TD, Int, Rush Attempts, Rush Yards, Rush TD, Fumbles, Fumbles Lost, Offensive Snaps, Offsensive Snap Percent,\n')
        for player in players:
            for year in player.years:
                curr_year = year.year
                for week in year.stats['gamelogs'].keys():
                    try:
                        stat_dict = year.stats['gamelogs'][week]
                        f.write('%s, %s, %s, %s, %s, %.2f, ' % (player.ln, player.fn, curr_year, stat_dict['team'], stat_dict['week_num'], float(stat_dict['age'])))
                        if 'pass_att' in stat_dict:
                            f.write('%s, %s, %s, %s, %s, ' % (stat_dict['pass_cmp'], stat_dict['pass_att'], stat_dict['pass_yds'], stat_dict['pass_td'], stat_dict['pass_int']))
                        else:
                            f.write('0, 0, 0, 0, 0, ')
                        if 'rush_att' in stat_dict:
                            f.write('%s, %s, %s, ' % (stat_dict['rush_att'], stat_dict['rush_yds'], stat_dict['rush_td']))
                        else:
                            f.write('0, 0, 0, ')
                        if 'fumbles' in stat_dict:
                            f.write('%s, ' % stat_dict['fumbles'])
                        else:
                            f.write('0, ')
                        if 'fumbles_lost' in stat_dict:
                            f.write('%s, ' % stat_dict['fumbles_lost'])
                        else:
                            f.write('0, ')
                        if 'offense' in stat_dict:
                            f.write('%s, ' % stat_dict['offense'])
                        else:
                            f.write('0, ')
                        if 'off_pct' in stat_dict:
                            f.write('%s, \n' % stat_dict['off_pct'])
                        else:
                            f.write('0, \n')
                    except:
                        print('Could not print week %s for %s %s' % (week, player.fn, player.ln))


def write_flex_gamestats_to_csv(players, csv):
    filepath = '%s/flex_gamelog.csv' % csv
    with open(filepath, 'w') as f:
        f.write('Last, First, Year, Team, Week, Age, Rush Attempts, Rush Yards, Rush TD, Targets, Receptions, Receiving Yards, Receiving TD, Fumbles, Fumbles Lost, Offensive Snaps, Offsensive Snap Percent,\n')
        for player in players:
            for year in player.years:
                curr_year = year.year
                for week in year.stats['gamelogs'].keys():
                    try:
                        stat_dict = year.stats['gamelogs'][week]
                        f.write('%s, %s, %s, %s, %s, %.2f, ' % (player.ln, player.fn, curr_year, stat_dict['team'], stat_dict['week_num'], float(stat_dict['age'])))
                        if 'rush_att' in stat_dict:
                            f.write('%s, %s, %s, ' % (stat_dict['rush_att'], stat_dict['rush_yds'], stat_dict['rush_td']))
                        else:
                            f.write('0, 0, 0, ')
                        if 'rec' in stat_dict:
                            f.write('%s, %s, %s, %s, ' % (stat_dict['targets'], stat_dict['rec'], stat_dict['rec_yds'], stat_dict['rec_td']))
                        if 'fumbles' in stat_dict:
                            f.write('%s, ' % stat_dict['fumbles'])
                        else:
                            f.write('0, ')
                        if 'fumbles_lost' in stat_dict:
                            f.write('%s, ' % stat_dict['fumbles_lost'])
                        else:
                            f.write('0, ')
                        if 'offense' in stat_dict:
                            f.write('%s, ' % stat_dict['offense'])
                        else:
                            f.write('0, ')
                        if 'off_pct' in stat_dict:
                            f.write('%s, \n' % stat_dict['off_pct'])
                        else:
                            f.write('0, \n')
                    except:
                        print('Could not print week %s for %s %s' % (week, player.fn, player.ln))
