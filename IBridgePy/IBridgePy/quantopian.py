from IBridgePy import IBCpp
import datetime as dt
import pandas as pd
import numpy as np
import os
from BasicPyLib.Printable import PrintableClass
from BasicPyLib.FiniteState import FiniteStateClass
    
stockList = pd.read_csv(str(os.path.dirname(os.path.realpath(__file__)))+'/all_US_Stocks.csv')
def from_symbol_to_security(s1):
    #print __name__+'::adjust_symbol:'+s1
    if ',' not in s1:
        s1='STK,%s,USD' %(s1,)        
    
    secType = s1.split(',')[0].strip()
    symbol=s1.split(',')[1].strip()     
    currency = s1.split(',')[2].strip()
    if secType=='CASH': # 'CASH.EUR.USD'
        exchange = 'IDEALPRO'
        primaryExchange = 'IDEALPRO'
        return Security(secType=secType, symbol=symbol, currency=currency,
                    exchange=exchange, primaryExchange=primaryExchange)

    elif secType == 'FUT': # 'FUT.ES.USD.201503'
        tmp_df = stockList[(stockList['Symbol'] == symbol)&(stockList['secType'] == 'FUT')]
        if (tmp_df.shape[0] > 0):
            exchange = tmp_df['exchange'].values[0]
            primaryExchange=tmp_df['primaryExchange'].values[0]
        else:
            print 'quantopian::Security: EXIT, Need to specify primaryExchange for symbol=',symbol
            exit()
        expiry=s1.split(',')[3].strip()
        return Security(secType=secType, symbol=symbol, currency=currency,
                    exchange=exchange, primaryExchange=primaryExchange, expiry=expiry)

    elif secType == 'OPT': # OPT.AAPL.USD.20150702.133.P.100
        exchange = 'SMART'
        expiry= s1.split(',')[3].strip()
        strike= s1.split(',')[4].strip()
        right= s1.split(',')[5].strip()
        multiplier= s1.split(',')[6].strip()
        tmp_df = stockList[(stockList['Symbol'] == symbol)&(stockList['secType'] == 'STK')]
        if (tmp_df.shape[0] > 0):
            primaryExchange = tmp_df['primaryExchange'].values[0]
            currency = tmp_df['Currency'].values[0]
        else:
            primaryExchange = 'NYSE'
            currency = 'USD'  
        return Security(secType=secType, symbol=symbol, currency=currency,
                    exchange=exchange, primaryExchange=primaryExchange, expiry=expiry,
                    strike=strike, right=right, multiplier=multiplier)

    elif secType == 'STK':
        exchange = 'SMART'         
        tmp_df = stockList[stockList['Symbol'] == symbol]
        if (tmp_df.shape[0] > 0):
            primaryExchange = tmp_df['primaryExchange'].values[0]
            currency = tmp_df['Currency'].values[0]
        else:
            primaryExchange = 'NYSE'
            currency = 'USD'
        return Security(secType=secType, symbol=symbol, currency=currency,
                    exchange=exchange, primaryExchange=primaryExchange)
    elif secType =='IND':
        exchange='SMART'
        tmp_df = stockList[(stockList['Symbol'] == symbol)&(stockList['secType'] == 'IND')]
        if (tmp_df.shape[0] > 0):
            exchange = tmp_df['primaryExchange'].values[0]
            primaryExchange=tmp_df['primaryExchange'].values[0]
        else:
            print 'quantopian::Security: EXIT, Need to specify primaryExchange for symbol=',symbol
            exit()
        return Security(secType=secType, symbol=symbol, currency=currency,
                    exchange=exchange, primaryExchange=primaryExchange)
    else:
        print __name__+'::Security: EXIT, cannot handle secType=%s' %(secType)
        exit()
      
def from_contract_to_security(one_contract):
    if one_contract.secType=='OPT':
        return from_symbol_to_security(one_contract.secType+','+\
        str(one_contract.symbol)+','+\
        str(one_contract.currency)+','+\
        str(one_contract.expiry)+','+\
        str(one_contract.strike)+','+\
        str(one_contract.right)+','+\
        str(one_contract.multiplier))    
    elif one_contract.secType=='STK' or one_contract.secType=='CASH':
        return from_symbol_to_security(one_contract.secType+','+\
        str(one_contract.symbol)+','+\
        str(one_contract.currency))   
    if one_contract.secType=='FUT':
        return from_symbol_to_security(one_contract.secType+','+\
        str(one_contract.symbol)+','+\
        str(one_contract.currency)+','+\
        str(one_contract.expiry)) 

