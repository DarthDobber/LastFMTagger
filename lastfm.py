# -*- coding: latin-1 -*-

import requests
import os
import json
import logging
import mutagen
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TPE1, TIT2, TXXX
import urllib
import sys
from optparse import OptionParser
import time
import datetime as dt

# NAS = "192.168.6.35"
# logging.basicConfig(filename='//{NAS}/Cloudstation/lastfmtag.log'.format(NAS=NAS),level=logging.DEBUG,format='%(asctime)s %(levelname)s:%(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
# api_key = "f503c65f589e57d58e15a96fab986f7b"
# Music_src_dir = "//{NAS}/music/MusicBee2017/Music".format(NAS=NAS)

def getTrackInfo(mp3file):
	"""
	@params:
		mp3file (str): string representation of a mp3 file.

	@returns:
		artist (str): string representation of the Artist ID3 ("TPE1") value stored in the mp3 file.
		track (str): string representation of the Title ID3 ("TIT2") value stored in the mp3 file. 
		mbid (str): string representation of the MusicBrainz ID value stored in the mp3 file, if it does not exist return '0'
	"""
	tags = ID3(mp3file)

	artist = tags.getall("TPE1")[0]
	track = tags.getall("TIT2")[0]
	mbid = get_mbid(mp3file)
	return artist, track, mbid

def get_mbid(file):
	try:
		f = mutagen.File(file, easy=True)
		mbid = f.get('musicbrainz_trackid', '')[0]
		if len(mbid) < 2:
			mbid = '0'            
		return mbid
	except Exception as e:
		print("Error occured in getmbid with details " + str(e))
		return '0'

def getLastFMbyMBID(mbid):
	mbid = urllib.parse.quote_plus(str(mbid))
	getTrackURL1 = "http://ws.audioscrobbler.com/2.0/?method=track.getInfo&api_key={api_key}&mbid={mbid}&format=json".format(api_key=api_key, mbid=mbid)
	headers = {"Content-Type": "application/x-www-form-urlencoded"}
	r = requests.post(getTrackURL1, headers=headers)

	data = json.loads(r.text)
	if 'track' in data:
		listeners = data['track']['listeners']
		playcount = data['track']['playcount']
		return listeners, playcount
	elif 'error' in data:
		return "error", "error"
	else:
		return 0, 0


def getLastFMbyTrack(artist, track):
	artist = urllib.parse.quote_plus(str(artist))
	track = urllib.parse.quote_plus(str(track))
	print("Artist is " + artist + " And Track is " + track)
	getTrackURL2 = "http://ws.audioscrobbler.com/2.0/?method=track.getInfo&api_key={api_key}&artist={artist}&track={track}&format=json".format(api_key=api_key, artist=artist, track=track)
	headers = {"Content-Type": "application/x-www-form-urlencoded"}
	r = requests.post(getTrackURL2, headers=headers)
	data = json.loads(r.text)
	if 'track' in data:
		listeners = data['track']['listeners']
		playcount = data['track']['playcount']
		return listeners, playcount
	else:
		return 0, 0


def getListenersandPlays(mp3file):
	try:	
		artist, track, mbid = getTrackInfo(mp3file)
		print("lookup by track and artist")
		listeners, playcount = getLastFMbyTrack(artist, track)
			
		return listeners, playcount
	except Exception as e:
		print("Error occured in JSON Request with details " + str(e))
		logging.error('URL error with artist: %s track %s ', artist, track)
		return 0, 0

def prependZeros(listeners, playcount):
	numLisZeros = 10 - len(str(listeners))
	numPlayZeros = 10 - len(str(playcount))
	list1 = numLisZeros * "0"
	play1 = numPlayZeros * "0"
	list2 = str(list1) + str(listeners)
	play2 = str(play1) + str(playcount)
	return list2, play2

def setTags(mp3file):
	try:		
		if not isTagged(mp3file):
			audiofile = ID3(mp3file)
			listeners, playcount = getListenersandPlays(mp3file)
			listeners, playcount = prependZeros(listeners, playcount)
			audiofile.add(TXXX(encoding=3, desc=u'lastfmListeners', text=str(listeners)))
			audiofile.add(TXXX(encoding=3, desc=u'lastfmplaycount', text=str(playcount)))
			audiofile.save()
			return listeners, playcount
		else:
			return 0, 0
	except UnicodeEncodeError as uni:
		print("Unable to encode some part of the filename " + mp3file + "\n" + "Check for special or foreign characters.")
	except Exception as e:
		print("Error occured in setTags with details " + str(e))
		return 0, 0

