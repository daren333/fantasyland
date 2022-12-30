import boto3
import pandas as pd
import sqlalchemy
from marshmallow import pprint
import mysql.connector

from mysql.connector import errorcode

from pymongo import MongoClient
from sqlalchemy import create_engine

import config


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


def connect_to_db():
    try:
        cnx = mysql.connector.connect(user=config.mysql_user,
                                      password=config.mysql_pw,
                                      host=config.mysql_host,
                                      port=config.mysql_port)
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
    else:
        return cnx


def init_mysql_db(engine):
    create_database(engine, "nfl")
    create_sql_tables(engine)


def create_database(engine, db_name):
    connection = engine.connect()
    try:
        connection.execute(
            "CREATE DATABASE IF NOT EXISTS {} DEFAULT CHARACTER SET 'utf8'".format(db_name))
    except mysql.connector.Error as err:
        print("Failed creating database: {}".format(err))
        exit(1)

    try:
        connection.execute("USE {}".format(db_name))
    except mysql.connector.Error as err:
        print("Database {} does not exists.".format(db_name))
        if err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database {} created successfully.".format(db_name))
            connection.database = db_name
        else:
            print(err)
            exit(1)


def add_player_info_cols(player, df, season):
    df.insert(0, "pid", player.pid)
    df.insert(1, "fn", player.fn)
    df.insert(2, "ln", player.ln)
    df.insert(3, "season", season)
    return df


def get_player_dfs(player):
    player_dfs = {year: {} for year in player.years}
    for year in player.years:
        player_dfs[year]['gamelog_table'] = add_player_info_cols(player,
                                                                 pd.DataFrame.from_dict(player.years[year]["gamelogs"]).transpose(), year)
        player_dfs[year]['fantasy_table'] = add_player_info_cols(player,
                                                                 pd.DataFrame.from_dict(player.years[year]["fantasy"]).transpose(), year)
        player_dfs[year]['dynasty_scoring_table'] = add_player_info_cols(player, pd.DataFrame.from_dict(
            [player.dynasty_scoring[year]]).transpose(), year)
        player_dfs[year]['adv_rush_rec_table'] = add_player_info_cols(player, pd.DataFrame.from_dict(
            player.years[year]["adv_gamelogs"]["rush_rec_stats"]).transpose(), year)
        if player.pos == "QB":
            player_dfs[year]['adv_pass_table'] = add_player_info_cols(player, pd.DataFrame.from_dict(
                player.years[year]["adv_gamelogs"]["passing_stats"]).transpose(), year)
        player_dfs[year]['splits_place_table'] = add_player_info_cols(player, pd.DataFrame.from_dict(
            player.years[year]["splits"]["Place"]).transpose(), year)
        player_dfs[year]['splits_result_table'] = add_player_info_cols(player, pd.DataFrame.from_dict(
            player.years[year]["splits"]["Result"]).transpose(), year)
        player_dfs[year]['splits_final_margin_table'] = add_player_info_cols(player, pd.DataFrame.from_dict(
            player.years[year]["splits"]["Final Margin"]).transpose(), year)
        player_dfs[year]['splits_month_table'] = add_player_info_cols(player, pd.DataFrame.from_dict(
            player.years[year]["splits"]["Month"]).transpose(), year)
        player_dfs[year]['splits_game_number_table'] = add_player_info_cols(player, pd.DataFrame.from_dict(
            player.years[year]["splits"]["Game Number"]).transpose(), year)
        player_dfs[year]['splits_day_table'] = add_player_info_cols(player, pd.DataFrame.from_dict(
            player.years[year]["splits"]["Day"]).transpose(), year)
        player_dfs[year]['splits_time_table'] = add_player_info_cols(player, pd.DataFrame.from_dict(
            player.years[year]["splits"]["Time"]).transpose(), year)
        player_dfs[year]['splits_conference_table'] = add_player_info_cols(player, pd.DataFrame.from_dict(
            player.years[year]["splits"]["Conference"]).transpose(), year)
        player_dfs[year]['splits_division_table'] = add_player_info_cols(player, pd.DataFrame.from_dict(
            player.years[year]["splits"]["Division"]).transpose(), year)
        player_dfs[year]['splits_opponent_table'] = add_player_info_cols(player, pd.DataFrame.from_dict(
            player.years[year]["splits"]["Opponent"]).transpose(), year)
        player_dfs[year]['splits_stadium_table'] = add_player_info_cols(player, pd.DataFrame.from_dict(
            player.years[year]["splits"]["Stadium"]).transpose(), year)
        player_dfs[year]['splits_down_table'] = add_player_info_cols(player, pd.DataFrame.from_dict(
            player.years[year]["splits"]["Down"]).transpose(), year)
        player_dfs[year]['splits_yards_to_go_table'] = add_player_info_cols(player, pd.DataFrame.from_dict(
            player.years[year]["splits"]["Yards To Go"]).transpose(), year)
        player_dfs[year]['splits_down_and_yards_to_go_table'] = add_player_info_cols(player, pd.DataFrame.from_dict(
            player.years[year]["splits"]["Down & Yards to Go"]).transpose(), year)
        player_dfs[year]['splits_field_position_table'] = add_player_info_cols(player, pd.DataFrame.from_dict(
            player.years[year]["splits"]["Field Position"]).transpose(), year)
        player_dfs[year]['splits_score_differential_table'] = add_player_info_cols(player, pd.DataFrame.from_dict(
            player.years[year]["splits"]["Score Differential"]).transpose(), year)
        player_dfs[year]['splits_quarter_table'] = add_player_info_cols(player, pd.DataFrame.from_dict(
            player.years[year]["splits"]["Quarter"]).transpose(), year)
        player_dfs[year]['splits_game_situation_table'] = add_player_info_cols(player, pd.DataFrame.from_dict(
            player.years[year]["splits"]["Game Situation"]).transpose(), year)
        player_dfs[year]['splits_snap_type_and_huddle_table'] = add_player_info_cols(player, pd.DataFrame.from_dict(
            player.years[year]["splits"]["Snap Type & Huddle"]).transpose(), year)
        player_dfs[year]['splits_play_action_table'] = add_player_info_cols(player, pd.DataFrame.from_dict(
            player.years[year]["splits"]["Play Action"]).transpose(), year)
        player_dfs[year]['splits_rpo_table'] = add_player_info_cols(player, pd.DataFrame.from_dict(
            player.years[year]["splits"]["Run/Pass Option"]).transpose(), year)
    return player_dfs


