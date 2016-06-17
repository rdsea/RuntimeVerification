#!/usr/bin/env python
__author__ = 'TU Wien'
__copyright__ = "Copyright 2015, TU Wien, Distributed Systems Group"
__license__ = "Apache LICENSE"
__version__ = "2.0"
__maintainer__ = "Daniel Moldovan"
__email__ = "d.moldovan@dsg.tuwien.ac.at"
__status__ = "Prototype"


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

    def __init__(self,HEALTH_CENTRAL_QUEUE_IP, SYSTEM_NAME, UNIT_ID, binding_keys, credentials, queueName, unitDetails):
        self.HEALTH_CENTRAL_QUEUE_IP=HEALTH_CENTRAL_QUEUE_IP
        self.SYSTEM_NAME=SYSTEM_NAME
        self.UNIT_ID=UNIT_ID
        self.binding_keys=binding_keys
        self.credentials=credentials
        self.queueName=queueName
        self.unitDetails = unitDetails

    def callback(self, ch, method, properties, body):
        global binding_keys, queueName, credentials, UNIT_ID
        ch.basic_ack(delivery_tag=method.delivery_tag)
        result = None
        try:
            logging.debug("Received " + str(body))
            message = pickle.loads(body)

            if not message.type == MessageType.Test:
                raise ValueError("Received message type " + str(message.type) + " instead of MessageType.Test=" + str(MessageType.Test))

            test = message.content
            result = TestResult(systemID=SYSTEM_NAME, username=USERNAME, testID=test.name, executionID=test.executionID, executorUnit=test.executorUnit, targetUnit=test.targetUnit)
            testName = test.name
            logging.debug("META " + str(test.meta))
            logging.debug("TEST " + str(test.test))
            logging.debug("Delivery ACK. Defining test")

            exec ("def " + testName + "(): \n" + test.test)

            possibles = globals().copy()
            possibles.update(locals())
            method = possibles.get(testName)

            method_result = method()
            result.successful = method_result.successful
            result.details = method_result.details
            result.meta = method_result.meta

        except Exception as e:
            logging.debug(e)
            if not result:
               result = TestResult(testID="GeneralFailure", executionID="0", executorUnit=None)
            result.meta["type"] = "Test Invocation Failure"
            result.successfull = False
            result.details = str(e)
        result.meta["origin.uuid"] = UNIT_UUID
        result.meta["origin.id"] = UNIT_ID

        message = Message(type=MessageType.TestResult, content=result)

        self.sendMessage(HEALTH_CENTRAL_QUEUE_IP, SYSTEM_NAME,UNIT_ID, SYSTEM_NAME + "." + UNIT_UUID + ".results", credentials,
                                 UNIT_UUID + "-Results", pickle.dumps(message))


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


if __name__ == '__main__':
    args = sys.argv

    logging.basicConfig(filename="./executor_" + UNIT_UUID + ".log", level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
    logging.info("Started test executor for " + UNIT_UUID)
    #remove pika chatter
    logging.getLogger('pika').setLevel(logging.WARNING)

    queueName = str(UNIT_UUID) + "-Tests"
    binding_keys = [SYSTEM_NAME + "." + UNIT_UUID + ".tests"]
    credentials = pika.PlainCredentials(USERNAME, PASSWORD)

    #start logging performance
    p = SimplePerformanceLogger("./performance_" + UNIT_UUID + ".csv")
    p.logPerformance(5)

    # send I am alive message
    unitDetails = UnitInstanceInfo(id=UNIT_ID, uuid=UNIT_UUID, type=UNIT_TYPE, system=SYSTEM_NAME, username=USERNAME, password=PASSWORD)
    iAmAliveMesssage = Message(type=MessageType.UnitInstanceInformation, content=unitDetails)
    stringMessage = pickle.dumps(iAmAliveMesssage)
    logging.debug("Sending I am alive message " + stringMessage)

    executor = TestExecutor(HEALTH_CENTRAL_QUEUE_IP, SYSTEM_NAME, UNIT_ID, binding_keys, credentials, queueName, unitDetails)

    executor.sendMessage(HEALTH_CENTRAL_QUEUE_IP, SYSTEM_NAME, SYSTEM_NAME, SYSTEM_NAME+ ".lifecycle.alive", credentials, "alive", stringMessage)
    # listen to messages
    # listen to messages
    signal.signal(signal.SIGTERM, executor.exit_sig_handler) #service stop
    signal.signal(signal.SIGINT, executor.exit_sig_handler)  # ctr-c
    executor.listenToMessages(HEALTH_CENTRAL_QUEUE_IP, SYSTEM_NAME, UNIT_ID, binding_keys, credentials, queueName)

