from bs4 import BeautifulSoup, SoupStrainer
import requests
import re
import time

import config
from classes.Player import Player
from config import team_map

# Aligns team abbreviations w/ pro football ref abbrevs
def fix_team_abbrev(team):
    if team == 'KC':
        return 'KAN'
    elif team == 'GB':
        return 'GNB'
    elif team == 'TB':
        return 'TAM'
    elif team == 'SF':
        return 'SFO'
    elif team == 'NO':
        return 'NOR'
    elif team == 'LV':
        return 'LVR'
    elif team == 'NE':
        return 'NWE'
    elif team == 'FA':
        return 'CAR'
    elif team == 'JAC':
        return 'JAX'
    else:
        return team


def convert_to_short_team_name(team_name):
    if team_name in team_map:
        return team_map[team_name]
    else:
        return None


def try_alt_pos_div_2(soup, orig_div_1, orig_div_2):
    pos_div = soup.select('#meta > div:nth-child(2) > p:nth-child(2)')
    pd = re.search(r">\:\s(\w+)", str(pos_div))
    if pd:
        return pd.group(1)
    else:
        raise Exception(f"Could not get player position from position div: "
                        f"{str(orig_div_1)}"
                        f"{str(orig_div_2)}"
                        f"{str(pos_div)}")


def try_alt_pos_div(soup, orig_div):
    pos_div = soup.select('#meta > div > p:nth-child(3)')
    pd = re.search(r">\:\s(\w+)", str(pos_div))
    if pd:
        return pd.group(1)
    else:
        return try_alt_pos_div_2(soup=soup, orig_div_1=orig_div, orig_div_2=pos_div)


def get_player_pos(soup):
    pos_div = soup.select('#meta > div:nth-child(2) > p:nth-child(3)')
    pd = re.search(r">\:\s(\w+)", str(pos_div))

    if pd:
        return pd.group(1)
    # try alternate location (where it would be if no picture)
    else:
        return try_alt_pos_div(soup=soup, orig_div=pos_div)


def get_team_id(soup):
    team_div = soup.select("#meta > div:nth-child(2) > p:nth-child(5) > span > a")
    td = re.search(r">(\w+\s?\w+\s?\w+)<", str(team_div))
    if td:
        return convert_to_short_team_name(td.group(1))
    else:
        return None


def get_player_name_and_link_from_playerlist(player_name_div):
    m = re.search(r"href=\"(.*)\">(.*)<\/a>", str(player_name_div))
    if m and m.lastindex == 2:
        player_name = m.group(2)
        player_link = config.base_url + m.group(1)
        return player_name, player_link
    else:
        raise Exception(f"Could not get player name or link from div: {str(player_name_div)}")


def get_current_team(player_link, session):
    r = session.get(player_link)

    if r.status_code != 200:
        raise Exception(f"Bad link {player_link}")

    soup = BeautifulSoup(r.text, features='lxml')
    return get_team_id(soup)


def get_player_team_from_playerlist(player_team_div, player_link, session):
    # check for multi team guys
    m = re.search(r"\d+TM", str(player_team_div))
    if m:
        return get_current_team(player_link, session)
    m = re.search(r"title=\"(.*)\"", str(player_team_div))
    if m:
        return m.group(1)
    raise Exception(f"Could not get team from div: {str(player_team_div)}")


def get_player_position_from_playerlist(player_pos_div):
    m = re.search(r">(\w{2})</td>", str(player_pos_div))
    if m:
        player_pos = m.group(1)
        return player_pos
    else:
        raise Exception(f"Could not get player position from div: {str(player_pos_div)}")


def get_player_age_from_playerlist(player_age_div):
    m = re.search(r">(\d{2})</td>", str(player_age_div))
    if m:
        player_age = m.group(1)
        return player_age
    else:
        raise Exception(f"Could not get player position from div: {str(player_age_div)}")


