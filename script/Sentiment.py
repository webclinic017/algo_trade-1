# Import Twitter & sentiment analysis related stuff
import tweepy
import textblob

import Queue
import threading
import time
import signal
import random


# Twitter sentiment analysis implementation

class StreamListener(tweepy.StreamListener):
    def __init__(self):
        super(StreamListener,self).__init__()
        self.shutdown_flag = threading.Event()

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



class TwitterThread(threading.Thread):
    def __init__(self, buf, access_token, access_token_secret,consumer_key, consumer_secret,group=None, target=None, name=None,args=(), kwargs=None, verbose=None):
        super(TwitterThread,self).__init__()
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.target = target
        self.name = name
        self.buffer = buf
        self.auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        self.auth.set_access_token(access_token, access_token_secret)
        self.api = tweepy.API(self.auth)
        self.stream_listener = StreamListener()
        self.stream = tweepy.Stream(auth=self.api.auth, listener=self.stream_listener)


    def run(self):
        # here comes the twitter implementation
        # so far dummy loop
        print("Twitter running")

        #find a lot of drama queens and see when major consent is negative about a certain brand
        #idea: compare week average to day average if change is large act on it
        self.stream.filter(track=["google"])

        print("Twitter shutdown")

    def shutdown(self):
        self.stream.disconnect()