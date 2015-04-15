#!/usr/bin/python
# My first python program
import socket
import threading
import time
import string
import random
import ConfigParser
import sys
import datetime

#apt-get install python-tk
import Tkinter
from Tkinter import *
from ScrolledText import ScrolledText

#ircServer handles the server connection
class ircServer(threading.Thread):
	#Instance variable (socket)
	irc = socket.socket ( socket.AF_INET, socket.SOCK_STREAM )
	
	#Constructor
	def __init__ ( self, myNick, server, port, dataPort ):
		self.myNick = myNick
		self.server = server
		self.port = port
		self.dataPort = dataPort
		threading.Thread.__init__ ( self )

	#Connects to irc server and parses data from server
	def connect(self):
		#Register self with server
		irc = socket.socket ( socket.AF_INET, socket.SOCK_STREAM )
		self.irc = irc
		self.irc.connect ( ( self.server, int(self.port) ) )
		self.irc.send ( 'NICK ' + self.myNick + '\r\n' )
		self.irc.send ( 'USER user user user :Hurr\r\n' )

		#Start the GUI
		client = ircClient(self.server)
		client.setSocket(self.irc)
		client.start()		
		time.sleep(1)
		

		#Listen and respond to server
		while True:
			buffer = ""
			try:	   		
				data = irc.recv ( self.dataPort )
			except Exception:
				print "Socket closed"
			self.data = data					
			buffer = buffer + data
			temp=string.split(buffer, "\n")
			buffer=temp.pop( )				
			for line in temp:
			        line=string.rstrip(line)
			        line=string.split(line)
				self.line = line
				try:				
					client.setServerMessage(line)		
				except:
					pass
				#Debug
				#for i in range(len(line)):
				#	print "Line" + str(i) + ": " + line[i]
				if ( len(line) < 0 ):
					pass
				#Keep-alive
				elif ( len(line) > 0 and line[0] == "PING" ):
					irc.send ("PONG %s\r\n" % line[1])
					#print "PING PONG"
				#Messages
				elif ( len(line) > 1 and line[1] == "PRIVMSG" ):
					#:Termina!termina@93E34681.60FF79BF.CA21EE30.IP PRIVMSG #hurrr :hey there
					#Parses nick and hostname (Termina and termina@93E3....
					self.parseNick(line[0])			
					client.setChannelMessage(str(self.nick[0]), line[2], ' '.join(line[3:len(line)])[1:])
				#Joined channel, got inital nick list
				elif ( len(line) > 1 and line[1] == "353" ):
					client.setNickList(line[4], line[5:])
				elif ( len(line) > 1 and line[1] == "PART" ):
					self.parseNick(line[0])
					#Make sure we don't remove ourself from a channel we just left...
					if ( self.myNick == self.nick[0] ):
						client.removeChannel(line[2].lower())
					else:
						client.removeNick(line[2], self.nick[0])					
				elif ( len(line) > 1 and line[1] == "JOIN" ):
					#Add to nicklist
					self.parseNick(line[0])
					#client.addNick(line[2].lower(), self.nick[0])
				elif ( len(line) > 1 and line[1] == "QUIT" ):
					self.parseNick(line[0])
					#Remove from all channel lists
					newnick = self.nick[0:]
					newnick = newnick[0]
					client.removeNick("all", newnick)
				#For modes, line[2] is channel, line[4] is nickname of person
				elif ( len(line) > 3 and line[3] == "+v" ):
					client.setMode(line[2].lower(), line[4], "+")	
				elif ( len(line) > 3 and line[3] == "-v" ):
					client.removeMode(line[2].lower(), line[4], "+")
				elif ( len(line) > 3 and line[3] == "+o" ):
					client.setMode(line[2].lower(), line[4], "@")
				elif ( len(line) > 3 and line[3] == "-o" ):
					client.removeMode(line[2].lower(), line[4], "@")
				#TOPIC and 332 (topic update) have a different format	
				elif ( len(line) > 1 and line[1] == "TOPIC" ):
					client.setTopic(line[2].lower(), line[3:])
				elif ( len(line) > 1 and line[1] == "332" ):
					client.setTopic(line[3].lower(), line[4:])
				#Nickname we're connecting with is already taken, try again with random nick
				elif ( len(line) > 1 and ( line[1] == "433" or line[1] == "431" ) ):
					self.randomNick()
				#elif ( len(line) > 1 and line[1] == "KICK" ):
					#self.parseNick(line[0])
				#Server or socket sent error; stop listening
				elif ( len(line) > 0 and line[0] == "ERROR" ):
					return -1
						
	def parseNick ( self, line ):
		self.nick = line.split(':')
		self.nick = self.nick[1].split('!')

	#Thread
	def run ( self ):
		self.connect()

	#Returns a random nickname in the format wIRC932854
	def randomNick(self):
		randomName = "wIRC"
		for i in range(6):
			randomName = randomName + str(random.randrange(0,9))	
		self.myNick = randomName		
		self.irc.send ( 'NICK ' + self.myNick + '\r\n' )
		self.irc.send ( 'USER user user user :Hurr\r\n' )

		