def scrape_playerlist(url, max_rows=1000):
    players = []
    with requests.Session() as session:
        r = session.get(url)

        if r.status_code != 200:
            raise Exception(f"Bad link {url}")

        strainer = SoupStrainer(id='all_fantasy')
        soup = BeautifulSoup(r.text, features='lxml', parse_only=strainer)

        i = 1
        while i < max_rows and soup.select(f"#fantasy > tbody > tr:nth-child({i})"):
            # skip header rows
            if not soup.select(f"#fantasy > tbody > tr:nth-child({i}) > th.ranker.sort_default_asc.show_partial_when_sorting.center"):
                player_name, player_link = get_player_name_and_link_from_playerlist(soup.select(f'#fantasy > tbody > tr:nth-child({i}) > td:nth-child(2) > a'))
                player_fn = player_name.split()[0]
                # Get multi last names like St. Brown and combine into one last name
                player_ln = ' '.join([str(elem) for elem in player_name.split()[1:]])
                player_age = get_player_age_from_playerlist(soup.select(f'#fantasy > tbody > tr:nth-child({i}) > td:nth-child(5)'))
                players.append(Player(fn=player_fn, ln=player_ln, age=player_age, url=player_link))
                print(f"Got playerdata for {player_name}")
            i += 1
    return players


# Players page follows the standard: 
# players/
# /capitalized first letter of last name/
# /first four letters of last name (first letter capitalized) 
# first two letters of first name (first letter capitalized)
# number for repeat names (usually 00)
# .htm
# ex. Tom Brady = players/B/BradTo00.htm
def craft_url(player, max_retries = 5, test_mode = False):
    base_url = 'http://www.pro-football-reference.com/players'
    last_initial = player.ln[0]
    ln_four = player.ln[0:4]
    fn_two = player.fn[0:2]
    ref_num = 0
    url = '%s/%s/%s%s0%d.htm' % (base_url, last_initial, ln_four, fn_two, ref_num)

    start = time.time() 

    with requests.Session() as session:
        r = session.get(url)
        pos = None
        team = None

        while r.status_code == 404:
            if ref_num <= max_retries:
                print('404 received for URL: %s\nincrementing ref_num and trying again' % url)
                ref_num += 1
                url = '%s/%s/%s%s0%d.htm' % (base_url, last_initial, ln_four, fn_two, ref_num)
                time.sleep(.5)
                r = session.get(url)
            else:
                print('Max number of retries attempted. failed to get page for %s %s' % (player.fn, player.ln))
                return -1

        while pos != player.pos or team != player.curr_team:
            time.sleep(.5)
            r = session.get(url)
            soup = BeautifulSoup(r.text, features='lxml')
            pos_div = soup.select('#meta > div:nth-child(2) > p:nth-child(3)')
            pd = re.search(r">\:\s(\w+)", str(pos_div))
        
            if pd:
                pos = pd.group(1)
                team = get_team_id(soup)
                full_web_name = soup.select('#meta > div:nth-child(2) > h1 > span')[0].contents[0].strip()
                full_name = '%s %s' % (player.fn, player.ln)
                if pos == player.pos and team == player.curr_team and full_name in full_web_name:
                    print("last name: %s\n team: %s\n position: %s" % (player.ln, team, pos))
                else:
                    if ref_num <= max_retries:
                        print('Wrong player info received for URL: %s\nIncrementing ref_num and trying again' % url)
                        ref_num += 1
                        url = '%s/%s/%s%s0%d.htm' % (base_url, last_initial, ln_four, fn_two, ref_num)

                    else:
                        print('Max number of retries attempted. failed to get page for %s %s' % (player.fn, player.ln))
                        return -2
            else:
                if ref_num <= max_retries:
                    print('Wrong player info received for URL: %s\nIncrementing ref_num and trying again' % url)
                    ref_num += 1
                    url = '%s/%s/%s%s0%d.htm' % (base_url, last_initial, ln_four, fn_two, ref_num)
                    
                else:
                    print('Max number of retries attempted. failed to get page for %s %s' % (player.fn, player.ln))
                    return None
        player.url = url

        end = time.time()
        if test_mode:
            print("HTML (soup) obtained in %.2f seconds" %(end - start))

        return soup


