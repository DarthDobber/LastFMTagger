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
import base64

authstring = b'065d75cdcc7142c8a155166f8466dee9:2ac84e8c76034a58a6dd4657893faa20'

def getTrackInfo(mp3file):
	"""
	@params:
		mp3file (str): string representation of a mp3 file.

	@returns:
		artist (str): string representation of the Artist ID3 ("TPE1") value stored in the mp3 file.
		track (str): string representation of the Title ID3 ("TIT2") value stored in the mp3 file. 
	"""
	tags = ID3(mp3file)

	artist = tags.getall("TPE1")[0]
	track = tags.getall("TIT2")[0]
	return artist, track

def getSpotifyToken():
	authtoken = base64.b64encode(authstring)
	headers = {"Content-Type": "application/x-www-form-urlencoded", "Authorization": "Basic " + str(authtoken)}
	print(str(authtoken))
	params = {"grant_type": "client_credentials"}
	getAccessTokenURL = "https://accounts.spotify.com/api/token"

	r = requests.post(getAccessTokenURL, headers=headers, data=params)
	#json.loads turns the json response into a dictionary
	data = json.loads(r.text)
	return data

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
		print("Removed tags from " + mp3file)
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

	print(getSpotifyToken())
			

if __name__ == "__main__":
	main()