
#!/usr/bin/env python
__author__ = 'TU Wien'
__copyright__ = "Copyright 2015, TU Wien, Distributed Systems Group"
__license__ = "Apache LICENSE"
__version__ = "2.0"
__maintainer__ = "Daniel Moldovan"
__email__ = "d.moldovan@dsg.tuwien.ac.at"
__status__ = "Prototype"

from xml.dom.minidom import parseString
import subprocess
import sys
import httplib, csv
import base64
import string
import xml.etree.ElementTree as ET


host = "localhost"
url = "/haproxy_stats"
username = 'comot'
password = 'comot'

#means connection rate
target_stat="rate"

def readStats():
 os = __import__('os')
 base64 = __import__('base64')
 httplib = __import__('httplib')

 targetID = '10.99.0.33'
 host ='128.130.172.216'
 url = "/haproxy_stats"
 username = 'comot'
 password = 'comot'

 #read haproxy stat web page and search for targetID in servers list

 auth = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
 webservice = httplib.HTTP(host)
 # write your headers
 webservice.putrequest("POST", url)
 webservice.putheader("Host", host)
 webservice.putheader("User-Agent", "Python http auth")
 webservice.putheader("Content-type", "text/html; charset=\"UTF-8\"")
 webservice.putheader("Authorization", "Basic %s" % auth)
 webservice.endheaders()

 statuscode, statusmessage, header = webservice.getreply()
 res = webservice.getfile().read()
 #print 'Content: ', res
 successful = str(targetID) in res
 details = res

 meta = {}
 meta["type"]="Checks if web server register as backend server in HAProxy by parsing HAProxy Stats Web UI"
 print successful

if __name__ == '__main__':
 targetID='Tomcat'
 executorID='128.130.172.216'
 host='10.99.0.34'
 os = __import__('os')
 base64 = __import__('base64')
 httplib = __import__('httplib')

 url = "/haproxy_stats"
 username = 'comot'
 password = 'comot'

 #read haproxy stat web page and search for targetID in servers list

 auth = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
 webservice = httplib.HTTP(host)
 # write your headers
 webservice.putrequest("POST", url)
 webservice.putheader("Host", host)
 webservice.putheader("User-Agent", "Python http auth")
 webservice.putheader("Content-type", "text/html; charset=\"UTF-8\"")
 webservice.putheader("Authorization", "Basic %s" % auth)
 webservice.endheaders()
 statuscode, statusmessage, header = webservice.getreply()
 res = webservice.getfile().read()
 #print 'Content: ', res
 successful = str(host) in res
 if successful:
   details = "Server " + str(host) + " found in haproxy cfg"
 else:
   details = "Server " + str(host) + " NOT found in haproxy cfg for " + str(executorID)
 meta = {}
 meta["type"]="Checks if web server register as backend server in HAProxy by parsing HAProxy Stats Web UI"

 print successful