def scrape_playerdata(player, years_to_scrape=None, test_mode=False):
    print(f"Scraping playerdata for player: {player.fn} {player.ln}")
    with requests.Session() as session:
        r = session.get(player.url)
        if r.status_code != 200:
            raise Exception(f"Player link wrong for player: {player.fn} {player.ln} {player.url}. Status code: {r.status_code}")
        soup = BeautifulSoup(r.text, features='lxml')

        player.pos = get_player_pos(soup)
        player.curr_team = get_team_id(soup)

        start = time.time()
        gamelogs = {}
        advanced_gamelogs = {}
        splits = {}
        fantasy = {}
        #try:
        gamelogs_html = soup.select("#inner_nav > ul > li:nth-child(2) > div")
        splits_html = soup.select("#inner_nav > ul > li:nth-child(3)")
        fantasy_html = soup.select("#inner_nav > ul > li:nth-child(4)")

        gamelog_links = re.findall(r"href=\"(.*/gamelog/\d{4}/)\">(\d{4})<", str(gamelogs_html))
        for link in gamelog_links:
            url = link[0]
            year = link[1]
            if (years_to_scrape and year in years_to_scrape) or not years_to_scrape:
                gamelogs[year] = "https://www.pro-football-reference.com" + url
                advanced_gamelogs[year] = "https://www.pro-football-reference.com" + url + "advanced"

        splits_links = re.findall(r"href=\"(.*/splits/\d{4}/)\">(\d{4})<", str(splits_html))
        for link in splits_links:
            url = link[0]
            year = link[1]
            if (years_to_scrape and year in years_to_scrape) or not years_to_scrape:
                splits[year] = "https://www.pro-football-reference.com" + url


        fantasy_links = re.findall(r"href=\"(.*/fantasy/\d{4}/)\">(\d{4})<", str(fantasy_html))
        for link in fantasy_links:
            url = link[0]
            year = link[1]
            if (years_to_scrape and year in years_to_scrape) or not years_to_scrape:
                fantasy[year] = "https://www.pro-football-reference.com" + url

        # Set up year objects for players
        player.years = {year: {} for year in gamelogs.keys()}

        with requests.Session() as session:
            scrape_gamelogs(player, gamelogs, session, test_mode=test_mode)
            scrape_advanced_gamelogs(player, advanced_gamelogs, session, test_mode=test_mode)
            scrape_fantasy(player, fantasy, session, test_mode=test_mode)
            scrape_splits(player, splits, session, test_mode=test_mode)

        end = time.time()
        if test_mode:
            print("Total scrape time is %f seconds" % (end - start))
        return 0
        # except Exception as e:
        #     print(e)
        #     print('Unable to get data for %s %s' % (player.fn, player.ln))
        #     return None


def scrape_gamelogs(player, gamelogs, session, test_mode):
    start = time.time()

    for year in gamelogs.keys():
        time.sleep(.5)
        r = session.get(gamelogs[year])
        strainer = SoupStrainer(id='all_stats')
        soup = BeautifulSoup(r.text, features='lxml', parse_only=strainer)
        year_stats = {}

        i = 1
        while soup.select("#stats > tbody > tr:nth-of-type(%d)" % i):
            week_stats = {}
            row = str(soup.select("#stats > tbody > tr:nth-of-type(%d)" % i))
            stats = re.findall(r"data-stat=\"(.*?)\".*?>(.*?)</", row)
            for stat in stats:
                s = re.search(r"<a href=.*?>(.*)", stat[1])
                if s:
                    week_stats[stat[0]] = s.group(1)
                else:
                    week_stats[stat[0]] = stat[1]
            game = week_stats["game_num"]
            year_stats[game] = week_stats
            i += 1
        
        # year_obj = player.get_year(year)
        # year_obj.stats['gamelogs'] = year_stats
        player.years[year]['gamelogs'] = year_stats
        # add teams played for for each week 
        #[year_obj.teams.add(year_stats[week]['team']) for week in year_stats]
    
    end = time.time()
    if test_mode:
        print("Gamelog scrape time is %.2f seconds" % (end - start))
    return


