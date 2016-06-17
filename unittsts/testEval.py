#!/usr/bin/env python
import ast
import types

__author__ = 'TU Wien'
__copyright__ = "Copyright 2015, TU Wien, Distributed Systems Group"
__license__ = "Apache LICENSE"
__version__ = "2.0"
__maintainer__ = "Daniel Moldovan"
__email__ = "d.moldovan@dsg.tuwien.ac.at"
__status__ = "Prototype"

import os, psutil
import pika, binascii, zlib, pickle, uuid, commands, atexit, logging, sys, time, signal
from lib.Common import TestResult, UnitInstanceInfo, Message, MessageType, SimplePerformanceLogger
from threading import Thread


HEALTH_CENTRAL_QUEUE_IP='128.130.172.191'
USERNAME='daniel'
PASSWORD='daniel'
SYSTEM_NAME='SportsAnalytics'
UNIT_ID='VM.StreamingAnalytics'
#UNIT_UUID is important as it is used to determine the "deployment stack"
#it is automatically generated but sometimes fails
# so it should be PARENT_UUID-[ParentUUID]*-UnitUUID
#for exammple VM_IP-Container_IP-TomcatProcess-WebService meaning WebSerice HostedON TomcatProcess in turn HostedOn Container_IP in turn Hosted on VM_IP
UNIT_UUID='10.99.0.68'
UNIT_TYPE='VirtualMachine'


class TestExecutor(object):



    def testFct(self,method, body):

        self.printMemCPU()

        # list = []
        for i in range(0,100):
            name = method + str(i)
            exec ("def " + name + "(): \n" + body)
            # list.append(name)
            self.printMemCPU()
            # del locals()[name]
            # self.printMemCPU()

        # print "Deleting"
        # for name in list:
        #     del locals()[name]
        #     self.printMemCPU()
        #
        # # create method
        # method = locals().get(method)
        # method_result = method()
        # #delete method
        # del locals()['method']
        # self.printMemCPU()



    def sendMessage(self, ip, system_name, exchange_name, routing_key, credentials, queueName, message):
        try:
          connection = pika.BlockingConnection(
          pika.ConnectionParameters(ip, virtual_host=system_name, credentials=credentials))
          channel = connection.channel()
#         channel.queue_declare(queue=queueName, durable=True)
#         channel.exchange_declare(exchange=exchange_name, type='topic',  durable=True, auto_delete=True)
          channel.basic_publish(exchange=exchange_name, routing_key=routing_key, body=message)
          connection.close()
        except Exception as e:
          print(e)
          time.sleep(10)
          self.sendMessage(ip, system_name, exchange_name, routing_key, credentials, queueName, message)



    def decompress(self, result):
        result.details = zlib.decompress(binascii.unhexlify(result.details))
        return result


    def listenToMessages(self, ip, system_name, unit_name, binding_keys, credentials, queueName):
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(ip, virtual_host=system_name, credentials=credentials))
            channel = connection.channel()
            channel.exchange_declare(exchange=unit_name, type='topic',  durable=True, auto_delete=True)
            channel.queue_declare(queue=queueName, durable=True)

            for binding_key in binding_keys:
                logging.debug(
                    "Binding channel to " + binding_key + " on queue " + queueName + " on UNIT_ID " + UNIT_ID + " on server " + ip)
                channel.queue_bind(exchange=unit_name, queue=queueName, routing_key=binding_key)

            logging.debug("Waiting for messages ...")
            channel.basic_consume(self.callback, queue=queueName)
            channel.start_consuming()
        except Exception as ex:
            logging.warning(str(ex), exc_info=True)
        #if we reach this we must reconnect
        logging.debug("Reconnecting ..")
        time.sleep(10)
        self.listenToMessages(ip, system_name, unit_name, binding_keys, credentials, queueName)

    def exit_handler(self, HEALTH_CENTRAL_QUEUE_IP, SYSTEM_NAME, credentials, queueName, unitDetails):
        logging.debug("Shutting down...")
        iAmDeadMesssage = Message(type=MessageType.UnitInstanceInformation, content=unitDetails)
        stringMessage = pickle.dumps(iAmDeadMesssage)
        # send I am dead message
        self.sendMessage(HEALTH_CENTRAL_QUEUE_IP, SYSTEM_NAME, SYSTEM_NAME,SYSTEM_NAME+  ".lifecycle.dead", credentials, "dead",
                                 stringMessage)
        # delete tests and results queues
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(HEALTH_CENTRAL_QUEUE_IP, virtual_host=SYSTEM_NAME, credentials=credentials))
        channel = connection.channel()
        logging.debug("Deleting used queue " + queueName)
        channel.queue_delete(queue=queueName + "-Results")
        channel.queue_delete(queue=queueName + "-Tests")
        logging.debug("Deleted queue " + queueName)
        connection.close()

    def exit_sig_handler(self, signum, frame):
        self.exit_handler(self.HEALTH_CENTRAL_QUEUE_IP, self.SYSTEM_NAME,
                          self.credentials, self.queueName, self.unitDetails)
        # global shutdown_flag
        # shutdown_flag = True
        logging.debug("Exiting ...")
        sys.exit(0)

    def printMemCPU(self):
       process = psutil.Process(os.getpid())
       mem = process.memory_info().rss
       print(str(mem))

if __name__ == '__main__':
    args = sys.argv

    t = TestExecutor()


    test=\
" os = __import__('os')\n\
 free = float(os.popen(\"free | grep Mem | awk '{print $4*100.0/$2}'\").read())\n\
 meta = {}\n\
 meta[\"type\"]=\"OS Usage\"\n\
 if free > 20:\n\
    successful=True\n\
 else:\n\
    successful=False\n\
 return TestResult(successful=successful, details=free, meta=meta)"

    t.testFct("AAA",test)

    # print(eval(test))
    #compile text, not read from file so indicating it is string, and
    #exec due to sequence of instructions
    # dynf = types.FunctionType(compile(test,'<string>','exec'), {})
    # result  = dynf()
    # print result
    #
    # astTST = ast.parse(test)
    # result = ast.literal_eval(astTST)
    # print(result)
    #
    # exec ("def " + "AAAA" + "(): \n" + test)
    #
    # possibles = globals().copy()
    # possibles.update(locals())
    # method = possibles.get("AAAA")
    #
    # method_result = method()
    # print method_result