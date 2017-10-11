# First test
#
# Problem: both APIs (twitter and the IBridgePy) have
# their own main loop where a function is continuously called upon new data.
# How to merge these?
#
# Easiest solution in my opinion: two threads one running the twitter related stuff
# the other running the broker stuff and a shared producer/consumer queue.
#

# CAREFUL IT IS NOT YET A WORKING EXAMPLE

# Import parallelization libraries
import queue # Nice! this is already thread safe no need to worry about race condition
import threading
import time
import signal
import random


import Sentiment
import Broker





# SETTINGS: PROVIDE ACCESS TOKEN TO TWITTER AND BROKER APIs
# Twitter:
access_token = '853595508366991360-joDmbKrcJbHAtiGNHPkj4G7yLqVWVFU'
access_token_secret = 'vknEzPskeXBMxQhGnSnbaawnn329h0aDM7rEGI1n6TaFx'
consumer_key = 'BYCrKwYk3oFI6r5g3x8mVKTcH'
consumer_secret = 'cpBLW4tqXNGZM43Vpar3H4bUJUIvMEep4NCiulL1oR7rJYVCAQ'
#

#
# MORE SPECIFIC SETTINGS
#
#size of the producer/consumer buffer

buffersize = 10
q = queue.Queue(buffersize)


# setup twitter and threading objects
twitter = Sentiment.TwitterThread(q,access_token, access_token_secret,
                            consumer_key, consumer_secret)
trading = Broker.TradingThread(q)


class ServiceExit(Exception):
    pass

def handler(signum, frame):
    twitter.shutdown()
    broker.shutdown()
    raise ServiceExit

def main():
    #signals!!!
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGTERM, handler)

    #starting the threads
    try:
        twitter.start()
        trading.start()
        while True:
            time.sleep(1000)

    except:
        twitter.shutdown()
        trading.shutdown()
        twitter.join()
        trading.join()


if __name__ == '__main__':
    main()