def scrape_advanced_gamelogs(player, adv_gamelogs, session, test_mode):
    start = time.time()

    for year in adv_gamelogs.keys():
        time.sleep(.5)
        r = session.get(adv_gamelogs[year])
        strainer = SoupStrainer(id='content')
        soup = BeautifulSoup(r.text, features='lxml', parse_only=strainer)
        year_stats = {}
        year_passing_stats = {}

        i = 1
        while soup.select("#advanced_rushing_and_receiving > tbody > tr:nth-of-type(%d)" % i):
            week_stats = {}
            row = str(soup.select("#advanced_rushing_and_receiving > tbody > tr:nth-of-type(%d)" % i))
            stats = re.findall(r"data-stat=\"(.*?)\".*?>(.*?)</", row)
            for stat in stats:
                s = re.search(r"<a href=.*?>(.*)", stat[1])
                if s:
                    week_stats[stat[0]] = s.group(1)
                else:
                    week_stats[stat[0]] = stat[1]
            game = week_stats["game_num"]
            year_stats[game] = week_stats
            i += 1

        # get passing stats
        if player.pos == "QB":
            i = 1
            while soup.select("#advanced_passing > tbody > tr:nth-of-type(%d)" % i):
                week_passing_stats = {}
                row = str(soup.select("#advanced_passing > tbody > tr:nth-of-type(%d)" % i))
                stats = re.findall(r"data-stat=\"(.*?)\".*?>(.*?)</", row)
                for stat in stats:
                    s = re.search(r"<a href=.*?>(.*)", stat[1])
                    if s:
                        week_passing_stats[stat[0]] = s.group(1)
                    else:
                        week_passing_stats[stat[0]] = stat[1]
                game = week_passing_stats["game_num"]
                year_passing_stats[game] = week_passing_stats
                i += 1

        # year_obj = player.get_year(year)
        # year_obj.stats['adv_gamelogs'] = {"rush_rec_stats": year_stats, "passing_stats": year_passing_stats}
        # # add teams played for for each week
        # [year_obj.teams.add(year_stats[week]['team']) for week in year_stats]
        player.years[year]['adv_gamelogs_rush_rec'] = year_stats
        player.years[year]['adv_gamelogs_passing'] = year_passing_stats


    end = time.time()
    if test_mode:
        print("Advanced Gamelog scrape time is %.2f seconds" % (end - start))
    return


