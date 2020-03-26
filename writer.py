from os import path
from classes import Player, PlayerSeason


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
    write_str += '{\"pid\": \"%s\", \"ln\": \"%s\", \"fn\": \"%s\", \"pos\": \"%s\", \"curr_team\": \"%s\",' \
                  % (player.pid, player.ln, player.fn, player.pos, player.curr_team)
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
    write_str += ']}'

    return write_str


def write_to_db(players, db):
    filepath = '%s/%s.json' % (db, 'test')
    player_str = ""
    with open(filepath, 'w') as f:
        for player in players:
            f.write(write_season_stats_to_json_str(player))


