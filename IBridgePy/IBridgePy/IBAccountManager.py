# -*- coding: utf-8 -*-
'''
There is a risk of loss in stocks, futures, forex and options trading. Please
trade with capital you can afford to lose. Past performance is not necessarily 
indicative of future results. Nothing in this computer program/code is intended
to be a recommendation to buy or sell any stocks or futures or options or any 
tradable securities. 
All information and computer programs provided is for education and 
entertainment purpose only; accuracy and thoroughness cannot be guaranteed. 
Readers/users are solely responsible for how they use the information and for 
their results.

If you have any questions, please send email to IBridgePy@gmail.com
'''
import time
import pandas as pd
import numpy as np
import pytz

from IBridgePy.quantopian import Security, PositionClass, \
create_contract, MarketOrder, OrderClass, same_security, \
DataClass,from_contract_to_security,EndCheckListClass, ReqHistClass, from_symbol_to_security
from IBridgePy import IBCpp
import datetime as dt 

# https://www.interactivebrokers.com/en/software/api/apiguide/tables/tick_types.htm
MSG_TABLE = {0: 'bid size', 1: 'bid price', 2: 'ask price', 3: 'ask size', 
             4: 'last price', 5: 'last size', 6: 'daily high', 7: 'daily low', 
             8: 'daily volume', 9: 'close', 14: 'open'}

