import json
from os import path
from marshmallow import Schema, fields
from classes.PlayerSeason import PlayerSeasonSchema


class Player:
    def __init__(self, fn, ln, pos, curr_team, pid=None, sal=0, age=0.0):
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

    def get_sqs_json(self):
        sqs_dict = {"pid": self.pid, "fn": self.fn, "ln": self.ln, "pos": self.pos, "curr_team": self.curr_team}
        return json.dumps(sqs_dict)

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
