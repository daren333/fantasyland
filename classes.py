from os import path


class Season:
    def __init__(self, year):
        self.year = year

    def __repr__(self):
        return 'Season(%s)' % self.year
        

class TeamSeason(Season):
    def __init__(self, year, city, name, abbrev, players):
        super().__init__(year)
        self.city = city
        self.name = name
        self.abbrev = abbrev
        self.players = players


    def __str__(self):
        return '%s %s (%s) team stats for %s season' % (self.city, self.name, self.abbrev, self.year)

    # allows indexing by last name or pid: 
    # ex. TeamSeason['Jones'] will return a list containing all players whose last name is Jones
    def __getitem__(self, p):
        if p.isalpha():
            return [player for player in self.players if player.ln == p]
        else:
            return [pid for pid in self.players if pid == p]


class PlayerSeason(Season):
    def __init__(self, year, teams):
        super().__init__(year)
        self.teams = teams
        self.stats = {'gamelogs': {}, 'splits': {}, 'fantasy': {}}

    def __str__(self):
        return 'Player stats for %s season while playing for %s' % (self.year, self.teams)

    def __getitem__(self, stat):
        return self.stats[stat]


class Team:
    def __init__(self, abbrev, year, o_line, rush_d, pass_d):
        pass


class Year:
    def __init__(self, year, teams):
        self.year = year
        self.teams = teams
        self.stats = {'gamelogs': {}, 'splits': {}, 'fantasy': {}}

    def __repr__(self):
        return 'Year(%s)' % self.year
        
    def __str__(self):
        return 'Player stats for %s while playing for %s' % (self.year, self.teams)


class Player:
    def __init__(self, pid, fn, ln, pos, sal, curr_team):
        self.pid = pid
        self.fn = fn
        self.ln = ln
        self.pos = pos
        self.salary = sal
        self.curr_team = curr_team
        self.years = []

    def __repr__(self):
        return 'Player(%s, %s, %s, %s, %s)' % (self.pid, self.ln, self.fn, self.pos, self.team)

    def get_year(self, year):
        for year_obj in self.years:
            if year_obj.year == year:
                return year_obj

    def write_stats(self, db):
        for year in self.years:
            for stat_type, stats_dict in year.stats.items():
            #for year, stats_dict in v.items():
                filepath = '%s/%s_%s.csv'%(db, stat_type, year.year)
                
                with open(filepath, 'w') as f:
                    if stat_type == 'splits':
                         # write headers if file doesn't exist yet
                        if not path.exists(filepath) or path.getsize(filepath) == 0:
                            f.write('pid, first, last, pos, team, ')
                            for stat_header, splits in stats_dict.items():
                                for split in splits.keys():
                                    f.write('%s_%s, ' % (stat_header, split))
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