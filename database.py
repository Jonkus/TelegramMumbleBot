#!/usr/bin/env python2.7

import MySQLdb as mysql

dhost = 'localhost'
duser = 's4y'
dpwd = 'ginaph9maureiCohr9a'
dname = 's4y_mumblebot'
db = mysql.connect(dhost, duser, dpwd, dname)

def add_server(chat_id, host, port, password):
    db = mysql.connect(dhost, duser, dpwd, dname)
    cur = db.cursor()
    try:
        cur.execute("INSERT INTO servers(hostname, port, password) VALUES( %s, %s, %s)", (host, str(port), password,))
    except Exception as e:
        print str(e)
    try:
        #print "SELECT server_id from servers WHERE hostname='"+host+"' AND  port="+str(port)+";"
        cur.execute("SELECT server_id from servers WHERE hostname=%s AND  port=%s ;", (host, str(port),))
        server_id = cur.fetchall()[0][0]
    except Exception as e:
        print str(e)
    try:
        cur.execute("INSERT INTO chats(chat_id, server_id) \
            VALUES ( %s, %s );", (str(chat_id), str(server_id),) )
        db.close()
        return server_id
    except Exception as e:
        print str(e)

def get_chat_id(server_id):
    db = mysql.connect(dhost, duser, dpwd, dname)
    cur = db.cursor()
    try:
        cur.execute("SELECT chat_id from chats WHERE server_id=%s ;", (str(server_id),))
        db.close()
        return cur.fetchall()[0][0]
    except Exception as e:
        print str(e)
    

def check_servers():
    db = mysql.connect(dhost, duser, dpwd, dname)
    cur = db.cursor()
    with db:
        cur.execute("SELECT * FROM servers;")
    
    servers = cur.fetchall()
    db.close()
    return servers

def del_chat(id):
    db = mysql.connect(dhost, duser, dpwd, dname)
    cur = db.cursor()
    cur.execute("DELETE from chats WHERE chat_id = %s;", (id, ) )
    db.close()
    


def del_server(id):
    db = mysql.connect(dhost, duser, dpwd, dname)
    cur = db.cursor()
    cur.execute("DELETE from servers WHERE server_id like " + id + ";")
    db.close()
