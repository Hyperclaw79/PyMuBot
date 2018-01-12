import tweepy
import requests
from secrets import *
import os
from wit import Wit
witty = Wit('P4PPKDLH7LUJJXN2YCOKNXYM37IJGKV5') # Use my token itself because I designed the appropriate NLP.

auth = tweepy.OAuthHandler(consumer_key, consumer_secret) # Twitter requires all requests to use OAuth for authentication
auth.set_access_token(access_token, access_secret) 
api = tweepy.API(auth) # The api to work with.
SEARCH_URL = "http://api.musixmatch.com/ws/1.1/track.search?page_size=3" + \
    "&page=1&s_track_rating=desc&format=json" + \
    "&apikey={}".format(MM_API_KEY)      # Search in case no artist is inputted.
TRACK_URL = "http://api.musixmatch.com/ws/1.1/track.search?" + \
    "format=json&apikey={}".format(MM_API_KEY) # Get in case artist is provided.

print('Bot is now live.')

# create a class inheriting from the tweepy  StreamListener
class BotStreamer(tweepy.StreamListener):
    # Called when a new status arrives which is passed down from the on_data method of the StreamListener
    def on_status(self, status):
        print('New query detected.')
        username = status.author.screen_name
        status_id = status.id
        message = ' '.join(status.text.split(' ')[1:]).strip()  # Message without mention.
        entities = witty.message(message)['entities']   # Returns detected entities from the message using Wit.AI
        if "bye" in entities:
            api.update_status(status="🤖 Bye @{} 👋".format(username), in_reply_to_status_id=status_id)
        elif "thanks" in entities:
            api.update_status(status="🤖 My pleasure, @{} 👍".format(username), in_reply_to_status_id=status_id)
        elif "greetings" in entities:
            api.update_status(status="\n@{}\n🤖 Hello there!\n".format(username) +
                                "I can get you the details" +
                                " of a song for you. " +
                                "All you gotta do is ask me" +
                                " to search for a song " +
                                "or request a song along" +
                                " with its artist. :)", in_reply_to_status_id=status_id)
        else:
            # Extract song or song & artist
            artist = ""
            if "song" not in entities:
                data = entities["data"][0]["entities"]
                song = data["song"][0]["value"]
                try:
                    artist = data["artist"][0]["value"]
                    artist = artist.replace('by ', '', 1)
                except:
                    try:
                        artist = entities["artist"][0]["value"]
                        artist = artist.replace('by ', '', 1)
                    except:
                        pass
            elif "song" in entities:
                song = entities["song"][0]["value"]
                try:
                    artist = entities["artist"][0]["value"]
                    artist = artist.replace('by ', '', 1)
                except:
                    try:
                        data = entities["data"][0]["entities"]
                        artist = data["artist"][0]["value"]
                        artist = artist.replace('by ', '', 1)
                    except:
                        artist = ''
            content = '@{}'.format(username)
            #try:
                # Function to get a list of dictionaries with song details.
            queue = self.getSongDetails(song=song,artist=artist)
            #except Exception as e:
            #    print(str(e))
            #    api.update_status(status="🤖 @{}, Sorry could not find the song {}. Please retry.".format(username,song), in_reply_to_status_id=status_id)
            media_ids = []
            for song in queue:
                song_name = song['song_name'].replace(' ','')
                try:
                    # For collaboartions and feats.
                    featList = ['feat.', 'feat', 'ft.', 'ft', 'featuring', ',', '&']
                    check = False
                    for feat in featList:
                        if feat in song['artist']:
                            check = True
                            break
                    if check:
                        artistList = song['artist'].replace(" ",'')
                        for feat in featList:
                            artistList = artistList.replace(feat,'ft') # Replace all types of feats with 'ft'
                        artistList = artistList.split('ft') # Now 'ft' becomes the delimiter.
                        tags = ''
                        for artist in artistList:
                            if api.search_users(artist.lower())[0].verified:
                                tags =  tags + '@{} '.format(api.search_users(artist.lower())[0].screen_name)
                        artist_name = "{}({})".format(song['artist'],tags)
                    else:
                        user = api.get_user(song['artist'].replace(' ','').lower())
                        if user.verified:
                            artist_name = "{}(@{})".format(song['artist'], user.screen_name)
                        else:
                            artist_name = song['artist']
                except:
                    artist_name = song['artist']
                    print('User not found on Twitter.') 
                content = content + '\n#{} by {}\nLyrics Link: {}.'.format(song_name,artist_name,song['lyrics'])
                response = requests.get(song['album'],stream=True)
                if response.status_code == 200:
                    filename = '{}.png'.format(song['song_name'])
                    with open(filename, 'wb') as image:
                        for chunk in response:
                            image.write(chunk)  # Download the album art
                    # Upload all the images and store a list of ids.        
                    media_ids.append(api.media_upload(filename).media_id_string)
                    os.remove(filename) # Delete the file.
                else:
                    print("Unable to download image")
            api.update_status(status=content, media_ids=media_ids, in_reply_to_status_id=status_id) # Complete Tweet.
            print('Successfully Tweeted!')
                

    def getSongDetails(self,song,artist):
        elements=[]
        # Append a detials dictionary per song. 
        if artist == "":
            search_url = SEARCH_URL + "&q_track={}".format(song)
            songResponse = requests.get(search_url).json()
            songList = songResponse['message']['body']['track_list']
            if len(songList) > 0:
                    for song in songList:
                        elements.append({'song_name':song['track']['track_name']
                                        , 'artist':song['track']['artist_name']
                                        , 'lyrics':song['track']['track_share_url'].split('?')[0]
                                        , 'album':self.getCover(song['track']['album_name'])})
            else:
                print('Could not find any informationg on ' +
                    song)
        else:
            track_url = TRACK_URL + "&q_track={}&q_artist={}&page_size=1".format(song, artist)
            songResponse = requests.get(track_url).json()
            if songResponse['message']['body'] == []:
                print('Could not find any informationg on ' +
                    song)
                return
            songInfo = songResponse['message']['body']['track_list'][0]['track']
            elements.append({'song_name':songInfo['track_name']
                            , 'artist':songInfo['artist_name']
                            , 'lyrics':songInfo['track_share_url'].split('?')[0]
                            , 'album':self.getCover(songInfo['album_name'])})
        return elements                    
        
    def getCover(self,album):
        # Since musixmatch's coverart is buggy, we can use last.fm's API instead.
        if album != '':
            # Unlimited API calls so feel free to use my key itself.
            url = 'http://ws.audioscrobbler.com/2.0/?method=album.search&album=' + \
                album + '&api_key=fccaa4cad8b877137ef190e7c53aacda&format=json'
            try:
                dic = requests.get(url, headers={"user-agent": "foobar 1.0"}).json()
                cover = dic["results"]["albummatches"]["album"][0]["image"][2]["#text"]
                if cover == '':
                   cover = "https://images.pexels.com/photos/1591/" + \
                    "technology-music-sound-things.jpg?fit=crop&w=640&h=426" 
            except:
                cover = "https://images.pexels.com/photos/1591/" + \
                    "technology-music-sound-things.jpg?fit=crop&w=640&h=426"
        else:
            # A dummy cover in case no cover is found.
            cover = "https://images.pexels.com/photos/1591/" + \
                    "technology-music-sound-things.jpg?fit=crop&w=640&h=426"
        return cover        
                

myStreamListener = BotStreamer()
# Construct the Stream instance
stream = tweepy.Stream(auth, myStreamListener)
# Cares about only the tweets mentioning the bot.
stream.filter(track=['@PyMuBot']) # Rename it with your own bot's screen_name.