def create_sql_tables(engine):
    cursor = engine.connect()
    cursor.execute("USE %s" % config.mysql_db)

    for table in config.sql_table_configs.keys():
        try:
            print("Creating table {}: ".format(table), end='')
            cursor.execute(config.sql_table_configs[table])
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                print("already exists.")
            else:
                print(err.msg)
        else:
            print("Created Table: %s" % table)


def write_to_mysql(player):
    engine = create_engine(
        "mysql+pymysql://" + config.mysql_user + ":" + config.mysql_pw + "@" + config.mysql_host + "/" + config.mysql_db)
    player_dfs = get_player_dfs(player)

    write_to_mysqldb(engine, player, player_dfs)
    print(f"wrote to DB for Player {player.fn} {player.ln}")


def create_player_info_df(player):
    player_info_dict = {
        "pid": player.pid,
        "fn": player.fn,
        "ln": player.ln,
        "pos": player.pos,
        "team": player.curr_team,
        "age": player.age,
        "url": player.url
    }

    return pd.DataFrame(player_info_dict, columns=[key for key in player_info_dict.keys()], index=[0])


# Needed to delete existing tables until Pandas decides to add upsert to to_sql function
def delete_player_info_row(engine, player, table_name):
    connection = engine.connect()

    info_table = sqlalchemy.Table(table_name, sqlalchemy.MetaData(), autoload=True, autoload_with=engine)
    delete_op = info_table.delete().where(info_table.columns.pid == player.pid).where(info_table.columns.url == player.url)
    connection.execute(delete_op)

    connection.close()


