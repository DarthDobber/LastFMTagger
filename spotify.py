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
import six
import six.moves.urllib.parse as urllibparse
import re
import unicodedata
import makeEnglish3
import string

SPOTIPY_CLIENT_ID ='065d75cdcc7142c8a155166f8466dee9'
SPOTIPY_CLIENT_SECRET ='2ac84e8c76034a58a6dd4657893faa20'

OAUTH_TOKEN_URL = 'https://accounts.spotify.com/api/token'


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
	albumartist = tags.getall("TPE2")[0]
	track = tags.getall("TIT2")[0]
	album = tags.getall("TALB")[0]
	if albumartist == 'Various Artists':
		return artist, track, album
	else:		
		return albumartist, track, album

def getISRC(mp3file):
	tags = ID3(mp3file)

	isrc = tags.getall('TXXX:ISRC')

	return str(isrc)

def _make_authorization_headers(client_id, client_secret):
	auth_header = base64.b64encode(six.text_type(client_id + ':' + client_secret).encode('ascii'))
	return {'Authorization': 'Basic %s' % auth_header.decode('ascii')}

def getSpotifyToken():
	"""Gets client credentials access token """
	payload = { 'grant_type': 'client_credentials'}

	headers = _make_authorization_headers(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET)

	response = requests.post(OAUTH_TOKEN_URL, data=payload,
		headers=headers, verify=True)
	if response.status_code is not 200:
		raise SpotifyOauthError(response.reason)
	token_info = response.json()
	return token_info['access_token']

authToken = "Bearer " + getSpotifyToken()

def searchspotify(query, type="track"):
	#query = urllib.parse.quote_plus(str(query))
	#type = urllib.parse.quote_plus(str(type))
	searchTrackURL = "https://api.spotify.com/v1/search"
	params = {"q": query, "type": type}
	headers = {"Content-Type": "application/x-www-form-urlencoded", "Authorization": authToken}
	r = requests.get(searchTrackURL, headers=headers, params=params)
	data = json.loads(r.text)
	return data

def getAlbumTracks(albumid):
	albumid = urllib.parse.quote_plus(str(albumid))
	searchTrackURL = "https://api.spotify.com/v1/albums/{id}/tracks".format(id=albumid)
	headers = {"Content-Type": "application/x-www-form-urlencoded", "Authorization": authToken}
	r = requests.get(searchTrackURL, headers=headers)
	data = json.loads(r.text)
	return data

def getSpotifyTrackInfo(trackid):
	trackid = urllib.parse.quote_plus(str(trackid))
	TrackInfoURL = "https://api.spotify.com/v1/tracks/{id}".format(id=trackid)
	headers = {"Content-Type": "application/x-www-form-urlencoded", "Authorization": authToken}
	r = requests.get(TrackInfoURL, headers=headers)
	data = json.loads(r.text)
	return data

def getfirstAlbumID(searchData):
	return searchData['albums']['items'][0]['id']

def getSpotifyAudioFeatures(spotifyid):
	audiofeatureURL = "https://api.spotify.com/v1/audio-features/{id}".format(id=spotifyid)
	headers = {"Content-Type": "application/x-www-form-urlencoded", "Authorization": authToken}
	r = requests.get(audiofeatureURL, headers=headers)
	data = json.loads(r.text)
	acoustic = (data['acousticness']) * 100
	energy = (data['energy']) * 100
	mood = (data['valence']) * 100
	dance = (data['danceability']) * 100
	tempo = (data['tempo'])
	return acoustic, energy, mood, dance, tempo



def prependZeros(acoustic, energy, mood, dance, tempo):
	numAcousticZeros = 5 - len(str(acoustic))
	numEnergyZeros = 5 - len(str(energy))
	numMoodZeros = 5 - len(str(mood))
	numDanceZeros = 5 - len(str(dance))
	numTempoZeros = 5 - len(str(tempo))

	acoustic1 = numAcousticZeros * "0"
	energy1 = numEnergyZeros * "0"
	mood1 = numMoodZeros * "0"
	dance1 = numDanceZeros * "0"
	tempo1 = numTempoZeros * "0"

	acoustic2 = str(acoustic1) + str(acoustic)
	energy2 = str(energy1) + str(energy)
	mood2 = str(mood1) + str(mood)
	dance2 = str(dance1) + str(dance)
	tempo2 = str(tempo1) + str(tempo)

	return acoustic2, energy2, mood2, dance2, tempo2

def prependZeroSingle(string):
	numZeros = 3 - len(str(string))

	string1 = numZeros * "0"

	string2 = str(string1) + str(string)

	return string2

