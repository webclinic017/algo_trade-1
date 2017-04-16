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

def initialize(context):
    pass

def handle_data(context, data):
    request_data(historyData=[(symbol('SPY'), '1 min', '1 D'),(symbol('AAPL'), '1 day', '10 D')  ])
    print data[symbol('SPY')].hist['1 min'].tail()
    print data[symbol('AAPL')].hist['1 day'].tail()
    exit()

          
  