# Needed to delete existing tables until Pandas decides to add upsert to to_sql function
def delete_player_stats_row(engine, player, season, table_name):
    connection = engine.connect()

    stats_table = sqlalchemy.Table(table_name, sqlalchemy.MetaData(), autoload=True, autoload_with=engine)

    delete_op = stats_table.delete().where(stats_table.columns.season == season).where(stats_table.columns.pid == player.pid)
    connection.execute(delete_op)

    connection.close()


def delete_row_if_present(engine, player, table_name, player_info, season=None):
    delete_player_info_row(engine, player, table_name) if player_info else \
        delete_player_stats_row(engine, player, season, table_name)


def write_to_mysqldb(engine, player, player_dfs):
    cursor = engine.connect()
    cursor.execute("USE %s" % config.mysql_db)
    player_info_df = create_player_info_df(player)

    # Needed until Pandas decides to add upsert to to_sql function
    delete_row_if_present(engine=engine, player=player, table_name="player_info_table", player_info=True)
    player_info_df.to_sql("player_info_table", con=cursor, if_exists='append', index=False)

    for year in player_dfs:
        for df_name in player_dfs[year]:
            df = player_dfs[year][df_name]
            # Needed until Pandas decides to add upsert to to_sql function
            delete_row_if_present(engine=engine, player=player, season=year, table_name=df_name, player_info=False)
            df.to_sql(df_name, con=cursor, if_exists='append', index=False)


# def write_to_dynamodb(player):
#     # boto3.setup_default_session()
#     # client = boto3.resource("dynamodb").Table("fantatsyland")
#     # serialized_player = PlayerSchema().dump(player)
#     # client.put_item(Item=serialized_player)
#
#     table_name = "fantasyland"
#     dynamodb_resource = boto3.resource("dynamodb")
#     table = dynamodb_resource.Table(table_name)
#     serialized_player = PlayerSchema().dump(player)
#     response = table.put_item(Item=serialized_player)
#     print(response)
#

# def write_to_db(player):
#     # filepath = '%s/%s.json' % (db, 'test')
#
#     # with open(filepath, 'w') as f:
#     #     f.write('{')
#     #     # Write all but last player with trailing commas
#     #     for player in players[:-1]:
#     #         f.write(write_season_stats_to_json_str(player))
#     #     # Write last player without trailing comma
#     #     f.write(write_season_stats_to_json_str(players[-1]) + '}')
#
#     # client = MongoClient("mongodb://root:example@localhost:27017/")
#     client = MongoClient("mongodb://root:example@localhost:27017/")
#     db = client["nfl"]
#     players_db = db["players"]
#     # for player in players:
#     serialized_player = PlayerSchema().dump(player)
#     players_db.update_one({'_id': player.pid}, {"$set": serialized_player}, upsert=True)


# def read_from_db(pid):
#     client = MongoClient("mongodb://root:example@localhost:27017/")
#
#     db = client["nfl"]
#     players_db = db["players"]
#     player_json = players_db.find_one({"pid": pid})
#     deserialized_player = PlayerSchema().load(player_json)
#     pprint(deserialized_player)


def write_single_csv_headers_fantasy(csv_path):
    with open(csv_path, 'w') as f:
        f.write('Last, First, Position, Year, Team, Year Total, ')
        [f.write('Week %d, ' % week) for week in range(1, 17)]
        f.write('\n')


def write_to_single_csv(player, csv_path):
    with open(csv_path, 'a') as f:
        for year in player.years:
            curr_year = year.year
            f.write('%s, %s, %s, %s, %s, %.2f, ' % (
            player.ln, player.fn, player.pos, curr_year, player.curr_team, player.fantasy[curr_year]['year_total']))
            for i in range(1, 17):
                if str(i) in player.fantasy[curr_year]['weekly'].keys():
                    week_stat = player.fantasy[curr_year]['weekly'][str(i)]
                    f.write(' %.2f,' % week_stat)
                else:
                    f.write(' 0.0,')

            # for week_stat in player.fantasy[curr_year]['weekly'].values():
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
                f.write('%s, %s, %s, %.2f,' % (
                player.ln, player.fn, player.curr_team, player.fantasy[curr_year]['year_total']))
                # for i in range(len(player.fantasy[curr_year]['weekly'])):
                # week_stat = player.fantasy[curr_year]['weekly'].values()
                # if not player.fantasy[curr_year][i]:
                #    f.write('0.0')
                for week_stat in player.fantasy[curr_year]['weekly'].values():
                    f.write(' %.2f,' % week_stat)
                f.write('\n')


