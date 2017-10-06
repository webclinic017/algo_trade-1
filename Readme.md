# Trading scripts

## Folders
Here is a short explanation of the folders:
* IB_source: The official Phython API has been released for Interactive brokers. I played around a bit and it seems to support everything.
* script: Folder for our programs.
* data: This folder contains additional data like stock names for companies.

## Prerequisites
The programs will run in python 3.5.
Furthermore two libraries are needed. 'TextBlob' for sentiment analysis and 'tweepy' for the twitter API.
Several parallelization libraries are needed as well, since we will make extensive use of the python Queue library.

## Progress
So far I wrote a script that processes tweets filtered by keywords and analyses the positivity of them. the most radical ones are printed to the screen.
I also implemented a script that connects to the Interactive Broker server.

## Goal
The best thing would be to find scenarios such as the recent united incident.
One could for example keep track of the popular opinion of all listed US companies and take a weekly average, and compare this average to the current day average. Large discrepancies might be an indicator for some event.

## Further reading
* Interactive Brokers: https://www.interactivebrokers.com/en/home.php
* Interactive Broker API: http://interactivebrokers.github.io/tws-api/introduction.html#gsc.tab=0
* Tutorial for IB API: https://qoppac.blogspot.ch/2017/03/interactive-brokers-native-python-api.html
* Tutorial to Twitter: https://www.dataquest.io/blog/streaming-data-python/