def isTagged(mp3file):
	try:
		tags = ID3(mp3file)
		playcount = tags.getall('TXXX:lastfmplaycount')[0]
		if str(playcount).startswith('00'):
			return True
		else:
			return False
	except IndexError as I:
		return False

def clearTags(mp3file):
	try:
		audiofile = ID3(mp3file)
		audiofile.delall('TXXX:lastfmListeners')
		audiofile.delall('TXXX:lastfmplaycount')
		audiofile.save()
		print("Done with " + mp3file)
	except Exception as e:
		print("Error occured in clearTags with details " + str(e))

def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")

# Print iterations progress
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', mp3 = '', listeners = '', playcount = ''):
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
		print("Listeners: " + listeners)
		print("Plays: " + playcount)
	if iteration == total: 
		print()

def getFileList(dir):
	file_list =[]
	try:
		print("Walking the Directory... May Take a while depending on the number of files")	
		for root, dirs, files in os.walk(dir):
			for name in files:
				file, ext = os.path.splitext(name)
				if (ext.lower() == ".mp3"):
					file_path = os.path.join(root, name).replace("\\", "/").rstrip()
					file_list.append(file_path)
		return file_list

	except Exception as e:
		print(str(e))
		#print("Check Directory string")
		sys.exit()

def getFileListQuick(dir, age=24):
	file_list =[]
	now = dt.datetime.now()
	ago = now-dt.timedelta(hours=age)

	try:
		print("Walking the Directory... May Take a while depending on the number of files")	
		for root, dirs, files in os.walk(dir):
			for name in files:
				file, ext = os.path.splitext(name)
				if (ext.lower() == ".mp3"):
					file_path = os.path.join(root, name).replace("\\", "/").rstrip()
					modified_time = dt.datetime.fromtimestamp(os.path.getmtime(file_path))
					if modified_time > ago:
						file_list.append(file_path)
		return file_list

	except Exception as e:
		print(str(e))
		#print("Check Directory string")
		continue

def setTagsProgress(file_list, update_freq = 1):
	i = 0
	#Total number of files to look at
	l = len(file_list)

	print("Directory Walk Completed, " + str(l) + " files detected, Beginning the tagging process")
	printProgressBar(i, l, prefix = 'Progress:', suffix = 'Complete', length = 50, fill = 'X')
	for mp3 in file_list:
		listeners, playcount = setTags(mp3)
		i += 1
		if i % update_freq == 0:
			printProgressBar(i, l, prefix = 'Progress:', suffix = 'Complete', length = 50, fill = 'X')
		if listeners != 0:
			logging.info('File %s - Adding Listners: %s Adding Playcount: %s', mp3, listeners, playcount)
			printProgressBar(i, l, prefix = 'Progress:', suffix = 'Complete', length = 50, fill='X', mp3 = mp3, listeners = listeners, playcount=playcount)
		else:
			logging.info('File %s - NO CHANGE Listners: %s Playcount: %s', mp3, listeners, playcount)


