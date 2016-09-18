#!/usr/bin/python
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer

import cgi
import filter
import re

PORT_NUMBER = 80

#This class will handles any incoming request from
#the browser 
class myHandler(BaseHTTPRequestHandler):
    
    #Handler for the GET requests
    def do_POST(self):
        if None != re.search('/*', self.path):
            ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
            if ctype == 'application/json':
                length = int(self.headers.getheader('content-length'))
                data = cgi.parse_qs(self.rfile.read(length), keep_blank_values=1)
                chat_room = self.path.split('/')[-1]
                filter.add_context(chat_room, data)
                print "record from %s is recieved" % chat_room
            else:
                data = {}
                self.send_response(200)
                self.end_headers()
        else:
            self.send_response(403)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
        return



try:
    #Create a web server and define the handler to manage the
    #incoming request
    # PUT INIT CODE HERE

    ###################
    server = HTTPServer(('', PORT_NUMBER), myHandler)
    print 'Started httpserver on port ' , PORT_NUMBER
    
    #Wait forever for incoming htto requests
    server.serve_forever()

except KeyboardInterrupt:
    print '^C received, shutting down the web server'
    server.socket.close()
