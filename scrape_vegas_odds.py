from bs4 import BeautifulSoup
import requests

url = 'http://www.vegasinsider.com/nfl/odds/las-vegas/?s=19'
html = requests.get(url)


soup = BeautifulSoup(html.text)
full_tab = soup.find("table", class_="frodds-data-tbl")

for c in full_tab.contents:
	print("new content: %s"%c)
	#print(row)
#tab = full_tab[0].findall("tr")

#for game in tab.
#tab = full_tab.split("<\\td>")
#print(tab[1])
