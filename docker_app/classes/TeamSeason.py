from marshmallow import Schema, fields
from docker_app.classes.Player import PlayerSchema


class TeamSeason:
    def __init__(self, year, city, name, abbrev, players):
        self.year = year
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


class TeamSeasonSchema(Schema):
    year = fields.Str()
    city = fields.Str()
    name = fields.Str()
    abbrev = fields.Str()
    players = fields.List(fields.Nested(PlayerSchema))
