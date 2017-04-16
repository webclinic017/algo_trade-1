# Trading scripts

## Folders
Here is a short explanation of the folders:
* IBridgePy: This is a third party (but officially supported) interface to InterativeBrokers. It is the only reasonable python API I found for any broker.
* script: Folder for our programs.

## Prerequisites
The programs will run in python 2.7 because the IBridgePy only supports old python :(.
Furthermore two libraries are needed. 'TextBlob' for sentiment analysis and 'tweepy' for the twitter API.

## Progress
So far I wrote a script that processes tweets filtered by keywords and analysis the positivity of them. the most radical ones are printed to the screen.

## Goal
The best thing would be to find those scenarios like the recent united incident.
One could for example keep track of the popular opinion of all listed US companies and take a weekly average, and compare this average to the current day average. Large discrepancies might be an indicator for some event.

## Further reading
* Interactive Brokers: https://www.interactivebrokers.com/en/home.php
* IBridgePy API: http://www.ibridgepy.com/
* Video Tutorial zu IBridgePy: https://youtu.be/Cg3gejGX3Xk
* Tutorial that covered everything I programmed so far: https://www.dataquest.io/blog/streaming-data-python/
