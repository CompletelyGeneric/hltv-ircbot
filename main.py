import socket
import feedparser
import pprint
import time
import re
from threading import Thread

network = 'irc.rizon.net'
port = 6667
channels = ['#cgsbots','#femgen']

irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
parse = feedparser.parse('http://www.hltv.org/hltv.rss.php?pri=15')
parse2 = feedparser.parse('http://www.hltv.org/hltv.rss.php?pri=15')
irc.connect((network, port))
print irc.recv(4096)
irc.send('NICK CSMatchBot\r\n')
irc.send('USER bot bot bot :wew laddy\r\n')
parse
for channel in channels:
	irc.send('JOIN ' + channel + '\r\n')


def sendToAllChans(message):
	for channel in channels:
		irc.send('PRIVMSG ' + channel + " :" + message + '\r\n')

#parses channel data and returns target of command
def parseChannel(data):
	channelName = ""
	d = data.split()
	for s in filter(lambda x: "PRIVMSG" in x, d):
		if s == "PRIVMSG":
			for s in filter(lambda x: "#" in x, d): 
				channelName = s
	return channelName


def parseCommands(data, channel):
	if data.find(':.matches') != -1:
		count = 0
		parse2
		for i in range(0, len(parse2.entries)):
			if count <= 4:
				irc.send("PRIVMSG "+ channel + " :" + "[" + parse2.entries[i]['summary'] + "] " + parse2.entries[i]['title'] + " on " + time.strftime("%m/%d %H:%M UTC", parse2.entries[i].published_parsed) + "\r\n")
				count = count + 1

#parses HLTV RSS feed and outputs it to all chans
#has its own thread
def parseFeed():
	while True:
		for i in range(0, len(parse.entries)):
			matchTimeTuple = parse.entries[i].published_parsed
			matchTime = str(list(matchTimeTuple)[3] - list(time.gmtime(time.time()))[3]) + " hour(s) and " + str(list(matchTimeTuple)[4] - list(time.gmtime(time.time()))[4]) + " minutes"
			matchFinal = "Upcoming Match: " + "[" + parse.entries[i]['summary'] + "] " + parse.entries[i]['title'] + " on in " + matchTime
			if matchTimeTuple[:4] == time.gmtime(time.time())[:4]:
				sendToAllChans(matchFinal)
				time.sleep(2)
		time.sleep(216000) #one hour

#threaded run loop
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