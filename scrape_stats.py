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

def walk_homepage(player, soup):
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
    
    scrape_game_logs(player, gamelogs)    


def scrape_game_logs(player, gamelogs):
    stats = {}

    for year in gamelogs.keys():
        r = requests.get(gamelogs[year])
        soup = BeautifulSoup(r.text, features='lxml')
        table = soup.find_all(re.compile(r"stats\.\d"))
        print(table)



