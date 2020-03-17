from bs4 import BeautifulSoup
import csv
import requests
import re

from classes import Player, Game

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

def craft_url(player, max_retries = 5):
    base_url = 'http://www.pro-football-reference.com/players'
    last_initial = player.ln[0]
    ln_four = player.ln[0:4]
    fn_two = player.fn[0:2]
    ref_num = 0
    url = '%s/%s/%s%s0%d.htm' % (base_url, last_initial, ln_four, fn_two, ref_num)
    #url = 'https://www.pro-football-reference.com/players/B/BradTo00.htm'
    r = requests.get(url)
    pos = None
    team = None

    while r.status_code == 404:
        if ref_num <= max_retries:
            print('404 received for URL: %s\nincrementing ref_num and trying again' % url)
            ref_num += 1
            url = '%s/%s/%s%s0%d.htm' % (base_url, last_initial, ln_four, fn_two, ref_num)
            r = requests.get(url)
        else:
            print('Max number of retries attempted. failed to get page for %s %s' % (player.fn, player.ln))
            return -1

    while pos != player.pos or team != player.team:
        r = requests.get(url)
        soup = BeautifulSoup(r.text, features='lxml')
        pos_div = soup.select('#meta > div:nth-child(2) > p:nth-child(3)')
        pd = re.search(r">\:\s(\w+)", str(pos_div))
    
        if pd:
            pos = pd.group(1)
            team = get_team_id(pos, soup)  
            print("last name: %s\n team: %s\n position: %s" % (player.ln, team, pos))
        else:
            if ref_num <= max_retries:
                print('Wrong player info received for URL: %s\nincrementing ref_num and trying again' % url)
                ref_num += 1
                url = '%s/%s/%s%s0%d.htm' % (base_url, last_initial, ln_four, fn_two, ref_num)
                
            else:
                print('Max number of retries attempted. failed to get page for %s %s' % (player.fn, player.ln))
                return -2
    player.url = url
    return soup

def scrape_playerdata(player, soup):
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
    
    scrape_gamelogs(player, gamelogs)
    scrape_fantasy(player, fantasy)
    scrape_splits(player, splits)
    

def scrape_gamelogs(player, gamelogs):
    for year in gamelogs.keys():
        r = requests.get(gamelogs[year])
        soup = BeautifulSoup(r.text, features='lxml')
        year_stats = {}

        i = 1
        while soup.select("#stats > tbody > tr:nth-of-type(%d)" % i):
            week_stats = {}
            row = soup.select("#stats > tbody > tr:nth-of-type(%d)" % i)
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
        player.stats['gamelogs'][year] = year_stats
    return

def scrape_splits(player, splits):
    splits_data = {}

    for year in splits.keys():
        year_splits = {}
        year_data = {}
        splits_data[year] = year_splits
        split_id = None

        r = requests.get(splits[year])
        soup = BeautifulSoup(r.text, features='lxml')
        tables = ["#stats", "#advanced_splits"]
        for table in tables:
            i = 1
            while(soup.select(table + " > tbody > tr:nth-child(%d)" % i)):
                row = soup.select("#stats > tbody > tr:nth-child(%d)" % i)
                s = re.search(r"thead", str(row))
                if not s:
                    stats = {}
                    s = re.search(r"data-stat=\"split_id\".*?>(.*?)</", str(row))
                    if s and s.group(1) != '':
                        split_id = s.group(1)
                        curr_data = {}
                        year_splits[split_id] = curr_data
                    s = re.search(r"data-stat=\"split_value\">(.*?)</", str(row))
                    if s:
                        split_val = s.group(1)
                        s = re.search(r"<a href=.*?>(.*)", split_val)
                        if s:
                            split_val = s.group(1)

                    stats_scraped = re.findall(r"data-stat=\"(.*?)\".*?>(.*?)</", str(row))
                    for scraped_stat in stats_scraped:
                        stats[scraped_stat[0]] = scraped_stat[1]
                    # Remove split_id and split_value from stats
                    stats.pop('split_id')
                    stats.pop('split_value')
                    curr_data[split_val] = stats
                i += 1
        #remove redundent League data
        splits_data[year].pop('League')
    player.stats['splits'] = splits_data

    return

def scrape_fantasy(player, fantasy):
    for year in fantasy.keys():
        r = requests.get(fantasy[year])
        soup = BeautifulSoup(r.text, features='lxml')
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
        player.stats['fantasy'][year] = year_stats
    return