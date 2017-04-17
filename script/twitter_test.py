#Import the necessary methods from tweepy library
import tweepy
import textblob

#Variables that contains the user credentials to access Twitter API
access_token = "853595508366991360-joDmbKrcJbHAtiGNHPkj4G7yLqVWVFU"
access_token_secret = "vknEzPskeXBMxQhGnSnbaawnn329h0aDM7rEGI1n6TaFx"
consumer_key = "BYCrKwYk3oFI6r5g3x8mVKTcH"
consumer_secret = "cpBLW4tqXNGZM43Vpar3H4bUJUIvMEep4NCiulL1oR7rJYVCAQ"


#This is a basic listener that just prints received tweets to stdout.
class StreamListener(tweepy.StreamListener):

    def on_status(self, status):
        if hasattr(status, "retweeted_status"):
            return

	#perform sentiment analysis
	blob = textblob.TextBlob(status.text)
	sent = blob.sentiment
        polarity = sent.polarity
        subjectivity = sent.subjectivity
	if (abs(polarity)>0.7):
            print("####################")
            print("polarity: "+str(polarity) + " subjectivity: " +str(subjectivity))
            print(status.text)

    def on_error(self, status):
        if status == 420:
            return False


if __name__ == '__main__':

    #This handles Twitter authetification and the connection to Twitter Streaming API
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)

    stream_listener = StreamListener()
    stream = tweepy.Stream(auth=api.auth, listener=stream_listener)

    #find a lot of drama queens and see when major consent is negative about a certain brand
    #idea: compare week average to day average if change is large act on it
    stream.filter(track=["trump", "donald trump"])

    print 'Donald Trump is gonna make us rich'