#Main window for IRC server
class ircClient(threading.Thread):
	#Array of channels for the server
	channels = []

	def setSocket(self, irc):
		self.irc = irc		
		ircSocket = irc
	#User types a command
	def parseCommand(self, cmd):
		command = cmd.split()
		if ( command[0] == "/join" ):
			self.irc.send ( 'JOIN ' + command[1].lower() + '\r\n' )
			self.channels.append(channelWindow(command[1].lower()))
			self.channels[len(self.channels)-1].setSocket(self.irc)

		elif ( command[0] == "/query" ):
			self.channels.append(channelWindow(command[1]))
			self.channels[len(self.channels)-1].setSocket(self.irc)
			
		elif ( command[0] == "/oper" ):
			self.irc.send ( 'OPER '+ command[1] + ' ' + command[2] + '\r\n')

		elif ( command[0] == "/nick" ):
			self.irc.send ( 'NICK '+ command[1] + '\r\n')
			self.nick = command[1]
	
	def setServerMessage(self, line):
		self.gui.textBox.config(state=NORMAL)
		self.gui.textBox.insert(INSERT,' '.join(line)+"\n")
		self.gui.textBox.see('end')
		self.gui.textBox.config(state=DISABLED)		
			
	def send(self, event):			
		if ( self.gui.chatField.get()[0:1] == "/" ):
			self.parseCommand(self.gui.chatField.get())
		self.gui.chatField.delete(0, END)

	def __init__(self, server):		
		threading.Thread.__init__ ( self )
		self.server = server
		#gui = Toplevel()
			



	#Disconnect from server, close channelWindows
	def quitHandler(self):

		self.irc.shutdown(1)
		self.irc.close()

		for n in range( len(self.channels) ):
			self.channels[n].other.destroy()
			self.channels[n].other.update()
			
		self.gui.destroy() 
		#self.gui.update() 
		sys.exit(0)

	


	#Draw objects on screen
	def createWidgets(self):
		#Text input field
		self.gui.chatField = Entry (self.gui, width=60)
		self.gui.chatField.grid(row=1,column=0) 
		self.gui.chatField.bind('<Return>', self.send)
		self.gui.textBox = ScrolledText(self.gui,width=80,height=20)
		self.gui.textBox.grid(row=0,column=0)

	def setData(self, data):
		self.gui.lbChat.set(data)	

	#Determines if message was to a channel, or to you. Displays on channelWindow object
	def setChannelMessage(self, nick, channel, text):
		date = datetime.datetime.now()
		for n in range( len(self.channels) ):
			if ( channel[0:1] == "#" and self.channels[n].winName == channel ):
				self.channels[n].setText(date.strftime("[%H:%M] ") + "<" + nick + ">" + " " + text)
			elif ( self.channels[n].winName == nick ):		
				self.channels[n].setText(date.strftime("[%H:%M] ") + "<" + nick + ">" + " " + text)
	#Sets inital nickList
	def setNickList(self, channel, nickList):
		for n in range( len(self.channels) ):
			if ( channel[0:1] == "#" and self.channels[n].winName == channel.lower() ):
				self.channels[n].setNickList(nickList)
			
	def addNick(self, channel, nickName):
		for n in range( len(self.channels) ):
			channel = channel[1:]
			if ( channel.lower() == self.channels[n].winName ):
				self.channels[n].addNick(nickName)

	def removeNick(self, channel, nickName):
		for n in range( len(self.channels) ):
			if ( channel == "all" ):
				for i in range( len(self.channels) ):
					self.channels[n].removeNick(nickName)
			elif ( channel.lower() == self.channels[n].winName ):
				self.channels[n].removeNick(nickName)
		
	def setMode(self, channel, nickName, mode):
		for n in range( len(self.channels) ):
			if ( channel.lower() == self.channels[n].winName ):
				self.channels[n].setMode(nickName, mode)

	def removeMode(self, channel, nickName, mode):
		for n in range( len(self.channels) ):
			if ( channel.lower() == self.channels[n].winName ):
				self.channels[n].removeMode(nickName, mode)

	def removeChannel(self, channel):
		for n in range( len(self.channels) ):
			if ( channel.lower() == self.channels[n].winName ):
				del self.channels[n]


	def setTopic(self, channel, topic):
		for n in range( len(self.channels) ):
			if ( channel.lower() == self.channels[n].winName ):
				self.channels[n].setTopic(' '.join(topic))	

	def run(self):
		gui = Tk()
		self.gui = gui
		self.gui.title(self.server)
		self.gui.protocol("WM_DELETE_WINDOW", self.quitHandler)
	        
	        self.createWidgets()	
		self.gui.mainloop()	
		
