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

#Import the necessary methods from tweepy library


import Queue # Nice! this is already thread safe no need to worry about race condition
import threading
import time
import signal
import random

from IBridgePy.MarketManagerBase import MarketManager
from IBridgePy.Trader_single_account import Trader
from IBridgePy.quantopian import LimitOrder, StopOrder


class TwitterThread(threading.Thread):
    def __init__(self, buf, group=None, target=None, name=None,args=(), kwargs=None, verbose=None):
        super(TwitterThread,self).__init__()
        self.shutdown_flag = threading.Event()
        self.target = target
        self.name = name
        self.buffer = buf

    def run(self):
        # here comes the twitter implementation
        # so far dummy loop
        print("Twitter running")
        while not self.shutdown_flag.is_set():
            time.sleep(1)
            if(not self.buffer.full()):
                x=random.randint(0,10)
                self.buffer.put(x)
                print("put in " + str(x))

        print("Twitter shutdown")



class TradingThread(threading.Thread):
    def __init__(self, buf, group=None, target=None, name=None,args=(), kwargs=None, verbose=None):
        super(TradingThread,self).__init__()
        self.shutdown_flag = threading.Event()
        self.target = target
        self.name = name
        self.buffer = buf


    def run(self):
	print("Trading running")
        while not self.shutdown_flag.is_set():
            time.sleep(1)
            if(not self.buffer.empty()):
                print("got: " + str(self.buffer.get()))
        print("Trading shutdown")
        #here comes the thrading loop
        #set up the Trading API
        #accountCode="DU15124" #need to set own IB account number
        #repBarFreq = 1
        #logLevel="INFO"
        #showTimeZone="US/Eastern"
        #trader = Trader()
        #trader.setup_trader(accountCode = accountCode,
        #    logLevel=LogLevel,
        #    showTimeZone=showTimeZone,
        #    repBarFreq=repBarFreq,
        #    initialize_quantopian=initialize,
        #    handle_data_quantopian = handle_data)


class ServiceExit(Exception):
    pass

def handler(signum, frame):
    raise ServiceExit

def main():
    #size of the producer/consumer buffer
    buffersize = 10
    q = Queue.Queue(buffersize)

    #signals!!!
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGTERM, handler)


    twitter = TwitterThread(q)
    trading = TradingThread(q)

    #starting the threads
    try:
        twitter.start()
        trading.start()
        while True:
            time.sleep(1000)

    except:
        twitter.shutdown_flag.set()
        trading.shutdown_flag.set()

        twitter.join()
        trading.join()


if __name__ == '__main__':
    main()
