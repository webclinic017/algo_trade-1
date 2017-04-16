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

#fileName='example_show_positions.py'
#fileName='example_get_historical_data.py'
#fileName='example_show_real_time_prices.py'
#fileName='example_place_order.py'

#!!!!!! IMPORTANT  !!!!!!!!!!!!!!!!!
accountCode='DU15124' # You need to change it to your own IB account number
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

repBarFreq=1 # in seconds 
logLevel='INFO'
showTimeZone='US/Eastern'

with open("realMode.txt") as f:
    script = f.read()
exec(script)