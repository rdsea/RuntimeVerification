#!/usr/bin/env python
__author__ = 'TU Wien'
__copyright__ = "Copyright 2015, TU Wien, Distributed Systems Group"
__license__ = "Apache LICENSE"
__version__ = "2.0"
__maintainer__ = "Daniel Moldovan"
__email__ = "d.moldovan@dsg.tuwien.ac.at"
__status__ = "Prototype"


import pika, binascii, zlib, pickle
from lib.Common import TestResult


RabbitMQ_IP='localhost'



class Message(object):
    routing_key=''
    body=''

def callback(ch, method, properties, body):
    message = pickle.loads(body)
    print str(message.successfull)
    print str(message.details)
    ch.basic_ack(delivery_tag = method.delivery_tag)

def decompress(result):
    result.details = zlib.decompress(binascii.unhexlify(result.details))
    return result

def listenToMessages(ip, vHost, binding_keys, credentials, queueName):
 connection = pika.BlockingConnection(pika.ConnectionParameters(ip, virtual_host=vHost, credentials=credentials))
 channel = connection.channel()
 channel.exchange_declare(exchange='someexchange', type='topic')
 channel.queue_declare(queue=queueName)

 for binding_key in binding_keys:
  channel.queue_bind(exchange='someexchange',
                       queue=queueName,
                       routing_key=binding_key)
 
  channel.basic_consume(callback, queue=queueName)
  channel.start_consuming()

 

if __name__=='__main__':
    binding_keys=["interests.A","interests.B"]
    credentials = pika.PlainCredentials('service1', 'service1')
    listenToMessages(RabbitMQ_IP, "service1", binding_keys, credentials,"MyQueue")


