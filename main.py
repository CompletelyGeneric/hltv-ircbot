#!/usr/bin/env python
#https://github.com/CompletelyGeneric/hltv-ircbot
import socket
import feedparser #sudo pip install feedparser
import pprint
import hashlib
import time
import re
from threading import Thread
from datetime import datetime, date

#bot config
network = 'irc.rizon.net' #irc network you're connecting to. NOTE: Doesn't currently support SSL
port = 6667 #server port
channels = ['#CSGOMatches'] #Channels the bot listens on for commands
channelsAutoBroadcast = [''] #Channels the bot will auto broadcast live matches to, as well as listen for commands
nickName = 'CSGOMatchBot' #nick name for bot
nickservPass = '' #if the nick is registered with nickserv, put it's password here. Otherwise leave this blank.

#Initial connection to the network
irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
irc.connect((network, port))
irc.send('NICK ' + nickName + '\r\n')
irc.send('USER bot bot bot :wew laddy\r\n')
time.sleep(2) #hacky way for nickserv to be happy
irc.send ('PRIVMSG NickServ :identify ' + nickservPass + "\r\n")
parseList = []

#join channels
for channel in channels:
	irc.send('JOIN ' + channel + '\r\n')
for channel1 in channelsAutoBroadcast:
	irc.send('JOIN ' + channel1 + '\r\n')
print irc.recv(4096)


#auto broadcasting function
def sendToAllChans(message):
	for channel2 in channelsAutoBroadcast:
		irc.send('PRIVMSG ' + channel2 + " :" + message + '\r\n')

#parses channel data and returns target of command
def parseChannel(data):
	channelName = ""
	d = data.split()
	for s in filter(lambda x: "PRIVMSG" in x, d):
		if s == "PRIVMSG":
			for s in filter(lambda x: "#" in x, d): 
				channelName = s
	return channelName

#Command parser, probably going to move this to another file for clarity's sake
def parseCommands(data, channel):
	channelMessage = "PRIVMSG " + channel + " :"
	if data.find(':.matches') != -1: #.matches
		parse2 = feedparser.parse('http://www.hltv.org/hltv.rss.php?pri=15')
		counter = 0
		for i in range(0, len(parse2.entries)):
			if counter <= 5:
				currentTime = time.gmtime(time.time())
				matchTimeTuple = parse2.entries[i].published_parsed
				matchTimeTillMatchSeconds = ((time.mktime(matchTimeTuple) - time.mktime(currentTime)))
				m, s = divmod(matchTimeTillMatchSeconds, 60)
				h, m = divmod(m, 60)
				if h < 0:
					irc.send("PRIVMSG " + channel + " :" + "--- " + parse2.entries[i]['title'] + " is live! " "\r\n")
				else:
					matchTimeTillMatch = "%d hour(s) and %02d minutes" % (h, m)
					irc.send("PRIVMSG " + channel + " :" + "--- " + parse2.entries[i]['title'] + " in "  + matchTimeTillMatch + "\r\n")
				counter = counter + 1
	if data.find(':.bots') != -1 or data.find(':.version') != -1: #.bots	
		irc.send(channelMessage + "Reporting in! [python] See https://github.com/CompletelyGeneric/hltv-ircbot" + "\r\n")
	if data.find(':.help') != -1: #.help
		irc.send("PRIVMSG" + channel +" :" + ".matches, .help, .version/.bots" )

#parses HLTV RSS feed and outputs it to all channels; has it's own thread
def parseFeed():
	matchHashList = []
	while True:
		parse = feedparser.parse('http://www.hltv.org/hltv.rss.php?pri=15')
		matchHashListCurrent = []
		for i in range(0, len(parse.entries)):
			currentTime = time.gmtime(time.time())
			matchTimeTuple = parse.entries[i].published_parsed
			matchTimeTillMatchSeconds = ((time.mktime(matchTimeTuple) - time.mktime(currentTime)))
			matchHashCurrent = hashlib.md5(parse.entries[i]['summary'] + "] " + parse.entries[i]['title'] + parse.entries[i]['published']).hexdigest()
			matchHashListCurrent.append(matchHashCurrent)
			if matchTimeTillMatchSeconds <= 0 and matchHashCurrent not in matchHashList:
				matchFinal = "--- " + parse.entries[i]['title'] + " is live! "  + "\r\n"
				sendToAllChans(matchFinal)
				matchHashList.append(matchHashCurrent)
				time.sleep(2)
		for x in matchHashList:
			if x not in matchHashListCurrent:
				matchHashList.remove(x)
		time.sleep(60) #don't spam the RSS feed

#Run loop; has its own thread.
def keepAlive():
	while True:
	   	data = irc.recv(8196)
	   	if data.find('PING') != -1:
	   		irc.send('PONG ' + data.split()[1] + '\r\n')
	   	focusChannel = parseChannel(data)
	   	parseCommands(data, focusChannel)
	   	print data

#starting the threads
t1 = Thread(target = keepAlive)
t2 = Thread(target = parseFeed)
t1.start()
t2.start()