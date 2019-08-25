from bs4 import BeautifulSoup
import requests
import re

url = 'http://www.vegasinsider.com/nfl/odds/las-vegas/?s=19'
html = requests.get(url)


soup = BeautifulSoup(html.text, features='lxml')
full_tab = soup.find("table", class_="frodds-data-tbl")

rows = []
for row in full_tab.contents:
	rowstr = str(row)
	if re.search("br(.*?)\n", rowstr):
		rows.append(rowstr)
	#print(str)
spreads = []
over_unders = []
for row in rows:
	m = re.search("<br/>(.?\d+½?(o|u)?).*?<br/>(.?\d+½?(o|u)?).*?", row)
	if m:
		if re.search('[ou]', m.group(1)):
			over_unders.append(m.group(1))
			spreads.append(m.group(3))
		else:
			spreads.append(m.group(1))
			over_unders.append(m.group(3))
		#print(m.group(1))
for spread in spreads:
	print('spread: %s' %spread)

for ou in over_unders:
	print('Over/Under: %s' %ou)
