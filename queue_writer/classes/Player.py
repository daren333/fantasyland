import json


class Player:
    def __init__(self, fn, ln, pos=None, curr_team=None, pid=None, sal=0, age=0.0, url=None):
        self.pid = pid
        self.fn = fn
        self.ln = ln
        self.pos = pos
        self.curr_team = curr_team
        self.salary = sal
        self.age = age
        self.url = url
        self.years = []

    def __repr__(self):
        return 'Player(%s, %s, %s, %s, %s)' % (self.pid, self.ln, self.fn, self.pos, self.curr_team)

    def get_year(self, year):
        for year_obj in self.years:
            if year_obj.year == year:
                return year_obj

    def get_sqs_json(self, full_scrape_enabled):
        sqs_dict = {"pid": self.pid, "fn": self.fn, "ln": self.ln, "age": self.age, "url": self.url, "full_scrape_enabled": full_scrape_enabled}
        return json.dumps(sqs_dict)
