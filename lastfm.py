# -*- coding: latin-1 -*-

import requests
import os
import json
import logging
import mutagen
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TPE1, TIT2, TXXX
import urllib

NAS = "192.168.6.35"
logging.basicConfig(filename='//{NAS}/Cloudstation/lastfmtag.log'.format(NAS=NAS),level=logging.DEBUG,format='%(asctime)s %(levelname)s:%(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
api_key = "f503c65f589e57d58e15a96fab986f7b"
Music_src_dir = "//{NAS}/music/MusicBee2017/Music".format(NAS=NAS)

def getTrackInfo(mp3file):
	"""
	Args:
        mp3file (str): string representation of a mp3 file.

    Returns:
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
		if isTagged(mp3file):
			audiofile = ID3(mp3file)
			audiofile.delall('TXXX:lastfmListeners')
			audiofile.delall('TXXX:lastfmplaycount')
			audiofile.save()
			print("Done with " + mp3file)
	except Exception as e:
		print("Error occured in clearTags with details " + str(e))

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
	"""
	percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
	filledLength = int(length * iteration // total)
	bar = fill * filledLength + '-' * (length - filledLength)
	print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = '\r')
	# Print File details if a file is updated.
	if mp3 != '':
		print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix))
		print(mp3)
		print(listeners)
		print(playcount)
	if iteration == total: 
		print()

file = "c:/temp/moon.mp3"

clearTags(file)
tempdir = "S:\MusicBee2017\Music\Mumford & Sons"
tempdir2 = "S:\MusicBee2017\Music\Georges Bizet"

file_list =[]

print("Walking the Directory... May Take a while depending on the number of files")	
for root, dirs, files in os.walk(Music_src_dir):
	for name in files:
		file, ext = os.path.splitext(name)
		if (ext.lower() == ".mp3"):
			file_list.append(os.path.join(root, name).replace("\\", "/").rstrip())

#Current Iteration Step
i = 0
#Total number of files to look at
l = len(file_list)
#How often to update the progress bar.  Set to 0.5% by default
update_freq = 1#int(l * 0.005)

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
			