class IBAccountManager(IBCpp.IBClient):
    """
    IBAccountManager manages the account, order, and historical data information
    from IB. These information are needed by all kinds of traders.
    """         
                        
    def error(self, errorId, errorCode, errorString):
        """
        only print real error messages, which is errorId < 2000 in IB's error
        message system, or program is in debug mode
        """
        if errorCode in [2119,2104,2108,2106, 2107, 2103]:
            pass
        else:
            self.log.error(__name__ + ": " + 'errorId = ' + str(errorId) + 
            ', errorCode = ' + str(errorCode) + ', error message: ' + errorString)
            if errorCode == 504:
                self.log.error(__name__ + ": " + 'errorId = ' + str(errorId) + 
                ', errorCode = ' + str(errorCode) + ', error message: ' + errorString)
                exit()
            
    def currentTime(self, tm):
        """
        IB C++ API call back function. Return system time in datetime instance
        constructed from Unix timestamp using the showTimeZone from MarketManager
        """
        #self.log.notset(__name__+'::currentTime')
        self.stime = dt.datetime.fromtimestamp(float(tm), tz = pytz.utc)                                       
        self.log.notset(__name__+'::currentTime'+str(self.stime))
                                                    
    def roundToMinTick(self, price, minTick=0.01):
        """
        for US interactive Brokers, the minimum price change in US stocks is
        $0.01. So if the user made calculations on any price, the calculated
        price must be round using this function to the minTick, e.g., $0.01
        """
        if price<0.0:
            self.log.error(__name__ + '::roundToMinTick price: EXIT, negtive price ='+str(price))
            exit()            
        rounded=int(price / minTick) * minTick
        self.log.debug(__name__ + '::roundToMinTick price: round ' + str(price) +'to ' + str(rounded))
        return rounded
    ######################   SUPPORT ############################33

    def set_timer(self):
        """
        set self.timer_start to current time so as to start the timer
        """
        self.timer_start = dt.datetime.now()
        self.log.notset(__name__ + "::set_timer: " + str(self.timer_start))
        
    def check_timer(self, limit = 1):
        """
        check_timer will check if time limit exceeded for certain
        steps, including: updated positions, get nextValidId, etc
        """
        self.log.notset(__name__+'::check_timer:')
        timer_now = dt.datetime.now()
        change = (timer_now-self.timer_start).total_seconds()
        if change > limit: # if time limit exceeded
            self.log.error(__name__+ '::check_timer: request_data failed after '+str(limit)+' seconds')
            self.log.error(__name__+'::check_timer: notDone items in self.end_check_list')           
            tp=self.search_in_end_check_list(notDone=True, output_version='list')
            for ct in tp:
                self.log.error(tp[ct].shortprint())            
            return True
        else:
            return None
  
    ############### Next Valid ID ################### 
    def nextValidId(self, orderId):
        """
        IB API requires an orderId for every order, and this function obtains
        the next valid orderId. This function is called at the initialization 
        stage of the program and results are recorded in startingNextValidIdNumber,
        then the orderId is track by the program when placing orders
        """        
        self.log.debug(__name__ + '::nextValidId: Id = ' + str(orderId))
        self.nextId = orderId
        ct=self.search_in_end_check_list(reqType='nextValidId', output_version='location', allowToFail=True)
        if ct!=None:
            self.end_check_list[ct].status='Done'
                                                  
    ################ Real time tick price data #########
    def update_DataClass(self, security, name, value=None, ls_info=None):
        self.log.notset(__name__+'::update_DataClass')  
        if ls_info==None and value!=None:
            if (self.maxSaveTime > 0 and value > 0):
                currentTimeStamp = time.mktime(dt.datetime.now().timetuple())
                newRow = [currentTimeStamp, value]
                tmp = getattr(self.data[security], name)
                tmp = np.vstack([tmp, newRow])
                # erase data points that go over the limit
                if (currentTimeStamp - tmp[0, 0]) > self.maxSaveTime:
                    tmp = tmp[1:,:]
                setattr(self.data[security], name, tmp)
        elif ls_info!=None and value==None:
            if name=='realTimeBars':
                if len(ls_info)!=8:
                    self.log.error(__name__+'::update_DataClass: ls_info does not matach data structure of '+name)
                    exit()
            currentTimeStamp = time.mktime(dt.datetime.now().timetuple())
            newRow = [currentTimeStamp]+ls_info
            tmp = getattr(self.data[security], name)
            tmp = np.vstack([tmp, newRow])
            # erase data points that go over the limit
            if (currentTimeStamp - tmp[0, 0]) > self.maxSaveTime:
                tmp = tmp[1:,:]
            setattr(self.data[security], name, tmp)
            
        
    def tickPrice(self, tickerId, tickType, price, canAutoExecute):
        """
        call back function of IB C++ API. This function will get tick prices
        """
        self.log.notset(__name__+'::tickPrice:'+str(tickerId)+' '+str(tickType)+' '+str(price))
        security=self.search_tickerId_in_Qdata_return_security(tickerId)
        if security==None:
            self.log.error(__name__+'::tickPrice: %i %s %f' %(tickerId,tickType,price) )
        else:    
            self.data[security].datetime=self.stime
            if tickType==1: #Bid price
                self.data[security].bid_price = price
                self.update_DataClass(security, 'bid_price_flow', price)
                if security.secType=='CASH':
                    self.data[security].last_price = price   
                    # won't work for multiple accounts
                    #ct=self.search_security_in_positions(security)
                    #self.context.portfolio.positions[ct].last_sale_price = price

            elif tickType==2: #Ask price
                self.data[security].ask_price = price
                self.update_DataClass(security, 'ask_price_flow', price)
                # won't work for multiple accounts
                #ct=self.search_security_in_positions(security)
                #self.context.portfolio.positions[ct].last_sale_price = price
    
            elif tickType==4: #Last price
                self.data[security].last_price = price
                self.update_DataClass(security, 'last_price_flow', price)
                # won't work for multiple accounts
                #ct=self.search_security_in_positions(security)
                #self.context.portfolio.positions[ct].last_sale_price = price
    
            elif tickType==6: #High daily price
                self.data[security].daily_high_price=price
                self.data[security].high=price
                #print security.symbol,'daily_high_price',price,canAutoExecute,self.stime   
            elif tickType==7: #Low daily price
                self.data[security].daily_low_price=price
                self.data[security].low=price
                #print security.symbol,'daily_low_price',price,canAutoExecute,self.stime   
            elif tickType==9: #last close price
                self.data[security].daily_prev_close_price = price
                self.data[security].close_price = price
            elif tickType == 14:#open_tick
                self.data[security].daily_open_price = price
            #print 'tickprice',security.symbol,'open_price',price,canAutoExecute,self.stime   


    def tickSize(self, tickerId, tickType, size):
        """
        call back function of IB C++ API. This function will get tick size
        """
        self.log.notset(__name__+'::tickSize: ' + str(tickerId) + ", " + MSG_TABLE[tickType]
        + ", size = " + str(size))
        security=self.search_tickerId_in_Qdata_return_security(tickerId)
        if security == None:
            return 0
        self.data[security].datetime=self.stime
        if tickType == 0: # Bid Size
            self.data[security].bid_size = size
            #self.update_DataClass(security, 'bid_size_flow', size)
        if tickType == 3: # Ask Size
            self.data[security].ask_size = size
            #self.update_DataClass(security, 'ask_size_flow', size)  
        if tickType == 3: # Last Size
            self.data[security].size = size
            #self.update_DataClass(security, 'last_size_flow', size)
        if tickType == 8: # Volume
            self.data[security].volume = size
                    
    def tickString(self, tickerId, field, value):
        """
        IB C++ API call back function. The value variable contains the last 
        trade price and volume information. User show define in this function
        how the last trade price and volume should be saved
        RT_volume: 0 = trade timestamp; 1 = price_last, 
        2 = size_last; 3 = record_timestamp
        """
        self.log.notset(__name__+'::tickString: ' + str(tickerId)
         + 'field=' +str(field) + 'value='+str(value))
        #print tickerId, field

        security=self.search_tickerId_in_Qdata_return_security(tickerId)
        if security == None:
            #self.log.debug('cannot find it')
            return 0
       
        if str(field)=='RT_VOLUME':
            currentTime = self.stime
            valueSplit = value.split(';')
            if valueSplit[0]!='':
                priceLast = float(valueSplit[0])
                timePy = float(valueSplit[2])/1000
                sizeLast = float(valueSplit[1])
                currentTimeStamp = time.mktime(dt.datetime.now().timetuple())
                self.log.notset(__name__ + ':tickString, ' + str(tickerId) + ", " 
                + str(security.symbol) + ', ' + str(priceLast)
                + ", " + str(sizeLast) + ', ' + str(timePy) + ', ' + str(currentTime))
                # update price
                newRow = [timePy, priceLast, sizeLast, currentTimeStamp]
                #newRow = [timePy, priceLast, sizeLast]
                priceSizeLastSymbol = self.data[security].RT_volume
                priceSizeLastSymbol = np.vstack([priceSizeLastSymbol, newRow])
                # erase data points that go over the limit
                if (timePy - priceSizeLastSymbol[0, 0]) > self.maxSaveTime:
                    #print timePy, priceSizeLastSymbol[0, 0]
                    #print 'remove'
                    priceSizeLastSymbol = priceSizeLastSymbol[1:,:]
                self.data[security].RT_volume = priceSizeLastSymbol
                #print self.data[security].RT_volume
            #except:
            #    self.log.info(__name__+'::tickString: ' + str(tickerId)
            #     + 'field=' +str(field) + 'value='+str(value))
                 # priceLast = float(valueSplit[0])
                 #ValueError: could not convert string to float:
            #    exit()
                
    def historicalData(self, reqId, date, price_open, price_high, price_low, price_close, volume, barCount, WAP, hasGaps):
        """
        call back function from IB C++ API
        return the historical data for requested security
        """
        self.log.notset(__name__+'::historialData: reqId='+str(reqId)+','+date)
        loc=self.search_in_end_check_list(reqId=reqId, reqType='historyData')
             
        if 'finished' in str(date):
            self.end_check_list[loc].status='Done'       
            
            #if the returned security is in self.data, put the historicalData into self.data
            # else, add the new security in self.data
            sec=self.end_check_list[loc].security
            barSize=self.end_check_list[loc].input_parameters.barSize
            self.data[self.search_security_in_Qdata(sec)].hist[barSize]=self.end_check_list[loc].return_result               
            self.log.debug(__name__ + '::historicalData: finished req hist data for '+sec.shortprint())
            self.log.debug('First line is ')
            self.log.debug(str(self.end_check_list[loc].return_result.iloc[0]))
            self.log.debug('Last line is ')
            self.log.debug(str(self.end_check_list[loc].return_result.iloc[-1]))
            
        else:
            if self.end_check_list[loc].input_parameters.formatDate==1:
                if '  ' in date:                       
                    date=dt.datetime.strptime(date, '%Y%m%d  %H:%M:%S') # change string to datetime                        
                else:
                    date=dt.datetime.strptime(date, '%Y%m%d') # change string to datetime
            else:
                if len(date)>9:
                    date = dt.datetime.fromtimestamp(float(date), tz = pytz.utc)
                    date = date.astimezone(self.showTimeZone)
                    #date = dt.datetime.strftime(date, '%Y-%m-%d  %H:%M:%S %Z')                                      
                else:
                    date=dt.datetime.strptime(date, '%Y%m%d') # change string to datetime
                    date=pytz.utc.localize(date)
                    date = date.astimezone(self.showTimeZone)
                    #date = dt.datetime.strftime(date, '%Y-%m-%d %Z')                                      

            if date in self.end_check_list[loc].return_result.index:
                self.end_check_list[loc].return_result['open'][date]=price_open
                self.end_check_list[loc].return_result['high'][date]=price_high
                self.end_check_list[loc].return_result['low'][date]=price_low
                self.end_check_list[loc].return_result['close'][date]=price_close
                self.end_check_list[loc].return_result['volume'][date]=volume
            else:
                newRow = pd.DataFrame({'open':price_open,'high':price_high,
                                       'low':price_low,'close':price_close,
                                       'volume':volume}, index = [date])
                self.end_check_list[loc].return_result=self.end_check_list[loc].return_result.append(newRow)

    def realtimeBar(self, reqId, time, price_open, price_high, price_low, price_close, volume, wap, count):
        """
        call back function from IB C++ API
        return the historical data for requested security
        """
        self.log.notset(__name__+'::realtimeBar: reqId='+str(reqId)+','+str(dt.datetime.fromtimestamp(time)))
        security=self.search_tickerId_in_Qdata_return_security(reqId)
        if security==None:
            self.log.error(__name__+'::realtimeBar: unexpected reqId = %i' %(reqId,) )
            exit()                
        self.update_DataClass(security, 'realTimeBars', ls_info=[time, price_open, price_high, price_low, price_close, volume, wap, count])
        self.realtimeBarCount+=1 
        self.realtimeBarTime=dt.datetime.fromtimestamp(time)   
                     
        
        
    ############## Account management ####################
    def updateAccountTime(self, tm):
        self.log.notset(__name__+'::updateAccountTime:'+str(tm))
        
    def accountSummaryEnd(self, reqId):
        self.log.debug(__name__ + '::accountSummaryEnd:CANNOT handle' + str(reqId))
        exit()

    def execDetails(self, reqId, contract, execution):
        self.log.notset(__name__+'::execDetails: DO NOTHING reqId'+str(reqId))     

    def commissionReport(self,commissionReport):
        self.log.notset(__name__+'::commissionReport: DO NOTHING'+str(commissionReport))        

        
    def positionEnd(self):
        self.log.notset(__name__+'::positionEnd: all positions recorded')
        ct=self.search_in_end_check_list(reqType='positions')
        self.end_check_list[ct].status='Done'
           
    def tickSnapshotEnd(self, reqId):
        self.log.notset(__name__+'::tickSnapshotEnd: '+str(reqId))
        ct=self.search_in_end_check_list(reqType='marketSnapShot', reqId=reqId)
        self.end_check_list[ct].status='Done'
                                 
    def get_datetime(self):
        """
        function to get the current datetime of IB system similar to that
        defined in Quantopian
        """
        self.log.notset(__name__+'::get_datetime_quantopian')  

        return self.stime.astimezone(self.showTimeZone)
      

    def contractDetails(self, reqId, contractDetails):
        '''
        IB callback function to receive contract info
        '''
        self.log.notset(__name__+'::contractDetails:'+str(reqId))                                     
        ct=self.search_in_end_check_list(reqId=reqId, reqType='contractDetails')
        newRow=pd.DataFrame({'right':contractDetails.summary.right,
                             'strike':float(contractDetails.summary.strike),
                             'expiry':dt.datetime.strptime(contractDetails.summary.expiry, '%Y%m%d'),
                             'contract':contractDetails.summary,
                             'multiplier':contractDetails.summary.multiplier\
                             },index=[0])
        self.end_check_list[ct].return_result=self.end_check_list[ct].return_result.append(newRow)

    def contractDetailsEnd(self, reqId):
        '''
        IB callback function to receive the ending flag of contract info
        '''
        self.log.debug(__name__+'::contractDetailsEnd:'+str(reqId))
        ct=self.search_in_end_check_list(reqId=reqId)
        self.end_check_list[ct].status='Done'
        self.data[self.search_security_in_Qdata(self.end_check_list[ct].security)].contractDetails=self.end_check_list[ct].return_result
   
      
    def req_info_from_server_if_all_completed(self):
        self.log.notset(__name__+'::req_info_from_server_if_all_completed')
        for ct in self.end_check_list:
            if self.end_check_list[ct].reqType=='realTimePrice':
                sec= self.end_check_list[ct].security
                if sec.secType!='IND':
                    if self.data[self.search_security_in_Qdata(sec)].ask_price>=0.01 \
                            and self.data[self.search_security_in_Qdata(sec)].bid_price>=0.01:
                        self.end_check_list[ct].status='Done'
                else: # index will never received bid ask price. only last_price
                    if self.data[self.search_security_in_Qdata(sec)].last_price>=0.01:
                        self.end_check_list[ct].status='Done'
                    
            if self.end_check_list[ct].reqType=='realTimeBars':
                self.end_check_list[ct].status='Done'
            if self.end_check_list[ct].reqType=='reqAllOpenOrders':
                self.end_check_list[ct].status='Done'
        flag=True
        for ct in self.end_check_list:
            if self.end_check_list[ct].status!='Done' and self.end_check_list[ct].waiver!=True:
                flag=False                
        return flag

    
    ###############  SUPPORTIVE functions       ###################
    def symbol(self, str_security):
        self.log.notset(__name__+'::symbol:'+str_security)  
        a_security=from_symbol_to_security(str_security)
        re=self.search_security_in_Qdata(a_security)
        return re

    def symbols(self, *args): 
        self.log.notset(__name__+'::symbols:'+str(args))  
        ls=[]
        for item in args:
            ls.append(self.symbol(item))
        return ls 

    def superSymbol(self, secType=None,
                    symbol=None,
                    currency='USD',
                    exchange='',
                    primaryExchange='',
                    expiry='',
                    strike=-1,
                    right='',
                    multiplier=-1):
        self.log.notset(__name__+'::superSymbol')  
        a_security= Security(secType=secType, symbol=symbol, currency=currency,
                    exchange=exchange, primaryExchange=primaryExchange, expiry=expiry,
                    strike=strike, right=right, multiplier=multiplier)  
        re=self.search_security_in_Qdata(a_security)
        return re
                    
    def reqHistParam(self,
                    security=None,
                    barSize=None,
                    goBack=None,
                    endTime=dt.datetime.now(),
                    whatToShow=None,
                    useRTH=1,
                    formatDate=2):
        self.log.notset(__name__+'::reqHistParam')
        if endTime.tzname()==None:
            endTime=self.showTimeZone.localize(endTime)   
        endTime=endTime.astimezone(tz=pytz.utc)
        endTime = dt.datetime.strftime(endTime,"%Y%m%d %H:%M:%S %Z") #datatime -> string
        if security.secType=='STK' or security.secType=='FUT':
            whatToShow='TRADES'
        elif security.secType=='CASH':
            whatToShow='ASK'
        else:
            self.log.error(__name__+'::reqHistParam: EXIT, cannot handle security.secType='+security.secType)
            exit()                                
        return ReqHistClass(security=security,barSize=barSize, goBack=goBack,
                    endTime=endTime, whatToShow=whatToShow,useRTH=useRTH,
                    formatDate=formatDate)

    def search_security_in_Qdata(self, a_security):
        self.log.notset(__name__+'::search_security_in_Qdata')  
        # if a_security is in Qdata, return it
        for ct in self.data:
            if same_security(ct, a_security):
                return ct
        # if it is not in Qdata, add it into Qdata
        self.data[a_security]=DataClass()
        self.log.debug(__name__+'::search_security_in_Qdata:Add %s into self.data' %(a_security.shortprint()))
        return a_security            


    def search_tickerId_in_Qdata_return_security(self, tickerId):
        self.log.notset(__name__+'::search_tickerId_in_Qdata_return_security')  

        Found_flag=0
        Found={}
        for security in self.data: 
            if security.reqRealTimePriceId==tickerId or security.reqMarketSnapShotId==tickerId or security.reqRealTimeBarsId==tickerId:
                Found_flag=Found_flag+1
                Found[Found_flag]=security
        if Found_flag==1:
            return Found[1]
        elif Found_flag==0:
            return None
            
        else:
            self.log.error(__name__+'::search_tickerId_in_Qdata_return_security:  EXIT, Found too many tickerId %s in self.data' %(tickerId,))
            for ct in Found:
                self.log.error(__name__+'::search_tickerId_in_Qdata_return_security:'+ Found[ct].shortprint())
            exit()            
            
    def search_in_end_check_list(self, reqType=None, security=None, \
                        reqId=None, notDone=None, output_version='location', allowToFail=False):
        self.log.notset(__name__+'::search_in_end_check_list')  
        search_result={}
        input_list=self.end_check_list
        if reqType!=None:
            for ct in input_list:
                if input_list[ct].reqType==reqType:
                    search_result[ct]=input_list[ct]
            input_list=search_result
            search_result={}
            
        if security!=None:    
            for ct in input_list:
                if same_security(input_list[ct].security,security):
                    search_result[ct]=input_list[ct]
            input_list=search_result
            search_result={}
                    
        if reqId!=None:                                       
            for ct in input_list:          
                if input_list[ct].reqId==reqId:
                    search_result[ct]=input_list[ct]
            input_list=search_result
            search_result={}
                                        
        if notDone!=None:                                       
            for ct in input_list:          
                if input_list[ct].status!='Done':
                    search_result[ct]=input_list[ct]
            input_list=search_result
            search_result={}

        if output_version=='location':
            if len(input_list)==0:
                if allowToFail==False:
                    self.log.error(__name__+'::search_in_end_check_list: cannot find any in self.end_check_list')
                    exit()
                else:
                    return None
            elif len(input_list)==1:
                for ct in input_list:
                    return ct
            else:
                self.log.error(__name__+'::search_in_end_check_list: found too many in self.end_check_list, EXIT')
                for ct in input_list:
                    self.log.error(input_list[ct].shortprint())
                exit()
        elif output_version=='list':
            return input_list
        else:
            self.log.error(__name__+'::search_in_end_check_list: cannot handle oupt_version='+output_version)
            

    def display_end_check_list(self):
        self.log.info(__name__+'::display_end_check_list')
        if len(self.end_check_list)==0:
            self.log.info(__name__+'::display_end_check_list: EMPTY self.end_check_list')
        else:    
            for ct in self.end_check_list:
                self.log.info(__name__+'::display_end_check_list: '+ str(ct)+' '+self.end_check_list[ct].shortprint())
            self.log.info(__name__+'::display_end_check_list: END     #############')

        
    def request_data(self,
                  positions  = None,
                  accountDownload= None,
                  reqAccountSummary = None,
                  nextValidId= None,
                  historyData= None,
                  realTimePrice = None,
                  realTimeBars=None,
                  contractDetails= None,
                  marketSnapShot=None,
                  reqAllOpenOrders= None,
                  waiver=None,
                  waitForFeedbackinSeconds=30,
                  repeat=3):
        self.log.notset(__name__+'::request_data')                          
        exit_untill_completed=0
        while(exit_untill_completed<=3):       
            if exit_untill_completed==0:
                all_req_info=self.create_end_check_list( \
                      positions  = positions,
                      accountDownload= accountDownload,
                      reqAccountSummary= reqAccountSummary,
                      nextValidId= nextValidId,
                      historyData= historyData,
                      realTimePrice = realTimePrice,
                      realTimeBars = realTimeBars,
                      contractDetails= contractDetails,
                      marketSnapShot= marketSnapShot,
                      reqAllOpenOrders= reqAllOpenOrders,
                      waiver=waiver)
                self.req_info_from_server(all_req_info)            
            elif exit_untill_completed>=1:
                self.log.error(__name__+'::request_data: Re-send request info')
                #self.display_end_check_list()
                new_list=self.search_in_end_check_list(notDone=True,output_version='list')
                self.log.debug(__name__+'::request_data:NotDone in self.end_check_list')
                for ct in new_list:
                    self.log.debug(__name__+'::reqeust_data:'+str(ct)+' '+new_list[ct].shortprint())
                    #print new_list[ct].reqId
                    #print new_list[ct].reqType
                    if new_list[ct].reqType=='realTimePrice':
                        self.cancelMktData(new_list[ct].reqId)
                        self.log.debug(__name__+'::request_data: cancelMktData Id='+str(new_list[ct].reqId))
                # re-send request info                
                self.req_info_from_server(new_list)  
                
            # continuously check if all requests have received responses 
            while (self.req_info_from_server_if_all_completed()==False) :
                time.sleep(0.1)            
                self.reqCurrentTime()
                self.processMessages()
                if self.check_timer(waitForFeedbackinSeconds)==True:
                    break
            
            # if receive data successfull, exit to loop
            # else, prepare to re-submit
            if self.req_info_from_server_if_all_completed()==True:
                self.log.debug(__name__+'::request_data: all responses are received')
                break
            else:
                # wait for 5 seconds
                for i in range(50):
                    time.sleep(0.1)            
                    self.reqCurrentTime()
                    self.processMessages()
                # prepare to re-submit    
                exit_untill_completed=exit_untill_completed+1
  
        # if tried many times, exit; if successfully done, return
        if exit_untill_completed>repeat:
            self.log.error(__name__+'::request_data: Tried many times, but Failed')
            exit()
        self.log.debug(__name__+'::req_info_from_server: COMPLETED')

    def show_nextId(self):
        return self.nextId
        
    def show_real_time_price(self, security, version):
        self.log.notset(__name__+'::show_real_time_price')                          
        adj_security=self.search_security_in_Qdata(security)
        if version=='ask_price':
            if self.data[adj_security].ask_price<0.01:
                self.request_data(realTimePrice=[adj_security])
            return self.data[adj_security].ask_price
        elif version=='bid_price':
            if self.data[adj_security].bid_price<0.01:
                self.request_data(realTimePrice=[adj_security])
            return self.data[adj_security].bid_price
        elif version=='last_price':
            if self.data[adj_security].last_price<0.01:
                self.request_data(realTimePrice=[adj_security])
            return self.data[adj_security].last_price
        else:
            self.log.error(__name__+'::show_real_time_price: EXIT, cannot handle version='+version)
            exit()

    def show_latest_price(self, security):
        self.log.notset(__name__+'::show_real_time_price')                          
        adj_security=self.search_security_in_Qdata(security)
        if self.data[adj_security].last_price<0.01:
            self.request_data(marketSnapShot=[adj_security])
        return self.data[adj_security].last_price    

    def create_end_check_list(self,
                      positions  = None,
                      accountDownload= None,
                      reqAccountSummary =None, 
                      nextValidId= None,
                      historyData= None,
                      realTimePrice = None,
                      realTimeBars = None,
                      contractDetails= None,
                      marketSnapShot=None,
                      reqAllOpenOrders =None,
                      waiver=None):
        self.log.notset(__name__+'::create_end_check_list')                          
        end_check_list={}
        end_check_list_id=0
        if positions  == True:
            end_check_list[end_check_list_id]=\
                    EndCheckListClass(status='Created',
                                      reqType='positions')  
            end_check_list_id=end_check_list_id+1
        if accountDownload!=None and accountDownload !=False:
            end_check_list[end_check_list_id]=\
                    EndCheckListClass(status='Created',
                                      reqType='accountDownload',
                                      input_parameters=accountDownload)
            end_check_list_id=end_check_list_id+1

        if reqAccountSummary!=None and reqAccountSummary !=False:
            end_check_list[end_check_list_id]=\
                    EndCheckListClass(status='Created',
                                      reqType='reqAccountSummary',
                                      input_parameters=reqAccountSummary)
            end_check_list_id=end_check_list_id+1

        if nextValidId== True:
            end_check_list[end_check_list_id]=\
                    EndCheckListClass(status='Created',
                                      reqType='nextValidId')            
            end_check_list_id=end_check_list_id+1
        if historyData!=None and historyData!=False: 
            if type(historyData[0])==type((0,0)):
                reqHistList=[self.reqHistParam(security=x[0],barSize=x[1],goBack=x[2],endTime=dt.datetime.now())  for x in historyData]
            else:
                reqHistList=historyData
            for ct in reqHistList:             
                end_check_list[end_check_list_id]=EndCheckListClass(\
                                            status='Created',
                                            input_parameters=ct,
                                            return_result=pd.DataFrame(),
                                            reqType='historyData',
                                            security=ct.security)                                            
                end_check_list_id=end_check_list_id+1
        if realTimePrice != False and realTimePrice != None: 
            if realTimePrice!='Default':            
                for security in realTimePrice:
                    end_check_list[end_check_list_id]=EndCheckListClass(\
                                                    status='Created',
                                                    input_parameters=security,
                                                    reqType='realTimePrice',
                                                    security=security)
                    end_check_list_id=end_check_list_id+1
            else:
                for security in self.data:
                    end_check_list[end_check_list_id]=EndCheckListClass(\
                                                    status='Created',
                                                    input_parameters=security,
                                                    reqType='realTimePrice',
                                                    security=security)
                    end_check_list_id=end_check_list_id+1

        if realTimeBars != False and realTimeBars != None: 
            if realTimeBars!='Default':            
                for security in realTimeBars:
                    end_check_list[end_check_list_id]=EndCheckListClass(\
                                                    status='Created',
                                                    input_parameters=security,
                                                    reqType='realTimeBars',
                                                    security=security)
                    end_check_list_id=end_check_list_id+1
            else:
                for security in self.data:
                    end_check_list[end_check_list_id]=EndCheckListClass(\
                                                    status='Created',
                                                    input_parameters=security,
                                                    reqType='realTimeBars',
                                                    security=security)
                    end_check_list_id=end_check_list_id+1
                
        if contractDetails!= False and contractDetails!= None:
            for security in contractDetails:
                end_check_list[end_check_list_id]=EndCheckListClass(\
                                                status='Created',
                                                input_parameters=security,
                                                return_result=pd.DataFrame(),
                                                reqType='contractDetails',
                                                security=security)
                end_check_list_id=end_check_list_id+1
        if marketSnapShot != False and marketSnapShot != None:             
            for security in marketSnapShot:
                end_check_list[end_check_list_id]=EndCheckListClass(\
                                                status='Created',
                                                input_parameters=security,
                                                reqType='marketSnapShot',
                                                security=security)
                end_check_list_id=end_check_list_id+1
        if reqAllOpenOrders != None:             
            end_check_list[end_check_list_id]=EndCheckListClass(\
                                            status='Created',
                                            reqType='reqAllOpenOrders')
            end_check_list_id=end_check_list_id+1
        if waiver!=None and waiver!=False:
            for ct in waiver:
                Found=False
                for item in end_check_list:
                    if end_check_list[item].reqType==ct:
                        Found=True
                        end_check_list[item].waiver=True
                if Found==False:
                    self.log.error(__name__+'::create_end_check_list: EXIT, cannot handle waiver='+str(ct))
                    exit()            
        return end_check_list


    def create_order(self, action, amount, security, orderDetails, 
                     ocaGroup=None, ocaType=1, transmit=None, parentId=None):
        contract=create_contract(security)
        order = IBCpp.Order()
        order.action = action      # BUY, SELL
        order.totalQuantity = amount
        order.orderType = orderDetails.orderType  #LMT, MKT, STP
        order.tif=orderDetails.tif 
        if ocaGroup !=None:
            order.ocaGroup=ocaGroup
        order.ocaType=ocaType 
        if transmit != None:
            order.transmit=transmit   
        if parentId != None:
            order.parentId=parentId
            
        if orderDetails.orderType=='MKT':
            pass
        elif orderDetails.orderType=='LMT':    
            order.lmtPrice=orderDetails.limit_price
        elif orderDetails.orderType=='STP':
            order.auxPrice=orderDetails.stop_price
        elif orderDetails.orderType=='STP LMT':
            order.lmtPrice=orderDetails.limit_price
            order.auxPrice=orderDetails.stop_price
        elif orderDetails.orderType=='TRAIL LIMIT':
            order.lmtPrice=orderDetails.stop_price-orderDetails.limit_offset
            order.trailingPercent=orderDetails.trailing_percent  # trailing percentage
            order.trailStopPrice=orderDetails.stop_price
        else:
            self.log.error(__name__+'::create_super_order: EXIT, Cannot handle order type=%s' %(orderDetails.orderType,))
            exit()  
        return OrderClass(contract=contract, order=order)

    def order(self, security, amount, orderDetails=MarketOrder()):
        if amount>0:  
            action='BUY'
        elif amount<0:
            action='SELL'
            amount=-amount
        else:
            self.log.debug(__name__+'::order: No order has been placed')
            return 0
        tmp=self.create_order(action, amount, security, orderDetails)
        if tmp!=None:
            return self.IBridgePyPlaceOrder(tmp)
        else:
            self.log.error(__name__+ '::order: EXIT wrong serurity instance '+security.shortprint())
            exit()

    def place_combination_orders(self, legList):
        '''
        legList is a list of created orders that are created by create_order( )
        '''
        finalOrderIdList=[]
        for leg in legList:
            orderId=self.IBridgePyPlaceOrder(leg)
            finalOrderIdList.append(orderId)
        return finalOrderIdList
                                 
    def place_order_with_TP_SL(self, parentOrder, tpOrder, slOrder):
        '''
        return orderId of the parentOrder only
        '''
        tpOrder.order.parentId=self.nextId
        slOrder.order.parentId=self.nextId
        parentOrder.order.transmit=False
        tpOrder.order.transmit=False
        slOrder.order.transmit=True
        self.IBridgePyPlaceOrder(parentOrder)
        self.IBridgePyPlaceOrder(tpOrder)
        self.IBridgePyPlaceOrder(slOrder)
