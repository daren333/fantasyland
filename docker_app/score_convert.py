
fanduel_settings = {'PaTD':4, 'PaY':0.04, 'PaI':-1,
					'Re': 0.5, 'ReY':0.1, 'ReTD':6,
					'RuY': 0.1, 'RuTD':6, 'FU/L':-2,
					'2PC':2, 'KR/TD':6, 'PR/TD':6,
					'DE/PA0':10, 'DE/PA1-6':7, 'DE/PA7-13':4,
					'DE/PA14-20':1, 'DE/PA28-34':-1, 'DE/PA35+':-4,
					'DE/BK':2, 'DE/Safe':2, 'DE/XPR':2,
					'DE/FR':2, 'DE/Int':2, 'DE/Sack':1,
					'DE/RTD':6, 'DE/BRTD': 6, 'DE/FRTD':6
					}


dynasty_settings = {'PaTD':4, 'PaY':0.04, 'PaI':-1,
					'Re': 1, 'ReY':0.1, 'ReTD':6,
					'RuY': 0.1, 'RuTD':6, 'FU':-1,
					'FU/L':-2, '2PC':2, 'KR/TD':6,
					'PR/TD':6
					}

# pass attempts
# rush attempts
# targets
# fantasy -> offense pct

def calc_passing(player, week = None, score_settings = fanduel_settings):
	if score_settings == fanduel_settings:
		pass_yds = player['Passing Yards'] * score_settings['PaY']
		pass_tds = player['TD Passes'] * score_settings['PaTD']
		ints = player['TD Passes'] * score_settings['PaI']
	elif score_settings == dynasty_settings:
		pass_yds = 0
		pass_tds = 0
		ints = 0
		if week['pass_yds']:
			pass_yds = float(week['pass_yds']) * score_settings['PaY']
		if week['pass_td']:
			pass_tds = float(week['pass_td']) * score_settings['PaTD']
		if week['pass_int']:
			ints = float(week['pass_int']) * score_settings['PaI']
		return pass_yds + pass_tds + ints


def calc_rushing(player, week = None, score_settings = fanduel_settings):
	if score_settings == fanduel_settings:
		rush_yds = player['Receiving Yards'] * score_settings['RuY']
		rush_tds = player['Receiving TDs'] * score_settings['RuTD']
		return rush_yds + rush_tds
	elif score_settings == dynasty_settings:
		rush_yds = 0
		rush_tds = 0
		if week['rush_yds']:
			rush_yds = float(week['rush_yds']) * score_settings['RuY']
		if week['rush_td']:
			rush_tds = float(week['rush_td']) * score_settings['RuTD']
		return rush_yds + rush_tds


def calc_receiving(player, week = None, score_settings = fanduel_settings):
	if score_settings == fanduel_settings:
		recs = player['Receptions'] * score_settings['Re']
		rec_yds = player['Receiving Yards'] * score_settings['ReY']
		rec_tds = player['Receiving TDs'] * score_settings['ReTD']
		return recs + rec_yds + rec_tds
	elif score_settings == dynasty_settings:
		recs = 0
		rec_yds = 0
		rec_tds = 0
		if week['rec']:
			recs = float(week['rec']) * score_settings['Re']
		if week['rec_yds']:
			rec_yds = float(week['rec_yds']) * score_settings['ReY']
		if week['rec_td']:
			rec_tds = float(week['rec_td']) * score_settings['ReTD']
		if player.pos == 'TE':
			recs = 2 * recs
		return recs + rec_yds + rec_tds


def calc_misc(player, week = None, score_settings = fanduel_settings):
	if score_settings == dynasty_settings:
		fums = 0
		fums_lost = 0
		two_pt_convs = 0
		kick_ret_tds = 0
		punt_ret_tds = 0
		if 'fumbles' in week and week['fumbles']:
			fums = float(week['fumbles']) * score_settings['FU']
		if 'fumbles_lost' in week and week['fumbles_lost']:
			fums_lost = float(week['fumbles_lost']) * score_settings['FU/L']
		if 'two_pt_md' in week and week['two_pt_md']:
			two_pt_convs = float(week['two_pt_md']) * score_settings['2PC']
		if 'kick_ret_td' in week and week['kick_ret_td']:
			kick_ret_tds = float(week['kick_ret_td']) * score_settings['KR/TD']
		if 'punt_ret_td' in week and week['punt_ret_td']:
			punt_ret_tds = float(week['punt_ret_td']) * score_settings['PR/TD']
		return fums + fums_lost + two_pt_convs + kick_ret_tds + punt_ret_tds


def fill_empties(week):
	for k, v in week.items():
		if v == '\"':
			week[k] = '0'


def calc_dynasty_scoring(player):
	years = {}
	#weeks = {}

	player.dynasty_scoring = {}

	for year in player.years:
		weeks = {}
		year_pts = 0
		for week in player.years[year]['gamelogs'].keys():
			week_pts = 0
			week_num = week
			#[stat.replace('\"', '0') for stat in player.years[year]['gamelogs'][week].values()]
			fill_empties(player.years[year]['gamelogs'][week])
			if 'pass_att' in player.years[year]['gamelogs'][week]:
				week_pts += calc_passing(player, player.years[year]['gamelogs'][week], dynasty_settings)
			if 'rush_att' in player.years[year]['gamelogs'][week]:
				week_pts += calc_rushing(player, player.years[year]['gamelogs'][week], dynasty_settings)
			if 'rec' in player.years[year]['gamelogs'][week]:
				week_pts += calc_receiving(player, player.years[year]['gamelogs'][week], dynasty_settings)
			week_pts += calc_misc(player, player.years[year]['gamelogs'][week], dynasty_settings)
			year_pts += round(week_pts, 2)
			weeks[week_num] = round(week_pts, 2)
		years[year] = year_pts
		player.dynasty_scoring[year] = weeks


def calc_scoring(players, score_settings = dynasty_settings):
	total_points = 0

	if score_settings == fanduel_settings:
		for player in players:
			if player['Passes Completed'] > 0:
				total_points += calc_passing(player)
			if player['Rushes'] > 0:
				total_points += calc_rushing(player)
			if player['Receptions'] > 0:
				total_points += calc_receiving(player)
			# subtract -2 for fumbles lost
			total_points += player['Fumbles Lost'] * score_settings['FU/L']
	elif score_settings == dynasty_settings:
		for player in players:
			year_points = 0
			for year in player.years:
				for week in year.stats['gamelogs'].items():
					week_points = 0
					week_str = week['week_num']
					week_points += calc_passing(week, score_settings)
					week_points += calc_rushing(week, score_settings)
					week_points += calc_receiving(week, score_settings)
					year_points += week_points

