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

from IBridgePy.quantopian import Security, PositionClass, \
create_contract, MarketOrder, OrderClass, same_security, \
from_contract_to_security
import datetime as dt
import time
from IBridgePy.TraderBase import Trader
import os
from IBridgePy import IBCpp

class Trader(Trader):

    def order_target(self, security, amount, orderDetails=MarketOrder()):
        self.log.notset(__name__ + '::order_target') 
        hold=self.count_positions(security) 
        if amount!=hold:
            return self.order(security, amount=amount-hold, orderDetails=orderDetails)
        else:
            self.log.debug(__name__+'::order_target: %s No action is needed' %(security.shortprint(),))
            return 0

    def order_target_II(self, security, amount, orderDetails=MarketOrder()):
        self.log.notset(__name__ + '::order_target_II') 
        hold=self.count_positions(security)  
        if (hold>=0 and amount>0) or (hold<=0 and amount<0):
            orderID=self.order(security, amount=amount-hold, orderDetails=orderDetails)
            if self.order_status_monitor(orderID,'Filled'):
                return orderID
        if (hold>0 and amount<0) or (hold<0 and amount>0):
            orderID=self.order_target(security, 0)
            if self.order_status_monitor(orderID,'Filled'):
                orderID=self.order(security, amount)
                if self.order_status_monitor(orderID,'Filled'):
                    return orderID
                else:
                    self.log.debug(__name__+'::order_target_II:orderID=%s was not processed as expected. EXIT!!!' %(orderID,))
                    return 0
            else:    
                self.log.debug(__name__+'::order_target_II:orderID=%s was not processed as expected. EXIT!!!' %(orderID,))
                return 0
        if hold==amount:
            self.log.debug(__name__+'::order_target_II: %s No action is needed' %(security.shortprint(),))
            return 0
        else:
            self.log.debug(__name__+'::order_target_II: hold='+str(hold) )
            self.log.debug(__name__+'::order_target_II: amount='+str(amount) )
            self.log.debug(__name__+'::order_target_II: Need debug EXIT' )
            exit()            

    def updateAccountValue(self, key, value, currency, accountName):
        """
        update account values such as cash, PNL, etc
        """
        self.log.notset(__name__+'::updateAccountValue: key='+key \
                +' value='+str(value)\
                +' currency=' + currency\
                +' accountName=' + accountName)

        if self.validateAccountCode(accountName):
            if key == 'AvailableFunds':
                self.context.portfolio.cash=float(value)
                #print __name__+'::updateAccountValue: cash=',self.context.portfolio.cash
                #self._transfer_data()
            elif key == 'UnrealizedPnL':
                self.context.portfolio.pnl=float(value)
            elif key == 'NetLiquidation':
                self.context.portfolio.portfolio_value=float(value)
                #print __name__+'::updateAccountValue: portfolio=',self.context.portfolio.portfolio_value
                #self._transfer_data()
            elif key == 'GrossPositionValue':
                self.context.portfolio.positions_value=float(value)
                #print __name__+'::updateAccountValue: positions=',self.context.portfolio.positions_value
                #self._transfer_data()
            else:
                pass

    def updatePortfolio(self, contract, position, marketPrice, marketValue, averageCost, unrealizedPNL, realizedPNL, accountName):
        pass
           
    def accountDownloadEnd(self, accountName):
        self.log.debug(__name__ + '::accountDownloadEnd: ' + str(accountName))
        if self.validateAccountCode(accountName):
            ct=self.search_in_end_check_list(reqType='accountDownload', allowToFail=True)
            if ct!=None:
                self.end_check_list[ct].status='Done'

    def validateAccountCode(self, accountName):
        self.log.notset(__name__+'::validateAccountCode: %s' %(accountName,))
        if accountName!=self.accountCode:
            self.log.error(__name__ + '::validateAccountCode: EXIT, returned accountN (%s) not equal to input accountN (%s)' %(accountName, self.accountCode))
            return False
        else:
            return True
            
    def accountSummary(self, reqId, accountName, tag, value, currency):
        pass
        #self.log.debug(__name__ + '::accountSummary:CANNOT handle' + str(reqId) + str(accountName) + str(tag) + 
        #str(value) + str(currency))
       
    def accountSummaryEnd(self, reqId):
        pass
        #self.log.debug(__name__+'::accountSummaryEnd: '+str(reqId))
        #ct=self.search_in_end_check_list(reqType='reqAccountSummary', reqId=reqId)
        #self.end_check_list[ct].status='Done'
        
    def position(self, accountName, contract, position, price):
        """
        call back function of IB C++ API which updates the position of a contract
        of a account
        """
        if self.validateAccountCode(accountName):
            security=from_contract_to_security(contract)
            self.log.debug(__name__+'::position: '+accountName+' '+security.shortprint() +','+ str(position) + ', ' + str(price))
            securityFound=self.search_security_in_positions(security)
            self.context.portfolio.positions[securityFound].amount=position
            self.context.portfolio.positions[securityFound].cost_basis=price       
            self.context.portfolio.positions[securityFound].accountCode=accountName

    def orderStatus(self,orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld):
        """
        call back function of IB C++ API which update status or certain order
        indicated by orderId
        """
        self.log.debug(__name__+'::orderStatus: ' + str(orderId) + ", " + str(status) + ", "
        + str(filled) + ", " + str(remaining) + ", " + str(avgFillPrice))
        if orderId in self.context.portfolio.orderStatusBook:     
            self.context.portfolio.orderStatusBook[orderId].filled=filled
            self.context.portfolio.orderStatusBook[orderId].remaining=remaining
            self.context.portfolio.orderStatusBook[orderId].status=status
            self.context.portfolio.orderStatusBook[orderId].avgFillPrice=avgFillPrice
            if (self.context.portfolio.orderStatusBook[orderId].parentOrderId 
            is not None and status == 'Filled'):
                if (self.context.portfolio.orderStatusBook[orderId].stop is not None):
                    self.context.portfolio.orderStatusBook[
                    self.context.portfolio.orderStatusBook[orderId].parentOrderId].stop_reached = True
                    self.log.info(__name__ + "::orderStatus " + "stop executed: " + 
                    self.context.portfolio.orderStatusBook[orderId].contract.symbol)
                if (self.context.portfolio.orderStatusBook[orderId].limit is not None):
                    self.context.portfolio.orderStatusBook[
                    self.context.portfolio.orderStatusBook[orderId].parentOrderId].limit_reached = True
                    self.log.info(__name__ + "::orderStatus " + "limit executed: " +
                    self.context.portfolio.orderStatusBook[orderId].contract.symbol)               
        else:
            self.log.error(__name__+'::orderStatus: EXIT, cannot find orderId=%i in orderStatusBook' %(orderId,))
            exit()

    def openOrder(self, orderId, contract, order, orderstate):
        """
        call back function of IB C++ API which updates the open orders indicated
        by orderId
        """
        self.log.debug(__name__+"::openOrder: " + str(orderId) + ', ' + str(contract.symbol) + 
        '.' + str(contract.currency) + ', ' + str(order.action) + ', ' + 
        str(order.totalQuantity))
        if orderId in self.context.portfolio.orderStatusBook:
            if self.context.portfolio.orderStatusBook[orderId].contract!=contract:
                self.context.portfolio.orderStatusBook[orderId].contract=contract                        
            if self.context.portfolio.orderStatusBook[orderId].order!=order:
                self.context.portfolio.orderStatusBook[orderId].order=order                        
            if self.context.portfolio.orderStatusBook[orderId].orderstate!=orderstate:
                self.context.portfolio.orderStatusBook[orderId].orderstate=orderstate                        
            self.context.portfolio.orderStatusBook[orderId].status=orderstate.status            
        else:
            self.context.portfolio.orderStatusBook[orderId] = \
                OrderClass(orderId=orderId,
                           created=dt.datetime.now(),
                    stop=(lambda x: x if x<100000 else None)(order.auxPrice),
                    limit=(lambda x: x if x<100000 else None)(order.lmtPrice),
                    amount=order.totalQuantity,
                    commission=(lambda x: x if x<100000 else None)(orderstate.commission),
                    #sid=Security(contract.secType+'.'+contract.symbol+'.'+contract.currency),
                    status=orderstate.status,
                    contract=contract, order=order,
                    orderstate=orderstate)
    def cancel_order(self, order):
        """
        function to cancel orders
        """
        self.log.notset(__name__+'::cancel_order')  

        if isinstance(order, OrderClass):
            self.cancelOrder(order.orderId)
        else:
            self.cancelOrder(int(order))

    def cancel_all_orders(self):
        self.log.notset(__name__+'::cancel_all_orders')  
        for orderId in self.context.portfolio.orderStatusBook:
            if self.context.portfolio.orderStatusBook[orderId].status not in ['Filled','Cancelled','Inactive']:
                self.cancel_order(orderId) 

    def get_open_order(self, sid=None):
        """
        function to get open orders
        """
        self.log.notset(__name__+'::get_open_order')  

        if sid==None:
            result={}
            for ct in self.context.portfolio.orderStatusBook:
                result[self.context.portfolio.orderStatusBook[ct].sid]=self.context.portfolio.orderStatusBook[ct]
            return result
        else:
            result={}            
            for ct in self.context.portfolio.orderStatusBook:
                if same_security(self.context.portfolio.orderStatusBook[ct].sid,sid):
                    result[self.context.portfolio.orderStatusBook[ct].sid]=self.context.portfolio.orderStatusBook[ct]
            return result

    def req_info_from_server(self, list_requests):
        self.log.debug(__name__+'::req_info_from_server: Request the following info to server')
        self.end_check_list=list_requests
        
        for ct in self.end_check_list:
            self.end_check_list[ct].status='Submitted'
            if self.end_check_list[ct].reqType=='positions':
                self.reqPositions()                            # request open positions
                self.log.debug(__name__+'::req_info_from_server: requesting open positions info from IB')
            elif self.end_check_list[ct].reqType=='reqAllOpenOrders':
                self.reqAllOpenOrders()                            # request all open orders
                self.log.debug(__name__+'::req_info_from_server: requesting allOpenOrders from IB')
            elif self.end_check_list[ct].reqType=='accountDownload':
                self.reqAccountUpdates(True,self.end_check_list[ct].input_parameters)  # Request to update account info
                self.log.debug(__name__+'::req_info_from_server: requesting to update account=%s info from IB' %(self.end_check_list[ct].input_parameters,))
            elif self.end_check_list[ct].reqType=='reqAccountSummary':
                self.log.error(__name__+'::req_info_from_server: EXIT, reqAccountSummary is not ready')
                exit()
                self.reqAccountSummary(self.nextId, 'All', 'TotalCashValue,AccountType, BuyingPower, SettledCash')                
                self.end_check_list[ct].reqId=self.nextId                                
                self.log.debug(__name__+'::req_info_from_server: reqAccountSummary account=%s, reqId=%i' %(self.end_check_list[ct].input_parameters,self.nextId))
                self.nextId += 1  # Prepare for next request

            elif self.end_check_list[ct].reqType=='nextValidId':                
                self.reqIds(0)
                self.log.debug(__name__+'::req_info_from_server: requesting nextValidId')
            elif self.end_check_list[ct].reqType=='historyData':
                #reqId=self.req_hist_price(self.end_check_list[ct].input_parameters.security, self.end_check_list[ct].input_parameters.barSize, self.end_check_list[ct].input_parameters.goBack, self.end_check_list[ct].input_parameters.endTime)
                self.reqHistoricalData(self.nextId, 
                                       create_contract(self.end_check_list[ct].input_parameters.security),
                                       self.end_check_list[ct].input_parameters.endTime,
                                       self.end_check_list[ct].input_parameters.goBack,
                                       self.end_check_list[ct].input_parameters.barSize,
                                       self.end_check_list[ct].input_parameters.whatToShow,
                                       self.end_check_list[ct].input_parameters.useRTH,
                                       self.end_check_list[ct].input_parameters.formatDate)
                self.end_check_list[ct].reqId=self.nextId                                
                self.nextId += 1  # Prepare for next request
                time.sleep(0.1)
                self.log.debug(__name__ + "::req_info_from_server:"
                                       + "requesting hist data for "
                                       + self.end_check_list[ct].input_parameters.security.shortprint() +' '
                                       + self.end_check_list[ct].input_parameters.barSize+' '
                                       + 'reqId='+str(self.nextId)+' '
                                       + str(self.end_check_list[ct].input_parameters.endTime) +' '
                                       + 'formatDate='+str(self.end_check_list[ct].input_parameters.formatDate))

            elif self.end_check_list[ct].reqType=='realTimePrice':
                sec=self.end_check_list[ct].security
                self.search_security_in_Qdata(sec).reqRealTimePriceId=self.nextId
                self.reqMktData(self.nextId, create_contract(self.end_check_list[ct].security),'233',False) # Send market data requet to IB server
                self.end_check_list[ct].reqId=self.nextId                                
                self.log.debug(__name__+'::req_info_from_server:requesting real time quotes: ' 
                            +self.end_check_list[ct].security.shortprint() + ' '
                            +'reqId='+str(self.nextId))
                self.nextId += 1  # Prepare for next request
            elif self.end_check_list[ct].reqType=='realTimeBars':
                sec=self.end_check_list[ct].security
                self.search_security_in_Qdata(sec).reqRealTimeBarsId=self.nextId
                self.reqRealTimeBars(self.nextId, create_contract(self.end_check_list[ct].security), 5, 'MIDPOINT', 0) # Send market data requet to IB server
                self.end_check_list[ct].reqId=self.nextId                                
                self.log.debug(__name__+'::req_info_from_server:requesting realTimeBars: ' 
                            +self.end_check_list[ct].security.shortprint() + ' '
                            +'reqId='+str(self.nextId))
                self.nextId += 1  # Prepare for next request
            elif self.end_check_list[ct].reqType=='contractDetails':
                self.reqContractDetails(self.nextId, create_contract(self.end_check_list[ct].security))
                self.end_check_list[ct].reqId=self.nextId                                
                self.log.debug(__name__+'::req_info_from_server: reqesting contractDetails '\
                                    +self.end_check_list[ct].security.shortprint()+' reqId='+str(self.nextId))
                self.nextId += 1  # Prepare for next request
            elif self.end_check_list[ct].reqType=='marketSnapShot':
                sec=self.end_check_list[ct].security
                self.search_security_in_Qdata(sec).reqMarketSnapShotId=self.nextId
                self.reqMktData(self.nextId, create_contract(self.end_check_list[ct].security),'',True) # Send market data requet to IB server
                self.end_check_list[ct].reqId=self.nextId                                
                self.log.debug(__name__+'::req_info_from_server: requesting market snapshot: '+self.end_check_list[ct].security.shortprint()+' reqId='+str(self.nextId))
                self.nextId += 1  # Prepare for next request
            else:
                self.log.error(__name__+'::req_info_from_server: EXIT, cannot handle reqType='+self.end_check_list[ct].reqType)
                exit()

        for ct in self.end_check_list:
            self.log.notset(str(ct)+' '+self.end_check_list[ct].shortprint())        
        self.set_timer()

    def search_security_in_positions(self, a_security):
        self.log.notset(__name__+'::search_security_in_positions')  
        # if positions is empty, add new security, then return
        if self.context.portfolio.positions=={}:
            self.context.portfolio.positions[a_security]=PositionClass()
            self.log.debug(__name__+'::search_security_in_positions: Empty, add a new position '+a_security.shortprint())
            return a_security
        # search security in positions, if found only one, return,
        foundFlag=0
        found={}
        for ct in self.context.portfolio.positions:
            if same_security(ct, a_security):
                foundFlag=foundFlag+1
                found[foundFlag]=ct
        if foundFlag==1:
            return found[1]
        elif foundFlag==0:   
            # a_security is not in positions,  add it in it               
            self.context.portfolio.positions[a_security]=PositionClass()
            self.log.debug(__name__+'::search_security_in_positions: cannot find one, add a new position '+a_security.shortprint())
            return a_security
        else:
            self.log.error(__name__+'::search_security_in_positions: EXIT, found too many securities')
            for ct in found:
                self.log.error(found[ct].shortprint())
            exit()  

    def display_positions(self):
        self.log.notset(__name__+'::display_positions')  
        if self.hold_any_position():
            self.log.info( '##    POSITIONS    ##')
            self.log.info( 'Symbol Amount Cost_basis Latest_profit')    

            for ct in self.context.portfolio.positions:            
                if self.context.portfolio.positions[ct].amount!=0:
                    a=self.data[self.search_security_in_Qdata(ct)].last_price
                    b=self.context.portfolio.positions[ct].cost_basis
                    c=self.context.portfolio.positions[ct].amount
                    if a!=None and a!=-1:
                        self.log.info( ct.shortprint()+' '+str(c)+' ' +str(b)+' '+str((a-b)*c )) 
                    else:
                        self.log.info( ct.shortprint()+' '+str(c)+' ' +str(b)+' NA') 
                        
            self.log.info( '##    END    ##')               
        else:
            self.log.info( '##    NO ANY POSITION    ##')

    def display_orderStatusBook(self): 
        self.log.notset(__name__+'::display_orderStatusBook')
           
        #show orderStatusBook
        if len(self.context.portfolio.orderStatusBook) >=1:
            self.log.info( '##    Order Status    ##')               
            for orderId in self.context.portfolio.orderStatusBook:
                self.log.info( 'reqId='+str(orderId)+' '\
                        +' '+self.context.portfolio.orderStatusBook[orderId].status\
                        +' '+self.context.portfolio.orderStatusBook[orderId].shortprint()\
                        )
            self.log.info( '##    END    ##')               

        else:
            self.log.info( '##    NO any order    ##')
            
    def display_account_info(self):
        """
        print account info such as position values in format ways
        """
        self.log.debug(__name__ + '::display_acount_info')
        self.log.info('##    ACCOUNT Balance    ##')
        self.log.info('CASH=' + str(self.context.portfolio.cash))
        #self.log.info('pnl=' + str(self.context.portfolio.pnl))
        self.log.info('portfolio_value=' + str(self.context.portfolio.portfolio_value))
        self.log.info('positions_value=' + str(self.context.portfolio.positions_value))
        #self.log.info('returns=' + str(self.context.portfolio.returns))
        #self.log.info('starting_cash=' + str(self.context.portfolio.starting_cash))
        #self.log.info('start_date=' + str(self.context.portfolio.start_date))

    def display_all(self):
        self.display_account_info()
        self.display_positions()
        self.display_orderStatusBook()

    def order_status_monitor(self, orderId, target_status,waitingTimeInSeconds=30 ):
        self.log.notset(__name__+'::order_status_monitor')
        if orderId==-1:
            self.log.error(__name__+'::order_status_monitor: EXIT, orderId=-1' )
            exit()
        elif orderId==0:
            return True
        else:
            timer=dt.datetime.now()
            exit_flag=True
            while(exit_flag):
                time.sleep(0.1)
                self.reqCurrentTime()
                self.processMessages()
                if (dt.datetime.now()-timer).total_seconds()<=waitingTimeInSeconds:
                    if self.context.portfolio.orderStatusBook[orderId].status=='Filled':
                        self.log.info(__name__+'::order_status_monitor: Filled '+self.context.portfolio.orderStatusBook[orderId].shortprint())                     
                        return True
                elif self.context.portfolio.orderStatusBook[orderId].status==target_status:
                        return True    
                elif self.context.portfolio.orderStatusBook[orderId].status=='Inactive':
                        self.log.error(__name__+'::order_status_monitor: EXIT, status=Inactive!!!, orderId=%i, %s' %(orderId,from_contract_to_security(self.context.portfolio.orderStatusBook[orderId].contract).shortprint()))
                        exit()                       
                else:
                    self.log.error(__name__+'::order_status_monitor: EXIT, waiting time is too long, >%i, orderId=%i, %s, %s' %(waitingTimeInSeconds,orderId,from_contract_to_security(self.context.portfolio.orderStatusBook[orderId].contract).shortprint(),self.context.portfolio.orderStatusBook[orderId].status))
                    exit()
                    

    def close_all_positions(self, orderStatusMonitor=True):
        self.log.debug(__name__+'::close_all_positions:')
        tp=self.context.portfolio.positions.keys()
        orderIdList=[]
        for security in tp:
            orderId=self.order_target(security, 0)
            orderIdList.append(orderId)
        if orderStatusMonitor:
            for orderId in orderIdList:
                self.order_status_monitor(orderId, 'Filled')

    def close_all_positions_except(self, a_security):
        self.log.debug(__name__+'::close_all_positions_except:'+a_security.shortprint())
        tp=self.context.portfolio.positions.keys()
        orderIdList=[]
        for security in tp:
            if same_security(a_security, security):
                #print tp_security.shortprint(), 'ignore'
                pass
            else:
                #print security.shortprint(),'close'
                orderId=self.order_target(security, 0)
                orderIdList.append(orderId)
        for orderId in orderIdList:
            self.order_status_monitor(orderId, 'Filled')                
 
    def check_if_any_unfilled_orders(self, verbose=False):
        self.log.notset(__name__+'::check_if_any_unfilled_orders')      
        flag=False
        for orderId in self.context.portfolio.orderStatusBook:
            if  self.context.portfolio.orderStatusBook[orderId].status!='Filled': 
                flag=True
        if flag==True:
            if verbose==True:
                self.log.info(__name__+'::check_if_any_unfilled_orders: unfilled orderst are:')
                self.display_orderStatusBook()
        return flag        
 
  

    def show_account_info(self, infoName ):
        #self.request_data(accountDownload=self.accountCode)
        if hasattr(self.context.portfolio, infoName):
            tp=getattr(self.context.portfolio, infoName)
            return tp
        else:
            self.log.error(__name__+'::show_account_info: ERROR, context.portfolio of accountCode=%s does not have attr=%s' %(self.accountCode, infoName))
            exit()

    def count_open_orders(self, security='All', verbose=False):
        self.log.debug(__name__+'::count_open_orders') 
        count=0
        for orderId in self.context.portfolio.orderStatusBook:
            if  self.context.portfolio.orderStatusBook[orderId].status!='Filled' and self.context.portfolio.orderStatusBook[orderId].status!='Cancelled': 
                if security=='All':          
                    count = count+  self.context.portfolio.orderStatusBook[orderId].amount                     
                else:
                    tp=self.context.portfolio.orderStatusBook[orderId].contract
                    tp=from_contract_to_security(tp)
                    if same_security(tp,security):
                        count = count+  self.context.portfolio.orderStatusBook[orderId].amount                     
        return count

    def count_positions(self, a_security, verbose=False):
        self.log.debug(__name__+'::count_positions') 
        for sec in self.context.portfolio.positions:
            if same_security(sec,a_security):
                return self.context.portfolio.positions[sec].amount
        return 0

    def hold_any_position(self):
        self.log.notset(__name__+'::hold_any_position')        
        for ct in self.context.portfolio.positions:
            if self.context.portfolio.positions[ct].amount!=0:
                return True
        return False        
        
        
    def calculate_profit(self, a_security):
        self.log.notset(__name__+'::calculate_profit:'+a_security.shortprint())
        tp=self.search_security_in_Qdata(a_security)
        a=self.show_real_time_price(tp, 'ask_price')
        b=self.context.portfolio.positions[tp].cost_basis
        c=self.context.portfolio.positions[tp].amount
        if a!=None and a!=-1:
            return (a-b)*c 
        else:
            return None
        
    def IBridgePyPlaceOrder(self, an_order):
        an_order.order.account=self.accountCode
        self.placeOrder(self.nextId, an_order.contract, an_order.order)
        an_order.orderId=self.nextId
        an_order.created=dt.datetime.now()
        an_order.stop=an_order.order.auxPrice
        an_order.limit=an_order.order.lmtPrice
        an_order.amount=an_order.order.totalQuantity
        an_order.status='PreSubmitted'
        self.context.portfolio.orderStatusBook[self.nextId] = an_order
        self.log.info(__name__+'::order: REQUEST orderId=%s ' %(self.nextId,) +self.context.portfolio.orderStatusBook[self.nextId].shortprint() )
        self.nextId=self.nextId+1
        return self.nextId-1
        
        
                      