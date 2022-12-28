from marshmallow import Schema, fields


class Game:
    def __init__(self, date=None, home=None, away=None, favorite=None, spread=None, over_under=None):
        self.date = date
        self.home = home
        self.away = away
        self.favorite = favorite
        self.spread = spread
        self.over_under = over_under

    def to_string(self):
        print("date: %s" % self.date)
        print("home: %s" % self.home)
        print("away: %s" % self.away)
        print("favorite: %s" % self.favorite)
        print("spread: %s" % self.spread)
        print("over_under: %s" % self.over_under)


class GameSchema(Schema):
    date = fields.Date()
    home = fields.Boolean()
    away = fields.Boolean()
    favorite = fields.Str()
    spread = fields.Str()
    over_under = fields.Str()
