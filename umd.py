import requests
import os
import json
import logging
import mutagen
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TPE1, TIT2, TXXX
import urllib
import sys
import time
import datetime as dt
import base64
import six
import six.moves.urllib.parse as urllibparse
import re
import unicodedata
import string
from stringSanitize import remove_accents, remove_stopwords, remove_featured_artists, remove_punc, remove_paren
from bs4 import BeautifulSoup


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

def searchUMD(artist, title):
	#query = urllib.parse.quote_plus(str(query))
	#type = urllib.parse.quote_plus(str(type))
	searchTrackURL = "http://www.umdmusic.com/default.asp"
	params = {"Lang": "English", "Chart": "D", "ChDay": "", "ChMonth": "", "ChYear": "", "ChBand": artist, "ChSong": title}
	headers = {'user-agent': 'Mozilla/5.0 (Android 4.4; Mobile; rv:41.0) Gecko/41.0 Firefox/41.0'}
	r = requests.get(searchTrackURL, headers=headers, params=params)
	if r.status_code == 200:
		html = r.content
		soup = BeautifulSoup(html, "lxml")
	return soup

def parseSoup(soup):
	valuelist = []
	for value in soup.find_all("td", align="center", style="font-size:10pt;font-family:Arial"):
		valuelist.append(value.text)
	if len(valuelist) == 4:
		entryDate = valuelist[0]
		entryPos = valuelist[1]
		peakPos = valuelist[2]
		weeks = valuelist[3]
	else:
		entryDate = 0
		entryPos = 0
		peakPos = 0
		weeks = 0
	return entryDate, entryPos, peakPos, weeks



print(parseSoup(searchUMD('AC/DC', 'Back In Black')))