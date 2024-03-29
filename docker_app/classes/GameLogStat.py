from marshmallow import Schema, fields


class GameLogStat:
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
        self.ru_td = ru_td
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
        self.punt_ret_tds = punt_tds
        self.fum = fum
        self.fum_lost = fum_lost
        self.off_snap_cnt = off_snap_cnt
        self.off_snap_per = off_snap_per
        self.st_snap_cnt = st_snap_cnt
        self.st_snap_per = st_snap_per



class GameLogStatSchema(Schema):
    date = fields.Date()
    game_num = fields.Int()
    week_num = fields.Int()
    age = fields.Int()
    team = fields.Str()
    away = fields.Boolean() #boolean
    opp = fields.Str()
    game_res = fields.Str()
    rec_tgt = fields.Int()
    recs = fields.Int()
    rec_yds = fields.Int()
    yds_per_rec = fields.Decimal()
    rec_td = fields.Int()
    catch_percent = fields.Str()
    yds_per_tgt = fields.Decimal()
    ru_att = fields.Int()
    ru_yds = fields.Int()
    yds_per_att = fields.Decimal()
    ru_td = fields.Int()
    pa_comp = fields.Int()
    pa_att = fields.Int()
    comp_perc = fields.Str()
    pa_yds = fields.Int()
    pa_td = fields.Int()
    pa_int = fields.Int()
    pa_rate = fields.Str()
    pa_sack = fields.Int()
    pa_yds_per_att = fields.Decimal()
    punt_ret = fields.Int()
    punt_ret_yds = fields.Int()
    punt_yds_per_ret = fields.Decimal()
    punt_ret_tds = fields.Int()
    fum = fields.Int()
    fum_lost = fields.Int()
    off_snap_cnt = fields.Int()
    off_snap_per = fields.Str()
    st_snap_cnt = fields.Int()
    st_snap_per = fields.Str()
