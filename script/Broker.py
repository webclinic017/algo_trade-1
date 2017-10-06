# Import broker related stuff

import sys
sys.path.append("../IBridgePy/")

from IBridgePy.MarketManagerBase import MarketManager
from IBridgePy.Trader_single_account import Trader
from IBridgePy.quantopian import LimitOrder, StopOrder

import Queue
import threading
import time
import signal
import random









# Broker consumer queue: executes trades issued by Twitter sentiment analysis
class TradingThread(threading.Thread):
    def __init__(self, buf, group=None, target=None, name=None,args=(), kwargs=None, verbose=None):
        super(TradingThread,self).__init__()
        self.shutdown_flag = threading.Event()
        self.target = target
        self.name = name
        self.buffer = buf

    #initialize function for trading
    def __initialize__(context):
        pass

    def handle_data(context, data):
        request_data(historyData=[(symbol('SPY'), '1 min', '1 D'),(symbol('AAPL'), '1 day', '10 D')  ])
        print data[symbol('SPY')].hist['1 min'].tail()
        print data[symbol('AAPL')].hist['1 day'].tail()
        exit()
        

    def run(self):
        print("Trading running")
        #here comes the thrading loop
        #set up the Trading API
        accountCode="DU228387" #need to set own IB account number
        repBarFreq = 1
        logLevel="INFO"
        showTimeZone="US/Eastern"
        trader = Trader()
        trader.setup_trader(accountCode = accountCode,
            logLevel=LogLevel,
            showTimeZone=showTimeZone,
            repBarFreq=repBarFreq,
            initialize_quantopian=__initialize__,
            handle_data_quantopian = handle_data)
        print("Trading shutdown")

    def shutdown(self):
        self.shutdown_flag.set()