def main():
	parser = OptionParser(usage="usage: %prog [options] filename",
						  version="%prog 1.0")
	parser.add_option("-d", "--dir",
					  action="store",
					  dest="dir",
					  help="Directory containing MP3 files to be tagged")
	parser.add_option("-f", "--file",
					  action="store",
					  dest="file",
					  help="MP3 File to be processed",)
	parser.add_option("-c", "--clear",
					  action="store_true",
					  dest="clear",
					  default=False,
					  help="Delete all Last.FM Listeners and Playcount tags")
	parser.add_option("-q", "--quick",
					  action="store_true",
					  dest="quick",
					  default=False,
					  help="Run a quick scan, only looking at files modified in the last X Hours (default 24 hours), use -a to specify a different time period")
	parser.add_option("-a", "--age",
					  action="store",
					  type="int",
					  default=24,
					  dest="age",
					  help="Number of hours old files you would like to look at, only used with -q")
	parser.add_option("-u", "--update",
					  action="store_true",
					  dest="update",
					  default=False,
					  help="Updates the Last.FM Listeners and Playcount tags for all files")
	(options, args) = parser.parse_args()

	if options.dir and options.file:
		parser.error("options -d and -f are mutually exclusive")
		sys.exit()

	if options.clear and options.update:
		parser.error("options -c and -u are mutually exclusive")
		sys.exit()

	#Quick Scan Conditions
	if options.dir:
		if options.quick:
			if options.update:
				#update Directory files using quick scan
				update_list = getFileListQuick(options.dir, age=options.age)
				for file in update_list:
					#clearing Tags already present
					clearTags(file)
					# #Current Iteration Step
				setTagsProgress(update_list)


			elif options.clear:
				#Clear Directory Tags using quick scan
				#Ensuring the user wants to delete the tags
				confirmation = query_yes_no("Are you sure you want to clear all tags for all files in " + options.dir + " for the last " + str(options.age) + " hours?")
				if confirmation:
					clear_list = getFileListQuick(options.dir, age=options.age)
					for file in clear_list:
						clearTags(file)
				else:
					sys.exit()
			else:
				#Quick Scan that updates tags of non-tagged files in last X hours
				update_list = getFileListQuick(options.dir, age=options.age)
				setTagsProgress(update_list)

		#Full Directory Operations
		elif options.clear and not options.quick:
			#Clear All Tags within a directory
			confirmation = query_yes_no("Are you sure you want to clear all tags for all files in " + options.dir + "?")
			if confirmation:
				clear_list = getFileList(options.dir)
				for file in clear_list:
					clearTags(file)
			else:
				sys.exit()
		elif options.update and not options.quick:
			#Update All Tags within a directory
			update_list = getFileList(options.dir)
			for file in update_list:
				clearTags()
			setTagsProgress(update_list)
		else:
			#Update Tags of files that are empty
			update_list = getFileList(options.dir)
			setTagsProgress(update_list)

	# if options.dir and options.quick and options.update:
	# 	file_list = getFileListQuick(options.dir, age=options.quick)
	# 	for file in file_list:
	# 		print(file)
	# elif options.dir and options.update:
	# 	file_list = getFileList(options.dir)
	# 	for file in file_list:
	# 		print(file)
	# elif options.dir and options.clear:
	# 	Confirmation = query_yes_no("Are you sure you want to clear all tags for " + options.dir)
	# 	if Confirmation:
	# 		print("Confirmed")
	# elif 

	# elif options.dir:
	# 	file_list = getFileList(options.dir)
	# 	for file in file_list:
	# 		print(file)



		

	if options.file:
		print("Do Something")


	# file = "c:/temp/moon.mp3"

	# clearTags(file)
	# tempdir = "S:\MusicBee2017\Music\Mumford & Sons"
	# tempdir2 = "S:\MusicBee2017\Music\Georges Bizet"



	# #Current Iteration Step
	# i = 0
	# #Total number of files to look at
	# l = len(file_list)
	# #How often to update the progress bar.  Set to 0.5% by default
	# update_freq = 1#int(l * 0.005)

	# print("Directory Walk Completed, " + str(l) + " files detected, Beginning the tagging process")
	# printProgressBar(i, l, prefix = 'Progress:', suffix = 'Complete', length = 50, fill = 'X')
	# for mp3 in file_list:
	# 	listeners, playcount = setTags(mp3)
	# 	i += 1
	# 	if i % update_freq == 0:
	# 		printProgressBar(i, l, prefix = 'Progress:', suffix = 'Complete', length = 50, fill = 'X')
	# 	if listeners != 0:
	# 		logging.info('File %s - Adding Listners: %s Adding Playcount: %s', mp3, listeners, playcount)
	# 		printProgressBar(i, l, prefix = 'Progress:', suffix = 'Complete', length = 50, fill='X', mp3 = mp3, listeners = listeners, playcount=playcount)
	# 	else:
	# 		logging.info('File %s - NO CHANGE Listners: %s Playcount: %s', mp3, listeners, playcount)
			

if __name__ == "__main__":
	main()