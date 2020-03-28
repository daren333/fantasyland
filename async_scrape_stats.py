import asyncio
from aiohttp import ClientSession, ClientTimeout
import aiofiles
from bs4 import BeautifulSoup, SoupStrainer
import csv
import re
import time

from async_classes import Player, Game, PlayerSeason
from async_writer import write_to_db


async def scrape_player(player, db_path, test_mode=True):
    # Set timeout to 15 minutes instead of default 5
    async with ClientSession(timeout=ClientTimeout(15*60)) as session:
        soup = await craft_url(player, session, test_mode)
        await scrape_playerdata(player, session, soup, test_mode)
        await write_to_db(player, db_path)


def get_team_id(pos, soup):

    if pos == 'QB':
        team_div = soup.select('#passing\.2019 > td:nth-child(3) > a')
        td = re.search(r">(\w+)<", str(team_div))
    else:
        team_div = soup.select('#rushing_and_receiving\.2019 > td:nth-child(3) > a')
        td = re.search(r">(\w+)<", str(team_div))
        if not td:
            team_div = soup.select('#receiving_and_rushing\.2019 > td:nth-child(3) > a')
            td = re.search(r">(\w+)<", str(team_div))
    return td.group(1)
    

# Players page follows the standard: 
# players/
# /capitalized first letter of last name/
# /first four letters of last name (first letter capitalized) 
# first two letters of first name (first letter capitalized)
# number for repeat names (usually 00)
# .htm
# ex. Tom Brady = players/B/BradTo00.htm

async def craft_url(player, session, max_retries = 5, test_mode = False):
    base_url = 'http://www.pro-football-reference.com/players'
    last_initial = player.ln[0]
    ln_four = player.ln[0:4]
    fn_two = player.fn[0:2]
    ref_num = 0
    url = '%s/%s/%s%s0%d.htm' % (base_url, last_initial, ln_four, fn_two, ref_num)

    start = time.time()

    r = await session.request(method="GET", url=url)
    pos = None
    team = None

    while r.status == 404:
        if ref_num <= max_retries:
            print('404 received for URL: %s\nincrementing ref_num and trying again' % url)
            ref_num += 1
            url = '%s/%s/%s%s0%d.htm' % (base_url, last_initial, ln_four, fn_two, ref_num)
            r = await session.request(method="GET", url=url)
        else:
            print('Max number of retries attempted. failed to get page for %s %s' % (player.fn, player.ln))
            return -1

    while pos != player.pos or team != player.curr_team:
        r = await session.request(method="GET", url=url)
        r = await r.text()
        soup = BeautifulSoup(r, features='lxml')
        pos_div = soup.select('#meta > div:nth-child(2) > p:nth-child(3)')
        pd = re.search(r">\:\s(\w+)", str(pos_div))

        if pd:
            pos = pd.group(1)
            team = get_team_id(pos, soup)
            print("last name: %s\n team: %s\n position: %s" % (player.ln, team, pos))
        else:
            if ref_num <= max_retries:
                print('Wrong player info received for URL: %s\nIncrementing ref_num and trying again' % url)
                ref_num += 1
                url = '%s/%s/%s%s0%d.htm' % (base_url, last_initial, ln_four, fn_two, ref_num)

            else:
                print('Max number of retries attempted. failed to get page for %s %s' % (player.fn, player.ln))
                return -2
    player.url = url

    end = time.time()
    if test_mode:
        print("HTML (soup) obtained in %.2f seconds" % (end - start))

    return soup


async def scrape_playerdata(player, session, soup, test_mode = False):
    start = time.time()
    gamelogs = {}
    splits = {}
    fantasy = {}

    gamelogs_html = soup.select("#bottom_nav_container > ul:nth-child(5)")
    splits_html = soup.select("#bottom_nav_container > ul:nth-child(7)")
    fantasy_html = soup.select("#bottom_nav_container > ul:nth-child(9)")

    gamelog_links = re.findall(r"href=\"(.*/gamelog/\d{4}/)\">(\d{4})<", str(gamelogs_html))
    for link in gamelog_links:
        url = link[0]
        year = link[1]
        gamelogs[year] = "https://www.pro-football-reference.com" + url
    
    splits_links = re.findall(r"href=\"(.*/splits/\d{4}/)\">(\d{4})<", str(splits_html))
    for link in splits_links:
        url = link[0]
        year = link[1]
        splits[year] = "https://www.pro-football-reference.com" + url

    fantasy_links = re.findall(r"href=\"(.*/fantasy/\d{4}/)\">(\d{4})<", str(fantasy_html))
    for link in fantasy_links:
        url = link[0]
        year = link[1]
        fantasy[year] = "https://www.pro-football-reference.com" + url
    
    # Set up year objects for players
    player.years = [PlayerSeason(year, set()) for year in gamelogs.keys()]

    await scrape_gamelogs(player, gamelogs, session, test_mode=test_mode)
    await scrape_fantasy(player, fantasy, session, test_mode=test_mode)
    await scrape_splits(player, splits, session, test_mode=test_mode)

    end = time.time()
    if test_mode:
        print("Total scrape time is %f seconds" % (end - start))
    

async def scrape_gamelogs(player, gamelogs, session, test_mode):
    start = time.time()

    for year in gamelogs.keys():
        r = await session.request(method="GET", url=gamelogs[year])
        r = await r.text()
        strainer = SoupStrainer(id='all_stats')
        soup = BeautifulSoup(r, features='lxml', parse_only=strainer)
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

        year_obj = player.get_year(year)
        year_obj.stats['gamelogs'] = year_stats
        # add teams played for for each week
        [year_obj.teams.add(year_stats[week]['team']) for week in year_stats]

    end = time.time()
    if test_mode:
        print("Gamelog scrape time is %.2f seconds" % (end - start))
    return


async def scrape_splits(player, splits, session, test_mode):
    start = time.time()
    avg_get_time = 0
    avg_parse_time = 0
    splits_data = {}

    for year in splits.keys():
        year_obj = player.get_year(year)
        year_splits = {}
        year_obj.stats['splits'] = year_splits
        split_id = None

        get_time_start = time.time()
        r = await session.request(method="GET", url=splits[year])
        r = await r.text()
        get_time_end = time.time()

        parse_time_start = time.time()
        strainer = SoupStrainer(id=['all_stats', 'all_advanced_splits'])
        soup = BeautifulSoup(r, features='lxml', parse_only=strainer)
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
                        split_id = s.group(1)
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
                    if table == '#stats':
                        stats.pop('split_id')
                        stats.pop('split_value')
                    else:
                        stats.pop('split_type')
                        stats.pop('split_value')
                    curr_data[split_val] = stats

                i += 1

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


async def scrape_fantasy(player, fantasy, session, test_mode):
    start = time.time()

    for year in fantasy.keys():
        r = await session.request(method="GET", url=fantasy[year])
        r = await r.text()
        strainer = SoupStrainer(id='all_player_fantasy')
        soup = BeautifulSoup(r, features='lxml', parse_only=strainer)
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
        year_obj = player.get_year(year)
        year_obj.stats['fantasy'] = year_stats

    end = time.time()
    if test_mode:
        print("Fantasy stats scrape time is %.2f seconds" % (end - start))

    return
