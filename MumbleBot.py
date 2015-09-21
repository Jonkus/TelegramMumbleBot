#!/usr/bin/env python2.7

'''
    MumbleBot - A python TelegramBot
    Copyright (C) 2015 Jonathan Kuhse

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''

import telegram
from telegram.chataction import ChatAction
from pymumble import Mumble
import time
import database as db
import copy
from thread import start_new_thread
import datetime

API_KEY = open('api.key', 'r').readline()


HELP_MESSAGE = '''
Hi I am MumbleBot I will inform you when a user connects to your murmur!
- /help - Show this help
- /start hostname:port- Start the bot and connect to a Murmur server
- /end - End the bot
'''

bot = None

servers = []
"""
server[0] -> server_id
server[1] -> Mumble-client
server[2] -> userlist
server[3] -> userlist-changed-flag
"""

USER="TelegramBot"
#CERT="/home/nonex/src/mumblebot/telegrambot.p12"
CERT=None
RECONNECT=True
DEBUG=False

def start_clients():
    """
    start Mumble-Clients for all saved servers
    """
    global servers
    # first we fetch all servers from our database
    server_liste = db.check_servers()
    servers = []
    for serverdata in server_liste:
        servers.append([ \
            serverdata[0],\
            Mumble(serverdata[1], int(serverdata[2]), USER, serverdata[3], CERT, RECONNECT, DEBUG), \
            [], \
            False])
    # now lets connect to all servers
    for client in servers:
        print datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S') + " connecting to server: " + str(client[0])
        client[1].start()
    # wait for all connections to start
    for client in servers:
        client[1].is_ready()
    print datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S') +" "+ "all clients started and ready"

def get_users():
    """
    Save all connected users in the server list 
    """
    global servers
    while True:
        time.sleep(1)
        try:
            for server in servers:
                state = server[1].users
                userlist = []
                bot_connected = False
                for id in state:
                    user = state[id].get("name")
                    if user != "TelegramBot":
                        userlist.append(user)
                    else:
                        bot_connected = True
                server[3] = False
                for user in userlist:
                    if user not in server[2]:
                        server[3] = True
                        print datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S') +" new users connected on server " + str(server[0])
                server[2] = copy.copy(userlist)
                # Bot is not connected and tries to reconnect
                if not bot_connected:
                    start_clients()
        except Exception as e:
            print datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S') + str(e)
        

def init():
    global bot
    start_clients()
    bot = telegram.Bot(token = API_KEY)
    start_new_thread(sendingLoop, ())
    start_new_thread(get_users, ())
    startMainLoop()

def new_server(chat_id, message):
    global servers
    if " " in message:
        message = message.split(" ")[1]
    else:
        sendMessage(chat_id, "Usage: /start hostname:port")
        return
    if ":" in message:
        hostname = message.split(":")[0]
        port = message.split(":")[1]
    else:
        if len(message) > 0:
            hostname =  message
            port = "64738"
        else:
            sendMessage(chat_id, "Usage: /start hostname:port")
            return
    # TODO: Check if connectable
    server_id = db.add_server(chat_id, hostname, port , "")
    for server in servers:
        if int(server[0]) == int(server_id):
            # Client already connected to server
            sendMessage(chat_id, "I am connected to your server")
            return
    try:
        connection = Mumble(hostname, int(port), USER, "", CERT, RECONNECT, DEBUG)
        connection.start()
        connection.is_ready()
        servers.append([ \
                server_id,\
                connection, \
                [], \
                False])
        sendMessage(chat_id, "I connected to your server")
    except Exception as e:
        print datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S') +" " +str(e)
        sendMessage(chat_id, "Could not Connect to thos server: " + hostname + ":" + str(port))


def deleteChat(chat_id):
    try:
        print datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S') +" "+"deleting instances of" + str(chat_id)
        db.del_chat(chat_id)
    except Exception as e:
        print datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S') +" "+str(e)

def sendMessage(chat_id, message):
    try:
        bot.sendChatAction(chat_id, ChatAction.TYPING)
        bot.sendMessage(chat_id, message)
    except Exception as e:
        print datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S') +" "+str(e)

def startMainLoop():
    messageOffset = 0
    print datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S') +" "+'Starting MainLoop'

    while True:
        try:
            updates = bot.getUpdates(offset = messageOffset, limit = 1, timeout = 2)
    
            if len(updates) != 0:
                for u in updates:
                    
                    messageOffset = u.update_id + 1
                    chat_id = u.message.chat_id
                    message = u.message.text

                    print datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S') +" " +message

                    if message.startswith(u'/start'):
                        start_new_thread(new_server, (chat_id, message,))
                    elif message.startswith(u'/end'):
                        deleteChat(chat_id)
                    elif message.startswith(u'/help'):
                        sendMessage(chat_id, HELP_MESSAGE)
        except Exception as e:
            print str(e)
            time.sleep(5)

def sendingLoop():
    while True:
        for server in servers:
            if server[3]:
                chat_id = db.get_chat_id(server[0])
                message = "Users connected to your Murmur-Server:\n"
                for user in server[2]:
                    message += " > " + user + "\n"
                print datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S') +" "+"sending message to " + str(chat_id)
                sendMessage(chat_id, message)
                server[3] = False



init()
