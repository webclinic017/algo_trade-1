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
def initialize(context):
    context.flag=False
    context.security=symbol('CASH,EUR,USD')    
    
def handle_data(context, data):
    if context.flag==False:               
        orderId=order(context.security, 100)
        order_status_monitor(orderId, target_status='Filled')
        context.flag=True

    else:
        time.sleep(10)
        display_all()
        exit()
     