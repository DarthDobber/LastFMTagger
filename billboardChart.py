import billboard
import csv

def getChartData(chartName):
	chart = billboard.ChartData(chartName)
	return chart

def getAlbumInfo(Entry):
	"""
	@param Entry
		Takes a Billboard.Chart Entry object as input
	@returns
		album - album name
		artist - album artist name
		spotifyID - The spotifyID for the Album
		peakpos - The peak chart position for the album
		weeks - Number of weeks the album has been on the chart
		rank - Current ranking of the album on the chart
		change - A string indicating the change in rank from last week (+4, -5, 0) or special value
			Hot Shot Debut - Highest rated album that is new to the chart
			New - New to the chart but not the highest rated new album
			Re-Entry - Fell of the chart but has climbed back into the chart
	"""

	album = Entry.title
	artist = Entry.artist
	spotifyID = Entry.spotifyID
	peakpos = Entry.peakPos
	weeks = Entry.weeks
	rank = Entry.rank
	change = Entry.change

	return rank, album, artist, spotifyID, peakpos, weeks, change

chart = getChartData('americana-folk-albums')

with open('chart.csv', 'a', encoding="utf-8") as csvfile:
	csvwriter = csv.writer(csvfile, delimiter='|', quotechar='^',lineterminator='\n', quoting=csv.QUOTE_MINIMAL)
	csvwriter.writerow(['Chart Date','Rank','Album','Artist','Spotify Album ID','Peak Pos','Weeks','Change'])
	chartDate = chart.date
	while chart.previousDate:
		chartDate = chart.date
		for entry in chart:
			rank, album, artist, spotifyID, peakpos, weeks, change = getAlbumInfo(entry)			
			csvwriter.writerow([chartDate, rank, album, artist, spotifyID, peakpos, weeks, change])
		chart = billboard.ChartData('americana-folk-albums', chart.previousDate)
		chartDate = chart.date