def setSpotifyID(mp3file):
	try:		
		if not isTagged(mp3file):
			audiofile = ID3(mp3file)
			artist, track, album = getTrackInfo(mp3file)
			artist, track, album = str(artist).replace(" ", "tacochina"), str(track).replace(" ", "tacochina"), str(album).replace(" ", "tacochina")
			artist, track, album = str(artist).replace("&", "and"), str(track).replace("&", "and"), str(album).replace("&", "and")

			print(track)

			# artist = re.sub('[\W_]+', '', artist)
			# track = re.sub('[\W_]+', '', track)
			# album = re.sub('[\W_]+', '', album)

			artist = remove_accents(artist)
			track = remove_accents(track)
			album = remove_accents(album)

			artist, track, album = str(artist).replace("tacochina", " "), str(track).replace("tacochina", " "), str(album).replace("tacochina", " ")

			print(track)

			artist = urllib.parse.quote_plus(str(artist))
			track = urllib.parse.quote_plus(str(track))
			album = urllib.parse.quote_plus(str(album))
			queryString = "track:{track} artist:{artist}".format(track=track, artist=artist)
			print(queryString)
			results = searchspotify(queryString)
			print(results)
			spotifyid = results['tracks']['items'][0]['id']
			audiofile.add(TXXX(encoding=3, desc=u'spotifytrackid', text=str(spotifyid)))
			audiofile.save()
			return spotifyid
		else:
			return 0
	except UnicodeEncodeError as uni:
		print("Unable to encode some part of the filename " + mp3file + "\n" + "Check for special or foreign characters.")
	except Exception as e:
		print("Error occured in setTags with details " + str(e))
		try:
			artist, track, album = getTrackInfo(mp3file)
			with open("errorfiles.txt", "a") as f:
				f.write("Artist: " + artist + " Track: " + " Album: " + album)

			isrc = getISRC(mp3file)
			queryString = "isrc:{isrc}".format(isrc=isrc)
			results = searchspotify(queryString)
			spotifyid = results['tracks']['items'][0]['id']
			audiofile.add(TXXX(encoding=3, desc=u'spotifytrackid', text=str(spotifyid)))
			audiofile.save()
			return spotifyid
		except Exception as e:
			print("Failed lookup by ISRC")
		return 0

def setSpotifyStats(mp3file):
	try:		
		if not isTaggedstats(mp3file):
			audiofile = ID3(mp3file)

			spotifyid = audiofile.getall('TXXX:spotifytrackid')[0]

			spotifyid = urllib.parse.quote_plus(str(spotifyid))

			popularity = prependZeroSingle(getSpotifyTrackInfo(spotifyid)['popularity'])

			print("Popularity: " + popularity)

			acoustic, energy, mood, dance, tempo = getSpotifyAudioFeatures(spotifyid)

			acoustic1, energy1, mood1, dance1, tempo1 = prependZeros(round(acoustic,1), round(energy,1), round(mood,1), round(dance,1), round(tempo,1))

			if not doesTagExist('spotifyenergy', mp3file):
				audiofile.add(TXXX(encoding=3, desc=u'spotifyenergy', text=str(energy1)))
			if not doesTagExist('spotifyacoustic', mp3file):
				audiofile.add(TXXX(encoding=3, desc=u'spotifyacoustic', text=str(acoustic1)))
			if not doesTagExist('spotifymood', mp3file):
				audiofile.add(TXXX(encoding=3, desc=u'spotifymood', text=str(mood1)))
			if not doesTagExist('spotifydance', mp3file):
				audiofile.add(TXXX(encoding=3, desc=u'spotifydance', text=str(dance1)))
			if not doesTagExist('spotifytempo', mp3file):
				audiofile.add(TXXX(encoding=3, desc=u'spotifytempo', text=str(tempo1)))
			if not doesTagExist('spotifypopularity', mp3file):
				audiofile.add(TXXX(encoding=3, desc=u'spotifypopularity', text=str(popularity)))
			audiofile.save()
			return acoustic1, energy1, mood1, dance1, tempo1
		else:
			return 0, 0, 0, 0, 0
	except UnicodeEncodeError as uni:
		print("Unable to encode some part of the filename " + mp3file + "\n" + "Check for special or foreign characters.")
	except Exception as e:
		print("Error occured in setSpotifyStats with details " + str(e))
		return 0, 0, 0, 0, 0

def isTaggedstats(mp3file):
	try:
		tags = ID3(mp3file)
		trackid = tags.getall('TXXX:spotifypopularity')[0]
		if trackid is not None:
			return True
		else:
			return False
	except IndexError as I:
		return False

def doesTagExist(tagname, mp3file):
	try:
		tags = ID3(mp3file)
		thistag = tags.getall('TXXX:' + tagname)[0]
		if thistag is not None:
			return True
		else:
			return False
	except IndexError as I:
		return False


