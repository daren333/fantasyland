from bs4 import BeautifulSoup
import requests
import re


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



url = 'http://www.vegasinsider.com/nfl/odds/las-vegas/?s=19'
html = requests.get(url)


soup = BeautifulSoup(html.text, features='lxml')
full_tab = soup.find("table", class_="frodds-data-tbl")

rows = []
for row in full_tab.contents:
	rowstr = str(row)
	if re.search("br(.*?)\n", rowstr):
		rows.append(rowstr)

games = []

for row in rows:
	game = Game()
	#print(row)
	m = re.search("href.*?/([A-Za-z]*?)-@-([A-Za-z]*?)\.cfm/date/(\d{2}\-\d{2}\-\d{2})#", row)
	if m:
		game.away = m.group(1)
		game.home = m.group(2)
		game.date = m.group(3)

	m = re.search("<br/>(.?\d+½?(o|u)?).*?<br/>(.?\d+½?(o|u)?).*?", row)
	if m:
		if re.search('[ou]', m.group(1)):
			game.over_under = m.group(1)
			game.spread = m.group(3)
			game.favorite = game.away
		else:
			game.spread = m.group(1)
			game.over_under = m.group(3)
			game.favorite = game.home

	games.append(game)

for game in games:
	game.to_string()