#Chat/Channel Windows	
class channelWindow(ircClient):
	#Constructor
	def __init__(self, winName, master=ircClient):		
		self.winName = winName
		other = Toplevel()
		self.other = other;
		self.other.protocol("WM_DELETE_WINDOW", self.quitHandler)
		other.topicField = Entry(self.other,width=60,state=DISABLED)
		other.topicField.grid(row=0,column=0)
		other.chatField = Tkinter.Entry (self.other, width=60)
		other.chatField.grid(row=2,column=0)   
		other.chatField.bind('<Return>', self.send)
		other.textBox = ScrolledText(self.other,width=80,height=20)
		other.textBox.grid(row=1,column=0)
		other.textBox.config(state=NORMAL)
		other.textBox.insert(INSERT,"Chatting with " + self.winName + "\n")
		other.textBox.config(state=DISABLED)
		other.nickBox = ScrolledText(self.other,width=15,height=20)
		other.nickBox.grid(row=1,column=1)
		other.grid()
		other.title(self.winName)

	#What we do if a quit event happens
	def quitHandler(self):
		self.irc.send('PART ' + self.winName + ' :Bye\r\n')
		#Should tell ircClient to remove channel from array		
		self.other.destroy() 
		self.other.update() 
		
	def send(self, event):			
		if ( self.other.chatField.get()[0:1] == "/" ):
			self.parseCommand(self.other.chatField.get())
		else:	
			self.irc.send ( 'PRIVMSG ' + self.winName + ' ' + self.other.chatField.get() + '\r\n' )		
			self.other.textBox.config(state=NORMAL)
			self.other.textBox.insert(END, self.other.chatField.get()+'\n')	
			self.other.textBox.see('end')	
			self.other.textBox.config(state=DISABLED)
		self.other.chatField.delete(0, END)

	def setText(self, message):
		self.other.textBox.config(state=NORMAL)
		self.other.textBox.insert(END,message+"\n")
		self.other.textBox.see('end')
		self.other.textBox.config(state=DISABLED)

	def setNickList(self, nickList):
		#time.sleep(1)
		#self.other.nickBox.insert(INSERT, "\n")
		self.other.nickBox.config(state=NORMAL)
		for n in nickList:
			self.other.nickBox.insert(INSERT, n+"\n")
		self.other.nickBox.config(state=DISABLED)

	def addNick(self, nickName):
		time.sleep(1)
		self.other.nickBox.config(state=NORMAL)
		self.other.nickBox.insert(END, nickName+"\n")
		self.other.nickBox.config(state=DISABLED)

	def removeNick(self, nickName):
		#Search for nickName+"\n" so bob2 doesn't match bob
		pos = self.other.nickBox.search(nickName+"\n", 1.0, stopindex=END)
		end = ""
		if ( pos != "" ):
			end = self.other.nickBox.search("\n", pos, stopindex=END)
		if ( end != "" ):
			self.other.nickBox.config(state=NORMAL)
			#+1c is to fully delete the line the nick is on
			self.other.nickBox.delete(pos+" linestart", end + "+1c")
			self.other.nickBox.config(state=DISABLED)
		else:
			pass
		
	def setMode(self, nickName, mode):
		#time.sleep(1)
		pos = self.other.nickBox.search(nickName, 1.0, stopindex=END)
		if ( pos == "" ):
			print "Could not change mode " + mode + " for nick " + nickName
		else:
			self.other.nickBox.config(state=NORMAL)		
			self.other.nickBox.insert(pos, mode)
			self.other.nickBox.config(state=DISABLED)

	def removeMode(self, nickName, mode):
		#time.sleep(1)
		pos = self.other.nickBox.search(mode+nickName, 1.0, stopindex=END)
		self.other.nickBox.config(state=NORMAL)
		self.other.nickBox.delete(pos)
		self.other.nickBox.config(state=DISABLED)

	def setTopic(self, topic):
		time.sleep(1)
		self.other.topicField.config(state=NORMAL)
		self.other.topicField.delete(0,END)
		self.other.topicField.insert(0, "Topic: " + topic[1:])
		self.other.topicField.config(state=DISABLED)

	
			
#Starts program
config = ConfigParser.ConfigParser()
config.read("wIRC.conf")

nick = config.get("server", "nick")
server = config.get("server", "server")
port = config.get("server", "port")
if ( nick == "" ):
	nick = " "
if ( server == "" ):
	server = "irc.bbis.us"
if ( port == "" ):
	port = "6667"
win = ircServer( nick, server, port, 39283 )
win.start()
