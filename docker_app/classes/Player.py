from os import path
from marshmallow import Schema, fields
from docker_app.classes.PlayerSeason import PlayerSeasonSchema


class Player:
    def __init__(self, pid, fn, ln, pos, curr_team, age=0.0, sal=0):
        self._id = pid
        self.pid = pid
        self.fn = fn
        self.ln = ln
        self.pos = pos
        self.curr_team = curr_team
        self.salary = sal
        self.age = age
        self.years = []

    def __repr__(self):
        return 'Player(%s, %s, %s, %s, %s)' % (self.pid, self.ln, self.fn, self.pos, self.curr_team)

    def get_year(self, year):
        for year_obj in self.years:
            if year_obj.year == year:
                return year_obj


class PlayerSchema(Schema):
    _id = fields.Str()
    pid = fields.Str()
    fn = fields.Str()
    ln = fields.Str()
    pos = fields.Str()
    curr_team = fields.Str()
    salary = fields.Str()
    age = fields.Int()
    years = fields.List(fields.Nested(PlayerSeasonSchema()))
