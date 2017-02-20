import string
import unicodedata

def remove_accents(string1):
	newstring = string1.replace('+', 'and')
	newstring = newstring.replace('-', 'tacochina')
	newstring = ''.join(x for x in unicodedata.normalize('NFD', newstring) if x in string.ascii_letters).lower()
	return newstring

def remove_stopwords(string):
	stop = ['the', 'of', 'a', 'band', 'are', 'that', 'has', 'live', 'and', 'is']
	string1 = ""
	for i in string.lower().split():
		if i not in stop:
			string1 = string1 + i + " "
	return string1

def remove_featured_artists(string):
	artist = string
	if 'feat' in string:
		artist, featartist = string.split('feat')
	if 'with' in string:
		artist, featartist = string.split('with')
	return artist

def remove_punc(string1):
	string2 = ""
	for c in string.punctuation:
		string2 = string1.replace(c,"")
	return string2

def remove_paren(string):
	start = string.find( '(' )
	end = string.find( ')' )
	result = ""
	sep = ""
	if start != -1 and end != -1:
		sep = string[start+1:end]
		one, two = string.split(sep)
		result = one + two
	else:
		result = string
	return result