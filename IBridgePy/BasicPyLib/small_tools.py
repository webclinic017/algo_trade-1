import time
import datetime as dt
import pytz

def localTzname():
    is_dst=time.localtime().tm_isdst 
    if time.daylight and is_dst>0:
        offsetHour = time.altzone / 3600
    else:
        offsetHour = time.timezone / 3600
    return 'Etc/GMT%+d' % offsetHour
    

def if_market_is_open(dt_aTime, start='9:30', end='16:00', early_end='13:00', version='true_or_false'):

    holiday=[dt.date(2015,11,26),dt.date(2015,12,25),\
             dt.date(2016,1,1),dt.date(2016,1,18),dt.date(2016,2,15),
             dt.date(2016,3,25),dt.date(2016,5,30),dt.date(2016,7,4),
             dt.date(2016,9,5),dt.date(2016,11,24),dt.date(2016,12,26)]
    earlyClosing=[dt.date(2015,11,27), dt.date(2015,12,24)] 
    fmt = '%Y-%m-%d %H:%M:%S %Z%z'
    if dt_aTime.tzinfo==None:
        print 'small_tools::if_market_is_open: cannot handle timezone unaware datetime',dt_aTime
        exit()

    dt_aTime=dt_aTime.astimezone(pytz.timezone('US/Eastern'))    
    if dt_aTime.weekday()==6 or dt_aTime.weekday()==5:
        #print 'weekend'
        if version=='true_or_false':        
            return False
        else:
            return None
    if dt_aTime.date() in holiday:
        #print 'holiday'
        if version=='true_or_false':        
            return False
        else:
            return None
            
    if dt_aTime.date() in earlyClosing:
        marketStartTime=dt_aTime.replace(hour=int(start.split(':')[0]), minute=int(start.split(':')[1]), second=0)
        marketCloseTime=dt_aTime.replace(hour=int(early_end.split(':')[0]), minute=int(early_end.split(':')[1]), second=0)
    else:
        marketStartTime=dt_aTime.replace(hour=int(start.split(':')[0]), minute=int(start.split(':')[1]), second=0)
        marketCloseTime=dt_aTime.replace(hour=int(end.split(':')[0]), minute=int(end.split(':')[1]), second=0)

    if version=='market_close_time':
        return marketCloseTime
    elif version=='market_open_time':
        return marketStartTime
    elif version=='true_or_false':       
        if dt_aTime>=marketStartTime and dt_aTime<marketCloseTime:
            #print marketStartTime.strftime(fmt)
            #print marketCloseTime.strftime(fmt)
            #print 'OPEN '+dt_aTime.strftime(fmt)   
            return True
        else:
            #print marketStartTime.strftime(fmt)
            #print marketCloseTime.strftime(fmt)
            #print 'CLOSE '+dt_aTime.strftime(fmt)      
            return False
    else:
        print 'small_tools::if_market_is_open: EXIT, Cannot handle version=',version
        exit()

def market_time(dt_aTime, version):
    if dt_aTime.tzinfo==None:
        print 'small_tools::market_time: cannot handle timezone unaware datetime',dt_aTime
        exit()
    if version=='open_time':    
        tp=if_market_is_open(dt_aTime, version='market_open_time')
    elif version=='close_time':
        tp=if_market_is_open(dt_aTime, version='market_close_time')
    else:
        print 'small_tools::market_time: EXIT, Cannot handle version=',version
        exit()
        
    if tp==None:
        print 'market is closed today',dt_aTime
        return None
    else:
        return tp
 

      
if __name__=='__main__':
    pass