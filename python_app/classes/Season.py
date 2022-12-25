from marshmallow import Schema, fields


class Season:
    def __init__(self, year):
        self.year = year

    def __repr__(self):
        return 'Season(%s)' % self.year


class SeasonSchema(Schema):
    year = fields.Str()
