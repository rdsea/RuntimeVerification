#!/usr/bin/env python
import sys

__author__ = 'TU Wien'
__copyright__ = "Copyright 2015, TU Wien, Distributed Systems Group"
__license__ = "Apache LICENSE"
__version__ = "2.0"
__maintainer__ = "Daniel Moldovan"
__email__ = "d.moldovan@dsg.tuwien.ac.at"
__status__ = "Prototype"


import pika, binascii, zlib, urllib2, pickle
#from lib.Common import Test

RabbitMQ_IP='localhost'
 

def downloadFile(url):

  attempts = 0

  while attempts < 3:
    try:
        response = urllib2.urlopen(url, timeout = 5)
        content = response.read()
        return content
        break
    except urllib2.URLError as e:
        attempts += 1
        print type(e)


def sendMessage(ip, vHost, exchange, routing_key, credentials, message):
 connection = pika.BlockingConnection(pika.ConnectionParameters(ip, virtual_host=vHost, credentials=credentials))
 channel = connection.channel()
 channel.basic_publish(exchange=exchange, routing_key=routing_key, body=message)
 connection.close()

def compress(result):
     result.message = binascii.hexlify(zlib.compress(result.message))
     return result


if __name__=='__main__':
    # tst_url="http://localhost/iCOMOTTutorial/files/"
    # tst_name="lazyTST"
    # tstContent = downloadFile(tst_url +  tst_name + ".py")
    # tst = Test()
    # tst.meta["name"]= tst_name
    # tst.test=tstContent
    # credentials = pika.PlainCredentials('service1', 'service1')
    # sendMessage(RabbitMQ_IP, "service1", "testsexecutor","interests.A", credentials , pickle.dumps(tst))

    args = sys.argv

    print len(args)
    print args




 
