# -*- coding: utf-8 -*-
"""
Module MarketManager

"""
import time, pytz
import datetime as dt
from BasicPyLib import small_tools
from IBridgePy.quantopian import MachineStateClass
                 
class MarketManager(object):
    """ 
    Market Manager will run trading strategies according to the market hours.
    It should contain a instance of IB's client, properly initialize the connection
    to IB when market starts, and properly close the connection when market closes
    inherited from __USEasternMarketObject__. 
    USeasternTimeZone and run_according_to_market() are inherited
    init_obj(), run_algorithm() and destroy_obj() should be overwritten
    """    
    def __init__(self, trader, port=7496, clientId=1):
        self.port=port
        self.clientId=clientId
        self.aTrader=trader
        self.marketState = MachineStateClass()
        self.marketState.set_state(self.marketState.SLEEP)
        self.aTrader.log.notset(__name__+'::__init__')
           
    ######### this part do real trading with IB
    def init_obj(self):
        """
        initialzation of the connection to IB
        updated account
        """   
        self.aTrader.connect("", self.port, self.clientId) # connect to server
        self.aTrader.log.debug(__name__ + ": " + "Connected to IB, port = " + 
        str(self.port) + ", ClientID = " + str(self.clientId))  
        time.sleep(1)
                    
    def destroy_obj(self):
        """
        disconnect from IB and close log file
        """
        self.aTrader.disconnect()
        self.aTrader.log.close_log()
        self.aTrader.log.info(__name__+'::destroy_obj: Disconnect, Market is closed now.')
        
    def run_according_to_market(self, start='9:30', end='16:00'):
        """
        run_according_to_market() will check if market is open every one second
        if market opens, it will first initialize the object and then run the object
        if market closes, it will turn the marketState back to "sleep"
        """

        # print OPEN/CLOSED immediately after run this function
        time_now=pytz.timezone(small_tools.localTzname()).localize(dt.datetime.now())
        self.aTrader.log.info(__name__+'::run_accounding_to_market: Start to run_according_to_market')
        if small_tools.if_market_is_open(time_now, start=start, end=end)==False:
            self.aTrader.log.error(__name__+'::run_accounding_to_market: Market is CLOSED now')
        else:
            self.aTrader.log.error(__name__+'::run_accounding_to_market: Market is OPEN now')
  
        while(True):
            # if the market is open, run aTrader
            # if the market is close, disconnect from IB server, and sleep
            time_now=pytz.timezone(small_tools.localTzname()).localize(dt.datetime.now())
            if small_tools.if_market_is_open(time_now, start=start, end=end):            
                if self.marketState.is_state(self.marketState.SLEEP):
                # if the market just open, initialize the trader
                    #self.aTrader.setup_trader()
                    self.init_obj()
                    self.aTrader.initialize_Function()
                    self.marketState.set_state(self.marketState.RUN)
                else:
                # process messages from server every 0.1 second
                    self.aTrader.reqCurrentTime()
                    self.aTrader.processMessages()
                    self.aTrader.repeat_Function()
                    time.sleep(0.1)
            else:
            # if the market is closed, disconnect from IB server and sleep.
            # during sleep, check if the market is open on every second
                if self.marketState.is_state(self.marketState.SLEEP):               
                    time.sleep(1)   
                elif self.marketState.is_state(self.marketState.RUN):
                    self.marketState.set_state(self.marketState.SLEEP)                             
                    self.destroy_obj()                    
            
    def run(self):
        self.init_obj()
        self.aTrader.initialize_Function()
        while(True):
            self.aTrader.reqCurrentTime()
            self.aTrader.processMessages()
            self.aTrader.repeat_Function()
            time.sleep(0.1)

    def runOnEvent(self):
        self.init_obj()
        if self.aTrader.repBarFreq%5!=0:
            print __name__+'::runOnEvent: cannot handle reqBarFreq=%i' %(self.aTrader.repBarFreq,)
            exit()
        self.aTrader.initialize_Function()
        while self.aTrader.realtimeBarTime==None:
            time.sleep(0.2)
            self.aTrader.reqCurrentTime()
            self.aTrader.processMessages()
            self.aTrader.log.debug(__name__+'::runOnEvent: waiting realtimeBarTime is called back')
            
        while self.aTrader.realtimeBarTime.second!=55:
        # when the realtimeBarTime.second==55 comes in, the IB server time.second==0
        # start the handle_data when second ==0
        # Set realtimeBarCount=0
        # realtimeBarCount+=1 when a new bar comes in
            time.sleep(0.2)
            self.aTrader.reqCurrentTime()
            self.aTrader.processMessages()
        self.aTrader.realtimeBarCount=0
        self.aTrader.event_Function()
        
        while(True):
            self.aTrader.reqCurrentTime()
            self.aTrader.processMessages()
            self.aTrader.event_Function()
            time.sleep(1)

    def test_run(self,start_time, end_time, time_interval):
        from BasicPyLib import small_tools
        from BasicPyLib.get_yahoo_data import get_yahoo_data
        import datetime as dt
        if type(self.aTrader.accountCode)==type((0,0)):
            for ct in self.aTrader.context.portfolio:
                self.aTrader.context.portfolio[ct].cash=100000.00
                self.aTrader.context.portfolio[ct].portfolio_value = 100000.00
                self.aTrader.context.portfolio[ct].positions_value = 0.0
        else:
            self.aTrader.context.portfolio.cash=100000.00
            self.aTrader.context.portfolio.portfolio_value = 100000.00
            self.aTrader.context.portfolio.positions_value = 0.0

        self.aTrader.initialize_Function()
        
        if hasattr(self.aTrader.context, 'security')==False:
            self.aTrader.context.security=self.aTrader.symbol('SPY')
        else:
            pass
            
        for ct in self.aTrader.data:
            #tp=get_yahoo_data([ct.symbol], dt.date(2016,1,1), dt.date.today(), add_postfix=False)       
            tp=get_yahoo_data([ct.symbol], start_time, end_time, add_postfix=False)       
            self.aTrader.data[self.aTrader.symbol(ct.symbol)].hist['1Day']=tp      

    
        print __name__+'::test_run: Start to simulate from',start_time,' to ', end_time
        start_time=small_tools.dt_to_timestamp(start_time)
        end_time=small_tools.dt_to_timestamp(end_time)
        for sTime in range(int(start_time), int(end_time), int(time_interval)):
            time_now=dt.datetime.fromtimestamp(float(sTime), tz = pytz.timezone('US/Eastern'))
            if small_tools.if_market_is_open(time_now)==True:
                self.aTrader.currentTime(sTime)
                tp= self.aTrader.stime.astimezone(pytz.timezone('US/Eastern'))
                tp=tp.replace(tzinfo=None)
                for ct in self.aTrader.data:
                    price=small_tools.simulate_spot_price(tp, self.aTrader.data[self.aTrader.symbol(ct.symbol)].hist['1Day'])        
                    self.aTrader.data[self.aTrader.symbol(ct.symbol)].ask_price=price
                    self.aTrader.data[self.aTrader.symbol(ct.symbol)].bid_price=price
                    self.aTrader.data[self.aTrader.symbol(ct.symbol)].last_price=price
    
                for ct in self.aTrader.context.portfolio.orderStatusBook:
                    if self.aTrader.context.portfolio.orderStatusBook[ct].status!='Filled':
                        self.aTrader.order_status_monitor(ct, 'Filled')
                self.aTrader.processMessages()
                self.aTrader.update_positions_value() # simulate to calculate position values for display purposes
                #print __name__+'::test_run: Simulate sever time=',time_now.strftime("%Y-%m-%d %H:%M %Z")
                self.aTrader.handle_data_quantopian(self.aTrader.context,self.aTrader.data)
                self.aTrader.stime_previous=self.aTrader.stime
            
if __name__=='__main__':                            
    from IBridgePy import IBCpp 
    class test(IBCpp.IBClient):
        pass
    c=test()
    d=MarketManager(c)
    d.init_obj()
          