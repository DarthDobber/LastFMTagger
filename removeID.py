import os
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TPE1, TIT2, TXXX


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

def clearTags(filelist):
	try:
		for mp3 in filelist:
			audiofile = ID3(mp3)
			id = audiofile.getall('TXXX:spotifytrackid')[0]
			if id =='4sk0nOr8BsLZmRpqQO9BDc':
				print(id)			
				audiofile.delall('TXXX:spotifytrackid')
				audiofile.save()
				print("Removed tags from " + mp3)
	except Exception as e:
		print("Error occured in clearTags with details " + str(e))



filelist = getFileList("S:\MusicBee2017\Music")
clearTags(filelist)