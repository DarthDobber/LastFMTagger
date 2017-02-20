import csv
import mutagen
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TPE1, TIT2, TXXX

def getSpotifyID(mp3file):
	"""
	@params:
		mp3file (str): string representation of a mp3 file.

	@returns:
		spotifyID (str): string representation of the Spotify Track ID
	"""
	tags = ID3(mp3file)

	spotifyID = tags.getall("spotifytrackid")[0]
	return spotifyID

def inChart(spotifyID):
	with open('hot100.csv', 'r', encoding="utf-8") as srcFile:
		csvreader = csv.reader(srcFile, delimiter=',')
		for row in csvreader:
			if row[9] == spotifyID:
				return True
		return False

def getChartValues(spotifyID):
	with open('hot100.csv', 'r', encoding="utf-8") as srcFile:
		csvreader = csv.reader(srcFile, delimiter=',')
		for row in csvreader:
			if row[9] == spotifyID:
				peakPos = row[4]
				weeks = row[6]
				return peakPos, weeks
		return 0, 0

def isTagged(mp3file):
	try:
		tags = ID3(mp3file)
		peakPos = tags.getall('TXXX:hot100peakpos')[0]
		if peakPos is not None:
			return True
		else:
			return False
	except IndexError as I:
		return False

def prependZeros(peakPos, weeks):
	numLisZeros = 3 - len(str(peakPos))
	numPlayZeros = 3 - len(str(weeks))
	list1 = numLisZeros * "0"
	play1 = numPlayZeros * "0"
	list2 = str(list1) + str(peakPos)
	play2 = str(play1) + str(weeks)
	return list2, play2

def setTags(mp3file):
	try:		
		if not isTagged(mp3file):
			audiofile = ID3(mp3file)
			spotifyID = getSpotifyID(mp3file)
			if spotifyID is not None:				
				peakPos, weeks = getChartValues(mp3file)
				peakPos, weeks = prependZeros(peakPos, weeks)
				audiofile.add(TXXX(encoding=3, desc=u'hot100peakpos', text=str(peakPos)))
				audiofile.add(TXXX(encoding=3, desc=u'hot100weeks', text=str(weeks)))
				audiofile.save()
			return peakPos, weeks
		else:
			return 0, 0
	except UnicodeEncodeError as uni:
		print("Unable to encode some part of the filename " + mp3file + "\n" + "Check for special or foreign characters.")
	except Exception as e:
		print("Error occured in setTags with details " + str(e))
		return 0, 0

def setTagsProgress(file_list, update_freq = 1):
	i = 0
	#Total number of files to look at
	l = len(file_list)

	print("Directory Walk Completed, " + str(l) + " files detected, Beginning the tagging process")
	printProgressBar(i, l, prefix = 'Progress:', suffix = 'Complete', length = 50, fill = 'X')
	for mp3 in file_list:
		peakPos, weeks = setTags(mp3)
		i += 1
		if i % update_freq == 0:
			printProgressBar(i, l, prefix = 'Progress:', suffix = 'Complete', length = 50, fill = 'X')
		if listeners != 0:
			logging.info('File %s - Adding Listners: %s Adding Playcount: %s', mp3, peakPos, weeks)
			printProgressBar(i, l, prefix = 'Progress:', suffix = 'Complete', length = 50, fill='X', mp3 = mp3, listeners = listeners, playcount=playcount)
		else:
			logging.info('File %s - NO CHANGE Listners: %s Playcount: %s', mp3, peakPos, weeks)

# Print iterations progress
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', mp3 = '', peakPos = '', weeks = ''):
	"""
	Call in a loop to create terminal progress bar
	@params:
		iteration   - Required  : current iteration (Int)
		total       - Required  : total iterations (Int)
		prefix      - Optional  : prefix string (Str)
		suffix      - Optional  : suffix string (Str)
		decimals    - Optional  : positive number of decimals in percent complete (Int)
		length      - Optional  : character length of bar (Int)
		fill        - Optional  : bar fill character (Str)
		mp3 		- Optional	: mp3 file name (Str)
		listeners 	- Optional	: number of listeners (Str)
		playcount 	- Optional	: number of plays (Str)

	@returns:
		prints a progress bar to the screen unless a MP3 file is being tageged and in that case it will
		return a progress bar with the file, # of listeners and # of plays
	"""
	percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
	filledLength = int(length * iteration // total)
	bar = fill * filledLength + '-' * (length - filledLength)
	print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = '\r')
	# Print File details if a file is updated.
	if mp3 != '':
		print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix))
		print(mp3)
		print("Peak Position: " + peakPos)
		print("Weeks on Charts: " + weeks)
	if iteration == total: 
		print()

if inChart('4jWG3QVhK55wARclW4eomT'):
	p, w = getChartValues('4jWG3QVhK55wARclW4eomT')
	print("Peak Position: " + p + " Number of Weeks: " + w)
