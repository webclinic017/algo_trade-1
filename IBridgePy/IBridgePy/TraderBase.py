import datetime as dt
import time, pytz
import pandas as pd
import BasicPyLib.simpleLogger as simpleLogger
from IBridgePy.quantopian import DataClass, ContextClass
from IBridgePy.IBAccountManager import IBAccountManager

class Trader(IBAccountManager):
    """
    TickTraders are IBAccountManager too, so TickTraders inherits from IBAccountManager.
    """
    daily_run_once=True   
    realtimeBarCount=0
    realtimeBarTime=None #MarketManagerBase use it to calculate the starting point
    
    def setup_trader(self,
                    accountCode='All',
                    logLevel='INFO',
                    showTimeZone='US/Pacific',
                    maxSaveTime=1800,
                    waitForFeedbackinSeconds=30,
                    repeat=3,
                    repBarFreq=1,
                    handle_data_quantopian=None, # a function name is passed in.
                    initialize_quantopian=None): # a function name is passed in.

        """
        initialize the IBAccountManager. We don't do __init__ here because we don't
        want to overwrite parent class IBCpp.IBClient's __init__ function
        stime: system time obtained from IB
        maxSaveTime: max timeframe to be saved in price_size_last_matrix for TickTrader

        """ 
        self.accountCode=accountCode
        self.context = ContextClass(accountCode)           
        self.logLevel=logLevel
        self.showTimeZone=pytz.timezone(showTimeZone)
        self.maxSaveTime=maxSaveTime
        self.initialize_quantopian=initialize_quantopian
        self.waitForFeedbackinSeconds=waitForFeedbackinSeconds
        self.repeat=repeat
        self.handle_data_quantopian=handle_data_quantopian
        self.repBarFreq=repBarFreq 

        self.stime = None
        self.stime_previous=None
            
        self.nextId = 0         # nextValidId, all request will use the same series
                
        # Prepare log
        self.todayDateStr = time.strftime("%Y-%m-%d")
        self.log = simpleLogger.SimpleLoggerClass(filename = 
        'TraderLog_' + self.todayDateStr + '.txt', logLevel = self.logLevel)    
        self.log.notset(__name__+'::setup_trader')        

        
    def initialize_Function(self):
        self.log.notset(__name__+'::initialize_Function')
        self.data={}
        self.request_data(
                  positions  = True,
                  accountDownload= self.accountCode,
                  reqAccountSummary= False,
                  reqAllOpenOrders =True,
                  nextValidId= True,
                  waitForFeedbackinSeconds=self.waitForFeedbackinSeconds,
                  repeat=self.repeat)
        self.initialize_quantopian(self.context) # function name was passed in.
        self.log.info('####    Starting to initialize trader    ####')              
        self.display_all()             
        self.log.info('####    Initialize trader COMPLETED    ####') 
        self.stime_previous=dt.datetime.now() 
        
    def event_Function(self):
        self.log.notset(__name__+'::event_Function')
        if self.realtimeBarCount==0:
            self.handle_data_quantopian(self.context,self.data) 
            self.realtimeBarCount+=1
        if self.repBarFreq/5+1==self.realtimeBarCount:
            self.realtimeBarCount=0
 
    def repeat_Function(self):
        self.log.notset(__name__+'::repeat_Function')
        
        #print self.stime
        if self.repBarFreq==1 :
            if self.stime.second!=self.stime_previous.second:
                self.handle_data_quantopian(self.context,self.data)
        elif self.repBarFreq==60:
            if self.stime.second==0 and self.stime_previous.second!=0:
                self.handle_data_quantopian(self.context,self.data)
        elif self.repBarFreq==3600*24:
            if self.stime.hour==6 and self.stime.minute==0:
                if self.daily_run_once==True:
                    self.daily_run_once=False
                    for ct in self.data:
                        self.data[ct].daily_open_price = None
                        self.data[ct].daily_high_price = None
                        self.data[ct].daily_low_price = None
                        self.data[ct].daily_prev_close_price = None
                    self.log.info('Reset daily OHLC to None')
                    self.request_data(
                                      positions  = None,
                                      accountDownload= None,
                                      nextValidId= None,
                                      historyData= [(x,'1 day','20 D') for x in self.data],
                                      realTimePrice = None,
                                      contractDetails= None,
                                      marketSnapShot=None,
                                      waiver=None,
                                      waitForFeedbackinSeconds=30,
                                      repeat=5)
                        
            if self.stime.hour==6 and self.stime.minute==1:
                if self.daily_run_once==False:
                    self.daily_run_once=True
                    self.log.info('Reset daily_run_once')
            self.handle_data_quantopian(self.context,self.data)
        else:
            self.log.error(__name__+'::repeat_Function: cannot handle repBarFreq=%i' %(self.repBarFreq,))
            exit()
        self.stime_previous=self.stime
