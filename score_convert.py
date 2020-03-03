
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


def calc_passing(player, score_settings):
	pass_yds = player['Passing Yards'] * score_settings['PaY']
	pass_tds = player['TD Passes'] * score_settings['PaTD']
	ints = player['TD Passes'] * score_settings['PaI']


def calc_rushing(player, score_settings):
	rush_yds = player['Receiving Yards'] * score_settings['RuY']
	rush_tds = player['Receiving TDs'] * score_settings['RuTD']
	return rush_yds + rush_tds


def calc_receiving(player, score_settings):
	recs = player['Receptions'] * score_settings['Re']
	rec_yds = player['Receiving Yards'] * score_settings['ReY']
	rec_tds = player['Receiving TDs'] * score_settings['ReTD']
	return recs + rec_yds + rec_tds


def calc_scoring(players, score_settings = fanduel_settings):
	total_points = 0
	for player in players:
		if player['Passes Completed'] > 0:
			total_points += calc_passing(player)
		if player['Rushes'] > 0:
			total_points += calc_rushing(player)
		if player['Receptions'] > 0:
			total_points += calc_receiving(player)
		# subtract -2 for fumbles lost
		total_points += player['Fumbles Lost'] * score_settings['FU/L']