def write_csv_gamestat_headers(output_dir, player):
    filepath = '%s%s_gamelog_test.csv' % (output_dir, player.pos)
    with open(filepath, 'w') as f:
        f.write('Last, First, Year, Team, ')
        week = next(iter(player.years[0].stats['gamelogs'].keys()))
        # [f.write('%s, ' % stat) for stat in player.years[0].stats['gamelogs'].keys()]
        # [f.write('%s, ' % stat) for stat in player.years[0].stats['fantasy'].keys()]
        [f.write('%s, ' % stat) for stat in player.years[0].stats['gamelogs'][week].keys()]
        [f.write('%s, ' % stat) for stat in player.years[0].stats['fantasy'][week].keys()]
        f.write('\n')


def write_gamestats_to_csv(players, csv):
    for player in players:
        for year in player.years:
            curr_year = year.year
            filepath = '%s%s_gamelog_test.csv' % (csv, player.pos)
            with open(filepath, 'a') as f:
                for week in player.years[year]['gamelogs'].keys():
                    f.write('%s, %s, %s, %s, ' % (player.ln, player.fn, curr_year, player.curr_team))
                    f.write('Week %s, ' % week)
                    [f.write('%s, ' % stat) for stat in player.years[year]['gamelogs'][week].values()]
                    [f.write('%s, ' % stat) for stat in player.years[year]['fantasy'][week].values()]
                    f.write('\n')


def write_qb_gamestats_to_csv(players, csv):
    filepath = '%s/QB_gamelog.csv' % csv
    with open(filepath, 'w') as f:
        f.write(
            'Last, First, Year, Team, Week, Age, Pass Completions, Pass Attempts, Pass Yards, Pass TD, Int, Rush Attempts, Rush Yards, Rush TD, Fumbles, Fumbles Lost, Offensive Snaps, Offsensive Snap Percent,\n')
        for player in players:
            for year in player.years:
                curr_year = year.year
                for week in player.years[year]['gamelogs'].keys():
                    try:
                        stat_dict = player.years[year]['gamelogs'][week]
                        f.write('%s, %s, %s, %s, %s, %.2f, ' % (
                        player.ln, player.fn, curr_year, stat_dict['team'], stat_dict['week_num'],
                        float(stat_dict['age'])))
                        if 'pass_att' in stat_dict:
                            f.write('%s, %s, %s, %s, %s, ' % (
                            stat_dict['pass_cmp'], stat_dict['pass_att'], stat_dict['pass_yds'], stat_dict['pass_td'],
                            stat_dict['pass_int']))
                        else:
                            f.write('0, 0, 0, 0, 0, ')
                        if 'rush_att' in stat_dict:
                            f.write(
                                '%s, %s, %s, ' % (stat_dict['rush_att'], stat_dict['rush_yds'], stat_dict['rush_td']))
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
        f.write(
            'Last, First, Year, Team, Week, Age, Rush Attempts, Rush Yards, Rush TD, Targets, Receptions, Receiving Yards, Receiving TD, Fumbles, Fumbles Lost, Offensive Snaps, Offsensive Snap Percent,\n')
        for player in players:
            for year in player.years:
                curr_year = year.year
                for week in player.years[year]['gamelogs'].keys():
                    try:
                        stat_dict = player.years[year]['gamelogs'][week]
                        f.write('%s, %s, %s, %s, %s, %.2f, ' % (
                        player.ln, player.fn, curr_year, stat_dict['team'], stat_dict['week_num'],
                        float(stat_dict['age'])))
                        if 'rush_att' in stat_dict:
                            f.write(
                                '%s, %s, %s, ' % (stat_dict['rush_att'], stat_dict['rush_yds'], stat_dict['rush_td']))
                        else:
                            f.write('0, 0, 0, ')
                        if 'rec' in stat_dict:
                            f.write('%s, %s, %s, %s, ' % (
                            stat_dict['targets'], stat_dict['rec'], stat_dict['rec_yds'], stat_dict['rec_td']))
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