def create_contract(security):
    #print security.shortprint()
    contract = IBCpp.Contract()
    contract.symbol = security.symbol
    contract.secType = security.secType
    contract.exchange = security.exchange
    contract.currency = security.currency       
    contract.primaryExchange = security.primaryExchange
    contract.includeExpired=security.includeExpired      

    if security.secType=='FUT':
        if security.expiry!='xx':       
            contract.expiry = security.expiry       
    if security.secType=='OPT':
        if security.expiry!='xx':
            contract.expiry= security.expiry
        if security.strike!='xx':    
            contract.strike= float(security.strike)
        if security.right!='xx':
            contract.right= security.right
        if security.multiplier!='xx':
            contract.multiplier= security.multiplier
    return contract 




def same_security(se_1, se_2):
    if se_1.shortprint()==se_2.shortprint():
        return True
    else:
        return False

class OrderBase():
    #use setup function instead of __init__
    def setup(self, orderType,
                 limit_price=None, # defaut price is None to avoid any misformatted numbers
                 stop_price=None,
                 trailing_amount=None,
                 limit_offset=None,
                 tif='DAY'):
        self.orderType=orderType
        self.limit_price=limit_price
        self.stop_price=stop_price
        self.trailing_amount=trailing_amount
        self.limit_offset=limit_offset
        self.tif=tif
        
    def shortprint(self):
        string_output=''
        if self.orderType=='MKT':        
            string_output='MarketOrder,unknown exec price'
        elif self.orderType=='STP':
            string_output='StopOrder, stop_price='+str(self.stop_price)
        elif self.orderType=='LMT':
            string_output='LimitOrder, limit_price='+str(self.limit_price)
        elif self.orderType=='TRAIL LIMIT':
            string_output='TrailStopLimitOrder, stop_price='+str(self.stop_price)\
                            +' trailing_percent='+str(self.trailing_percent)\
                            + ' limit_offset='+str(self.limit_offset)
        else:
            print 'EXIT, quantopian::OrderType::shortprint, cannot handle'+self.orderType
            exit()
        return string_output

class MarketOrder(OrderBase):
    def __init__(self):
        self.setup(orderType='MKT')

class StopOrder(OrderBase):
    def __init__(self,stop_price):
        self.setup(orderType='STP', stop_price=stop_price)

class LimitOrder(OrderBase):
    def __init__(self,limit_price):
        self.setup(orderType='LMT', limit_price=limit_price)
        
class TrailStopLimitOrder(OrderBase):
    def __init__(self, stop_price, trailing_percent, limit_offset):
        self.setup(orderType='TRAIL LIMIT',
                   stop_price=stop_price,
                   trailing_percent=trailing_percent,
                   limit_offset=limit_offset)
         
############## Quantopian compatible data structures
class Security(object):
    def __init__(self,
                secType=None,
                symbol=None,
                currency='USD',
                exchange=None,
                primaryExchange=None,
                expiry=None,
                strike=-1,
                right=None,
                multiplier=-1,
                includeExpired=False,
                sid=-1,
                security_name=None,
                security_start_date=None,
                security_end_date=None):
        self.secType=secType
        self.symbol=symbol
        self.currency=currency
        self.exchange=exchange
        self.primaryExchange=primaryExchange
        self.expiry=expiry
        self.strike=strike
        self.right=right
        self.multiplier=multiplier
        self.includeExpired=includeExpired
        self.sid=sid
        self.security_name=security_name
        self.security_start_date=security_start_date
        self.security_end_date=security_end_date
        
        self.reqRealTimePriceId = -1
        self.reqRealTimeBarsId = -1
        self.reqMarketSnapShotId= -1        
        
    def shortprint(self):
        if self.secType=='STK' or self.secType=='IND':
            string_output=self.secType+','+self.symbol+','+self.currency
        elif self.secType=='FUT':
            string_output='FUTURES,'+self.symbol+','+self.currency+','+str(self.expiry)
        elif self.secType=='CASH':
            string_output='CASH,'+self.symbol+','+self.currency
        elif self.secType=='OPT':
            string_output='OPTION,'+self.symbol+','+self.currency+','+str(self.expiry)+','+str(self.strike)+','+self.right+','+str(self.multiplier)
        else:
            print 'EXIT, quantopian::security::shortprint, cannot handle secType=',self.secType
            exit()
        return string_output
         
