from bs4 import BeautifulSoup, SoupStrainer
import requests
import re
import time

import config

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
    if team_name in config.team_map:
        return config.team_map[team_name]
    else:
        return None


def get_player_pos(soup):
    pos_div = soup.select('#meta > div:nth-child(2) > p:nth-child(3)')
    pd = re.search(r">\:\s(\w+)", str(pos_div))

    if pd:
        return pd.group(1)
    raise Exception(f"Could not get player position from position div: {str(pos_div)}")


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
    return soup
    #     i = 1
    #     while i < max_rows and soup.select(f"#fantasy > tbody > tr:nth-child({i})"):
    #         # skip header rows
    #         if not soup.select(f"#fantasy > tbody > tr:nth-child({i}) > th.ranker.sort_default_asc.show_partial_when_sorting.center"):
    #             player_name, player_link = get_player_name_and_link_from_playerlist(soup.select(f'#fantasy > tbody > tr:nth-child({i}) > td:nth-child(2) > a'))
    #             player_fn = player_name.split()[0]
    #             # Get multi last names like St. Brown and combine into one last name
    #             player_ln = ' '.join([str(elem) for elem in player_name.split()[1:]])
    #             player_age = get_player_age_from_playerlist(soup.select(f'#fantasy > tbody > tr:nth-child({i}) > td:nth-child(5)'))
    #             #players.append(Player(fn=player_fn, ln=player_ln, age=player_age, url=player_link))
    #             print(f"Got playerdata for {player_name}")
    #         i += 1
    # return players
