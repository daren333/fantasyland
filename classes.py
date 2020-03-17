from os import path, stat

class Player:
    def __init__(self, pid, fn, ln, pos, sal, team, injury_status, url=None):
        self.pid = pid
        self.fn = fn
        self.ln = ln
        self.pos = pos
        self.sal = sal
        self.team = team
        self.injury_status = injury_status
        self.stats = {'gamelogs' : {}, 'splits' : {}, 'fantasy' : {}}

    def write_stats(self, db):
        for stat_type, v in self.stats.items():
            for year, stats_dict in v.items():
                filepath = '%s/%s_%s.csv'%(db, stat_type, year)
                
                with open(filepath, 'w') as f:
                    if stat_type == 'splits':
                         # write headers if file doesn't exist yet
                        if not path.exists(filepath) or path.getsize(filepath) == 0:
                            f.write('pid, first, last, pos, team, ')
                            for stat_header, splits in stats_dict.items():
                                for split in splits.keys():
                                    f.write('%s-%s, ' % (stat_header, split))
                            f.write('\n')
                        #write stats to csv
                        for stat_header, splits in stats_dict.items():
                            f.write('%s, %s, %s, %s, %s, ' %(self.pid, self.fn, self.ln, self.pos, self.team))
                            for split in splits.values():
                                f.write('%s, ' % split)
                            f.write('\n')
                    else:
                        # write headers if file doesn't exist yet
                        if not path.exists(filepath) or path.getsize(filepath) == 0:
                            f.write('pid, first, last, pos, team, week, ')
                            week = next(iter(stats_dict))
                            for stat_header in stats_dict[week].keys():
                                f.write('%s, '%stat_header)
                            f.write('\n')
                        #write stats to csv
                        for week in sorted(stats_dict.keys()):
                            f.write('%s, %s, %s, %s, %s, ' %(self.pid, self.fn, self.ln, self.pos, self.team))
                            f.write('%s, ' % week)
                            for stat in stats_dict[week].values():
                                f.write('%s, '%stat)
                            f.write('\n')

                    



class Game:

	def __init__(self, date=None, home=None, away=None, favorite=None, spread=None, over_under=None):
		self.date = date
		self.home = home
		self.away = away
		self.favorite = favorite
		self.spread = spread
		self.over_under = over_under

	def to_string(self):
		print("date: %s" %self.date)
		print("home: %s" %self.home)
		print("away: %s" %self.away)
		print("favorite: %s" %self.favorite)
		print("spread: %s" %self.spread)
		print("over_under: %s" %self.over_under)

class GameLog_Stat:
    
    def __init__(self, date, game_num, week_num, age, team, away, opp, result,
                    rec_tgt, recs, rec_yds, yds_per_rec, rec_td, catch_per, yds_per_tgt,
                    ru_att, ru_yds, yds_per_att, ru_td,
                    pa_comp, pa_att, comp_perc, pa_yds, pa_td, pa_int, pa_rate, pa_sack, pa_yds_per_att,
                    punt_ret, punt_ret_yds, punt_yds_per_ret, punt_tds,
                    fum, fum_lost,
                    off_snap_cnt, off_snap_per, st_snap_cnt, st_snap_per):

                    self.date = date 
                    self.game_num = game_num
                    self.week_num = week_num
                    self.age = age
                    self.team = team
                    self.away = away #boolean 
                    self.opp = opp
                    self.game_res = result
                    self.rec_tgt = rec_tgt
                    self.recs = recs
                    self.rec_yds = rec_yds 
                    self.yds_per_rec = yds_per_rec
                    self.rec_td = rec_td
                    self.catch_percent = catch_per
                    self.yds_per_tgt = yds_per_tgt
                    self.ru_att = ru_att
                    self.ru_yds = ru_yds
                    self.yds_per_att = yds_per_att
                    self.ru_td = ru_td, 
                    self.pa_comp = pa_comp
                    self.pa_att = pa_att
                    self.comp_perc = comp_perc 
                    self.pa_yds = pa_yds 
                    self.pa_td = pa_td
                    self.pa_int = pa_int
                    self.pa_rate = pa_rate
                    self.pa_sack = pa_sack
                    self.pa_yds_per_att = pa_yds_per_att
                    self.punt_ret = punt_ret
                    self.punt_ret_yds = punt_ret_yds
                    self.punt_yds_per_ret = punt_yds_per_ret
                    self.punt_ret_tds = punt_tds,
                    self.fum = fum 
                    self.fum_lost = fum_lost
                    self.off_snap_cnt = off_snap_cnt
                    self.off_snap_per = off_snap_per
                    self.st_snap_cnt = st_snap_cnt
                    self.st_snap_per = st_snap_per