'''
stockList = pd.read_csv(str(os.path.dirname(os.path.realpath(__file__)))+'/all_US_Stocks.csv')
class Security(PrintableClass):
    def __init__(self, symbol, sid=0, security_name=None, security_start_date=None,security_end_date=None):
        self.sid=sid
        self.security_name=security_name
        self.security_start_date = None
        self.security_end_date=datetime.datetime.now()
        self.reqRealTimePriceId = -1
        self.reqRealTimeBarsId = -1
        self.reqMarketSnapShotId= -1
        self.secType = symbol.split(',')[0].strip()
        self.symbol=symbol.split(',')[1].strip()     
        self.currency = symbol.split(',')[2].strip()

        if self.secType=='CASH': # 'CASH.EUR.USD'
            self.exchange = 'IDEALPRO'
            self.primaryExchange = 'IDEALPRO'
        elif self.secType == 'FUT': # 'FUT.ES.USD.201503'
            tmp_df = stockList[(stockList['Symbol'] == self.symbol)&(stockList['secType'] == 'FUT')]
            if (tmp_df.shape[0] > 0):
                self.exchange = tmp_df['exchange'].values[0]
                #self.primaryExchange=tmp_df['primaryExchange'].values[0]
                self.primaryExchange=''
            else:
                print 'quantopian::Security: EXIT, Need to specify primaryExchange for symbol=',symbol
                exit()
            self.expiry=symbol.split(',')[3].strip()
        elif self.secType == 'OPT': # OPT.AAPL.USD.20150702.133.P.100
            self.exchange = 'SMART'
            self.expiry= symbol.split(',')[3].strip()
            self.strike= symbol.split(',')[4].strip()
            self.right= symbol.split(',')[5].strip()
            self.multiplier= symbol.split(',')[6].strip()
            tmp_df = stockList[(stockList['Symbol'] == self.symbol)&(stockList['secType'] == 'STK')]
            if (tmp_df.shape[0] > 0):
                self.primaryExchange = tmp_df['primaryExchange'].values[0]
                self.currency = tmp_df['Currency'].values[0]
                self.security_name = tmp_df['Name'].values[0]
                self.security_start_date = tmp_df['IPOyear'].values[0]
            else:
                self.primaryExchange = 'NYSE'
                self.currency = 'USD' 
            
        elif self.secType == 'STK':
            self.exchange = 'SMART'         
            tmp_df = stockList[stockList['Symbol'] == self.symbol]
            if (tmp_df.shape[0] > 0):
                self.primaryExchange = tmp_df['primaryExchange'].values[0]
                self.currency = tmp_df['Currency'].values[0]
                self.security_name = tmp_df['Name'].values[0]
                self.security_start_date = tmp_df['IPOyear'].values[0]
            else:
                self.primaryExchange = 'NYSE'
                self.currency = 'USD'
        elif self.secType =='IND':
            self.exchange='SMART'
            tmp_df = stockList[(stockList['Symbol'] == self.symbol)&(stockList['secType'] == 'IND')]
            if (tmp_df.shape[0] > 0):
                self.exchange = tmp_df['primaryExchange'].values[0]
                self.primaryExchange=tmp_df['primaryExchange'].values[0]
            else:
                print 'quantopian::Security: EXIT, Need to specify primaryExchange for symbol=',symbol
                exit()

        else:
            print __name__+'::Security: EXIT, cannot handle secType=%s' %(self.secType)
            exit()
            
    def shortprint(self):
        if self.secType=='STK' or self.secType=='IND':
            string_output=self.secType+','+self.symbol+','+self.currency
        elif self.secType=='FUT':
            string_output='FUTURES,'+self.symbol+','+self.currency+','+str(self.expiry)
        elif self.secType=='CASH':
            string_output='CASH,'+self.symbol+','+self.currency
        elif self.secType=='OPT':
            string_output='OPTION,'+self.symbol+','+self.currency+','+str(self.expiry)+','+str(self.strike)+','+self.right+','+str(self.multiplier)
        else:
            print 'EXIT, quantopian::security::shortprint, cannot handle secType=',self.secType
            exit()
        return string_output
'''        
        
class ContextClass(PrintableClass):
    def __init__(self, accountCode):
        if type(accountCode)==type((0,0)):
            self.portfolio={}
            for ct in accountCode:
                self.portfolio[ct] = PortofolioClass()       
        else:
            self.portfolio = PortofolioClass()       

class PortofolioClass(PrintableClass):
    def __init__(self, capital_used = 0.0, cash = 0.0, pnl = 0.0, 
                 portfolio_value = 0.0, positions_value = 0.0, returns = 0.0, 
                 starting_cash = 0.0, start_date = dt.datetime.now()):
        self.capital_used = capital_used
        self.cash = cash
        self.pnl = pnl
        self.positions = {}
        self.orderStatusBook= {}
        self.portfolio_value = portfolio_value
        self.positions_value = positions_value
        self.returns = returns
        self.starting_cash = starting_cash
        self.start_date = start_date
        