def scrape_splits(player, splits, session, test_mode):
    start = time.time()
    avg_get_time = 0
    avg_parse_time = 0
    splits_data = {}

    for year in splits.keys():
        time.sleep(.5)
        year_splits = {}

        split_id = None

        get_time_start = time.time()
        r = session.get(splits[year])
        get_time_end = time.time()

        parse_time_start = time.time()
        strainer = SoupStrainer(id=['all_stats', 'all_advanced_splits'])
        soup = BeautifulSoup(r.text, features='lxml', parse_only=strainer)
        tables = ["#stats", "#advanced_splits"]
        for table in tables:
            i = 1
            while soup.select(table + " > tbody > tr:nth-child(%d)" % i):
                row = str(soup.select(table + " > tbody > tr:nth-child(%d)" % i))
                
                s = re.search(r"thead", str(row))
                if not s:
                    stats = {}

                    #fix ampersand and less than signs
                    row = row.replace('&amp;', '&')
                    row = row.replace('&lt;', '<')
                    row = row.replace('&gt;', '>')

                    #b/c for some reason its split_id in one table and split_type in the other :/
                    if table == '#stats':
                        s = re.search(r"data-stat=\"split_id\".*?>(.*?)</", row)
                    else:
                        s = re.search(r"data-stat=\"split_type\".*?>(.*?)</", row)

                    if s and s.group(1) != '':
                        split_id = "Splits " + s.group(1)
                        curr_data = {}
                        year_splits[split_id] = curr_data
                    s = re.search(r"data-stat=\"split_value\">(.*?)</", row)
                    if s:
                        split_val = s.group(1)
                        # minor optimization; no hyperlinks in advanced splits tables
                        if table == '#stats':
                            s = re.search(r"<a href=.*?>(.*)", split_val)
                            if s:
                                split_val = s.group(1)
                    
                    stats_scraped = re.findall(r"data-stat=\"(.*?)\".*?>(.*?)</", row)
                    
                    for scraped_stat in stats_scraped:
                        stats[scraped_stat[0]] = scraped_stat[1]
                    

                    # Remove split_id/split_type and split_value from stats
                    # if table == '#stats':
                    #     stats.pop('split_id')
                    #     stats.pop('split_value')
                    # else:
                    #     stats.pop('split_type')
                    #     stats.pop('split_value')
                    curr_data[split_val] = stats

                i += 1

        player.years[year].update(year_splits)
        parse_time_end = time.time()
        avg_get_time += (get_time_end - get_time_start)
        avg_parse_time += (parse_time_end - parse_time_start)
        
    end = time.time()
    avg_get_time /= len(splits)
    avg_parse_time /= len(splits)
    if test_mode:
        print("Splits total time is %.2f seconds" % (end - start))
        print("Splits average get time is %.2f seconds" % avg_get_time)
        print("Splits average parse time is %.2f seconds" % avg_parse_time)

    return


def scrape_fantasy(player, fantasy, session, test_mode):
    start = time.time()

    for year in fantasy.keys():
        time.sleep(.5)
        r = session.get(fantasy[year])
        strainer = SoupStrainer(id='all_player_fantasy')
        soup = BeautifulSoup(r.text, features='lxml', parse_only=strainer)
        year_stats = {}

        i = 1
        while soup.select("#player_fantasy > tbody > tr:nth-of-type(%d)" % i):
            week_stats = {}
            row = soup.select("#player_fantasy > tbody > tr:nth-of-type(%d)" % i)
            stats = re.findall(r"data-stat=\"(.*?)\".*?>(.*?)</", str(row))
            for stat in stats:
                s = re.search(r"<a href=.*?>(.*)", stat[1])
                if s:
                    week_stats[stat[0]] = s.group(1)
                else:
                    week_stats[stat[0]] = stat[1]
            game = week_stats["game_num"]
            year_stats[game] = week_stats
            i += 1
        # year_obj = player.get_year(year)
        # year_obj.stats['fantasy'] = year_stats
        #player.stats['fantasy'][year] = year_stats
        player.years[year]['fantasy'] = year_stats


    end = time.time()
    if test_mode:
        print("Fantasy stats scrape time is %.2f seconds" % (end - start))

    return


def replace_empties(player):
    for year in player.years:
        for key in year.stats['gamelogs'].keys():
            for k, v in year.stats['gamelogs'][key].items():
                year.stats['gamelogs'][k] = str(v).replace('\"', '0')


def get_player_list():
    url = "https://www.fantasypros.com/nfl/rankings/ros-overall.php"
    with requests.Session() as session:
        r = session.get(url)
        strainer = SoupStrainer(id='ranking-table')
        soup = BeautifulSoup(r.text, features='lxml', parse_only=strainer)

        i = 1
        while soup.select("#ranking-table > tbody > tr:nth-of-type(%d)" % i):
            row = soup.select("#player_fantasy > tbody > tr:nth-of-type(%d)" % i)
            name = soup.select("#ranking-table > tbody > tr:nth-child(1) > td:nth-child(3) > div > a:nth-child(1)")