import spotify

authToken = "Bearer " + spotify.getSpotifyToken()

def getAlbumID(query):
	result = spotify.searchSpotify(query,type=album)
	return result['albums']['items'][0]['id']

def getAlbumTracks(spotifyID):
	albumTrackURL = "https://api.spotify.com/v1/albums/{id}/tracks".format(id=spotifyID)
	headers = {"Content-Type": "application/x-www-form-urlencoded", "Authorization": authToken}
	params = {"limit": "50"}
	r = requests.get(searchTrackURL, headers=headers, params=params)
	data = json.loads(r.text)
	return data