class PositionClass(PrintableClass):
    def __init__(self, amount=0, cost_basis=0.0, last_sale_price=None, sid=None, accountCode=None):
        self.amount = amount
        self.cost_basis=cost_basis
        self.last_sale_price = last_sale_price
        self.sid=sid
        self.accountCode=accountCode
    def shortprint(self):
        return 'accountCode='+self.accountCode+' share='+str(self.amount)+' cost_basis='+str(self.cost_basis)+' last_sale_price='+str(self.last_sale_price)

        
      
class DataClass(PrintableClass):
    def __init__(self,
                 datetime=dt.datetime(2000,01,01,00,00),
                 price = -1,
                 open_price = -1,
                 close_price = None,
                 high = -1,
                 low =-1,
                 volume = -1):        
        self.datetime=datetime # Quatopian
        self.price=price # Quatopian
        self.size = -1
        self.open_price=open_price # Quatopian
        self.close_price=close_price # Quatopian
        self.high = high # Quatopian
        self.low = low # Quatopian
        self.volume = volume # Quatopian
        self.daily_open_price = -1
        self.daily_high_price = -1
        self.daily_low_price = -1
        self.daily_prev_close_price = -1
        self.bid_price = -1
        self.ask_price = -1
        self.last_price=-1
        self.bid_size = -1
        self.ask_size = -1
        self.hist={}

        # by Hui    
        #self.bid_price_flow = pd.DataFrame()
        #self.ask_price_flow = pd.Series()
        #self.last_price_flow = pd.Series()
        #self.bid_size_flow = pd.Series()
        #self.ask_size_flow = pd.Series()
        #self.last_size_flow = pd.Series()  
        # by Hui
        
        # handle realTimeBars
        #self.realTimeBars=pd.DataFrame(columns=['time','open', 'high', 'low', 'close', 'volume', 'wap', 'count'])
        self.realTimeBars=np.zeros(shape =(0,9))        
        
        # 0 = record_timestamp
        self.bid_price_flow = np.zeros(shape = (0,2))
        self.ask_price_flow = np.zeros(shape = (0,2))
        self.last_price_flow = np.zeros(shape = (0,2))
        self.bid_size_flow = np.zeros(shape = (0,2))
        self.ask_size_flow = np.zeros(shape = (0,2))
        self.last_size_flow = np.zeros(shape = (0,2))        
        # 0 = trade timestamp; 1 = price_last; 2 = size_last; 3 = record_timestamp
        self.RT_volume = np.zeros(shape = (0,4))
        self.contractDetails=None
        
    def update(self,time_input):
        self.datetime=time_input
        self.price=self.hist_bar['close'][-1]
        self.close_price=self.hist_bar['close'][-1]
        self.high=self.hist_bar['high'][-1]
        self.low=self.hist_bar['low'][-1]
        self.volume=self.hist_bar['volume'][-1]
        self.open_price=self.hist_bar['open'][-1]
        self.hist_daily['high'][-1]=self.daily_high_price
        self.hist_daily['low'][-1]=self.daily_low_price
        self.hist_daily['close'][-1]=self.price
    
    def mavg(self, n):
        return pd.rolling_mean(self.hist_daily['close'],n)[-1]

    def returns(self):
        if self.hist['close'][-2]>0.000001:
            return (self.hist_daily['close'][-1]-self.hist_daily['close'][-2])/self.hist_daily['close'][-2]            
        else:
            return 0.0
    def stddev(self, n):
        return pd.rolling_std(self.hist_daily['close'],n)[-1]

    def vwap(self, n):
        return pd.rolling_sum(self.hist_daily['volume']*self.hist_daily['close'],n)/pd.rolling_sum(self.hist_daily['volume'],n)

    def shortprint(self):
        return 'Ask= %f; Bid= %f; Open= %f; High= %f; Low= %f; Close= %f; lastUpdateTime= %s' \
            %(self.ask_price,self.bid_price,self.daily_open_price, self.daily_high_price, self.daily_low_price,self.daily_prev_close_price, str(self.datetime))

class HistClass(object):
    def __init__(self, security=None, period=None,status=None):
        self.status=status
        self.security=security
        self.period=period
        self.hist=pd.DataFrame(columns=['open','high','low','close','volume'])


