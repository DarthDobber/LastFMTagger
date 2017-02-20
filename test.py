import unicodedata
import string

def remove_accents(data):
	return ''.join(x for x in unicodedata.normalize('NFD', data) if x in string.ascii_letters).lower()

string2 = "Mötley Crüe"

string3 = remove_accents(string2)
print(string3)