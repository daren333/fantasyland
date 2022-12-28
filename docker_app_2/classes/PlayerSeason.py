from marshmallow import Schema, fields


class PlayerSeason:
    def __init__(self, year, teams):
        self.year = year
        self.teams = teams
        self.stats = {'gamelogs': {}, 'splits': {}, 'fantasy': {}, 'adv_gamelogs': {}}

    def __str__(self):
        return 'Player stats for %s season while playing for %s' % (self.year, self.teams)

    def __getitem__(self, stat):
        return self.stats[stat]


class PlayerSeasonSchema(Schema):
    year = fields.Str()
    teams = fields.List(fields.Str())
    stats = fields.Dict()