class OrderClass(object):
    def __init__(self,orderId=None, created=None, parentOrderId = None, stop = None, 
                 limit = None, amount = 0, sid = None, filled = 0,
                 stop_reached = False, limit_reached = False, commission = None,
                 remaining = 0, status = 'na', contract = None, order = None, 
                 orderstate = None, avgFillPrice=0.0):
        self.orderId=orderId
        self.parentOrderId = parentOrderId
        self.created=created
        self.stop=stop
        self.limit=limit
        self.amount=amount
        self.sid=sid
        self.filled=filled
        self.stop_reached=stop_reached
        self.limit_reached=limit_reached
        self.commission=commission
        self.remaining=remaining
        self.status=status
        self.contract=contract
        self.order=order
        self.orderstate=orderstate
        self.avgFillPrice=avgFillPrice
    def shortprint(self):
        if self.avgFillPrice>=0.01:
            tp=self.order.action+' '\
                    +self.order.orderType+' '\
                    +str(self.order.totalQuantity)+' shares of '+from_contract_to_security(self.contract).shortprint()+' at '+str(self.avgFillPrice)
        else:
            if self.stop<1e10 and self.limit>1e10:
                tp=self.order.action+' '\
                        +self.order.orderType+' '\
                        +str(self.order.totalQuantity)+' shares of '+from_contract_to_security(self.contract).shortprint()+' at stop price='+str(self.stop)
            elif self.stop>1e10 and self.limit<1e10:
                tp=self.order.action+' '\
                        +self.order.orderType+' '\
                        +str(self.order.totalQuantity)+' shares of '+from_contract_to_security(self.contract).shortprint()+' at limit price='+str(self.limit)
            elif self.stop<1e10 and self.limit<1e10:
                tp=self.order.action+' '\
                        +self.order.orderType+' '\
                        +str(self.order.totalQuantity)+' shares of '+from_contract_to_security(self.contract).shortprint()+' at limit price='+str(self.limit)+' at stop price='+str(self.stop)
            else:
                tp=self.order.action+' '\
                        +self.order.orderType+' '\
                        +str(self.order.totalQuantity)+' shares of '+from_contract_to_security(self.contract).shortprint()+' at unknown price'
        return tp


class ReqHistClass(object):
    def __init__(self,
                    security=None,
                    barSize=None,
                    goBack=None,
                    endTime=None,
                    whatToShow=None,
                    useRTH=None,
                    formatDate=None):
        self.security=security
        self.barSize=barSize
        '''
        1 sec, 5 secs,15 secs,30 secs,1 min,2 mins,3 mins,5 mins,15 mins,30 mins,1 hour,1 day
        '''        
        self.goBack=goBack
        self.endTime=endTime
        self.whatToShow=whatToShow
        '''
        TRADES,MIDPOINT,BID,ASK,BID_ASK,HISTORICAL_VOLATILITY,OPTION_IMPLIED_VOLATILITY
        '''
        self.useRTH=useRTH
        self.formatDate=formatDate
        
        
class EndCheckListClass(object):
    def __init__(self,
                 status=None,
                 reqId=None,
                 input_parameters=None,
                 return_result=None,
                 waiver=False,
                 reqType=None,
                 security=None):
        self.status=status
        self.reqId=reqId
        self.input_parameters=input_parameters
        self.return_result=return_result
        self.waiver=waiver
        self.reqType=reqType
        self.security=security
        
    def shortprint(self):
        if self.security!=None:
            output=self.reqType+' reqId='+str(self.reqId)+' '+self.security.shortprint()+' '+self.status
        else:
            output=self.reqType+' reqId='+str(self.reqId) +' '+self.status           
        return output

class MachineStateClass(FiniteStateClass):
    def __init__(self):
        self.SLEEP = 'SLEEP'
        self.RUN = 'RUN'
        self.INIT ='INIT'

                        
if __name__ == '__main__':
    #a=create_order('BUY',1000,TrailStopLimitOrder(stop_price=1.23, trailing_percent=0.01, limit_offset=0.001))
    #a=create_order('BUY',1000, MarketOrder())    
    #a=TrailStopLimitOrder(stop_price=1.23, trailing_percent=0.01, limit_offset=0.001)
    #a=symbol('OPT,AAPL,USD,20150702,133,P,100')
    #a=symbol('STK,GLD,USD')    
    #print a.shortprint()
    #print a.primaryExchange
    #print a.__dict__
    #a=MarketOrder()
    #print a.exchange

    ########
    '''
    c=ContextClass(('aaa','bbb'))
    print c.portfolio['aaa'].positions
    c.portfolio['aaa'].positions['aa']=1
    print c.portfolio['aaa'].positions
    print c.portfolio['bbb'].positions
    '''    
    ########
    a=LimitOrder(2355.0)
    print a.__dict__