def isTagged(mp3file):
	try:
		tags = ID3(mp3file)
		trackid = tags.getall('TXXX:spotifytrackid')[0]
		if trackid is not None:
			return True
		else:
			return False
	except IndexError as I:
		return False

def clearTags(mp3file):
	try:
		audiofile = ID3(mp3file)
		audiofile.delall('TXXX:spotifyenergy')
		audiofile.delall('TXXX:spotifyacoustic')
		audiofile.delall('TXXX:spotifymood')
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

def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', mp3 = '', acoustic = '', energy = '', mood = '', dance = '', tempo = ''):
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
		print("Acoustic: " + str(acoustic))
		print("Energy: " + str(energy))
		print("Mood: " + str(mood))
		print("Dance: " + str(dance))
		print("Tempo: " + str(tempo))
	if iteration == total: 
		print()

def printProgressBarID(iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', mp3 = '', spotifyid = ''):
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
		print("SpotifyID: " + str(spotifyid))
	if iteration == total: 
		print()

def setTagsProgress(file_list, update_freq = 1):
	i = 0
	#Total number of files to look at
	l = len(file_list)

	print("Directory Walk Completed, " + str(l) + " files detected, Beginning the tagging process")
	printProgressBar(i, l, prefix = 'Progress:', suffix = 'Complete', length = 50, fill = 'X')
	for mp3 in file_list:
		acoustic, energy, mood, dance, tempo = setSpotifyStats(mp3)
		i += 1
		if i % 2000 ==0:
			global authToken
			authToken = "Bearer " + getSpotifyToken()
		if i % update_freq == 0:
			printProgressBar(i, l, prefix = 'Progress:', suffix = 'Complete', length = 50, fill='X', mp3 = mp3, acoustic = acoustic, energy = energy, mood = mood, dance = dance, tempo = tempo)
		else:
			#logging.info('File %s - NO CHANGE Listners: %s Playcount: %s', mp3, listeners, playcount)
			pass

def setIDProgress(file_list, update_freq = 1):
	i = 0
	#Total number of files to look at
	l = len(file_list)

	print("Directory Walk Completed, " + str(l) + " files detected, Beginning the tagging process")
	printProgressBarID(i, l, prefix = 'Progress:', suffix = 'Complete', length = 50, fill = 'X')
	for mp3 in file_list:
		spotifyid = setSpotifyID(mp3)
		i += 1
		if i % 2000 ==0:
			global authToken
			authToken = "Bearer " + getSpotifyToken()
		if i % update_freq == 0:
			printProgressBar(i, l, prefix = 'Progress:', suffix = 'Complete', length = 50, fill = 'X')
		if spotifyid != 0:
			printProgressBarID(i, l, prefix = 'Progress:', suffix = 'Complete', length = 50, fill='X', mp3 = mp3, spotifyid = spotifyid)
		else:
			#logging.info('File %s - NO CHANGE Listners: %s Playcount: %s', mp3, listeners, playcount)
			pass

def remove_accents(data):
	bob = data.replace('+', 'and')
	bob = bob.replace('-', 'tacochina')
	bob = ''.join(x for x in unicodedata.normalize('NFD', bob) if x in string.ascii_letters).lower()
	return bob

def remove_featured_artists(string):
	artist = string
	if 'feat' in string:
		artist, featartist = string.split('feat')
	if 'with' in string:
		artist, featartist = string.split('with')
	return artist


def main():

	artist="Alan Jackson"
	track="Chasin that Neon Rainbow"

	artist = urllib.parse.quote_plus(str(artist))
	track = urllib.parse.quote_plus(str(track))

	queryString = "track:{track} artist:{artist}".format(track=track, artist=artist)
	results = searchspotify(queryString)
	print(results['tracks']['items'][0]['id'])



	# # albumresults = searchspotify("The Very Best of SuperTramp", "album")
	# # tryid = getfirstAlbumID(albumresults)
	# # tracks = getAlbumTracks(tryid)
	# # print(tracks.keys())
	# # print(tracks['total'])
	# # for track in tracks['items']:
	# # 	print("Track # " + str(track['track_number']) + " Name: " + track['name'])
	# # trackinfo = getTrackInfo(tracks['items'][0]['id'])
	# # print(trackinfo.keys())
	# # print(trackinfo['external_ids'])

	filelist = getFileList("S:\MusicBee2017\Music")
	setTagsProgress(filelist)

	# one, two, three = getSpotifyAudioFeatures("6zPXWXS2pZwSsIM7f08Mg5")
	# acoustic, energy, mood = prependZeros(round(one,1), round(two,1), round(three,1))
	# print(acoustic)
	# print(energy)
	# print(mood)
			

if __name__ == "__main__":
	main()