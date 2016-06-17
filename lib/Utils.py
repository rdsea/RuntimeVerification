#!/usr/bin/env python
from Queue import Queue
from lib.Model import User, Unit

__author__ = 'TU Wien'
__copyright__ = "Copyright 2015, TU Wien, Distributed Systems Group"
__license__ = "Apache LICENSE"
__version__ = "2.0"
__maintainer__ = "Daniel Moldovan"
__email__ = "d.moldovan@dsg.tuwien.ac.at"
__status__ = "Prototype"

#currently implements functionality to interract with message queues

import pika, logging, pickle, urllib, urllib2, sys, httplib, base64, smtplib #, sqlite3, sqlitebck
from threading import Thread, Timer
import time


class QueueUtil(object):

    INTERRUPTED = "interrupted"

    __deadQueue = {}
    
    def __markQueueDead(self, queueName):
        QueueUtil._QueueUtil__deadQueue[queueName] = True


    def listenToMessages(self, ip, vHost, binding_keys, username,password, exchange, queueName, callback, arguments={}):
        t = Thread(target=QueueUtil().__listenToMessages, args=(ip, vHost, binding_keys, username,password, exchange, queueName, callback, arguments))
        t.setDaemon(True)
        t.start()


    def __listenToMessages(self,ip, vHost, binding_keys, username,password, exchange, queueName, callback, arguments):
        pika_logger = logging.getLogger('pika')
        pika_logger.setLevel(logging.CRITICAL)
        try:
            credentials = pika.PlainCredentials(username,password)
            parameters = pika.URLParameters(str('amqp://'+credentials.username+':'+credentials.password+'@'+str(ip)+':5672/'+vHost))
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            channel.exchange_declare(exchange=exchange, exchange_type='topic', durable=True, auto_delete=True)
            channel.queue_declare(queue=queueName, durable=True)

            for binding_key in binding_keys:
                logging.debug("Binding channel to " + binding_key + " on queue " + queueName + " on exchange " + exchange + " on server " + ip)
                channel.queue_bind(exchange=exchange, queue=queueName, routing_key=binding_key)
                channel.basic_consume(consumer_callback=callback, queue=queueName)
                channel.start_consuming()
        except Exception as ex:
            logging.warning(str(ex), exc_info=True)
            if not queueName in QueueUtil._QueueUtil__deadQueue:
                logging.warning("Connection dropped. Reconnecting to listen to " + queueName)
                time.sleep(10)
                self.__listenToMessages(ip, vHost, binding_keys, username,password, exchange, queueName, callback, arguments)
            else:
                del QueueUtil._QueueUtil__deadQueue[queueName]


    def removeQueue(self, ip, vHost,  queueName, username,password):

            self.__markQueueDead(queueName)

            try:
                credentials = pika.PlainCredentials(username,password)
                parameters = pika.URLParameters(str('amqp://'+credentials.username+':'+credentials.password+'@'+str(ip)+':5672/'+vHost))
                connection = pika.BlockingConnection(parameters)
                channel = connection.channel()
                channel.queue_delete(queue=queueName)
                connection.close()

            except Exception as ex:
                logging.warning(str(ex), exc_info=True)


    @staticmethod
    def sendMessage(ip, vHost, exchange, routing_key, username,password, queueName, message):
        try:
            # properties for persistent message delivery
            properties = pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            )
            credentials = pika.PlainCredentials(username,password)
            #parameters = pika.URLParameters(str('amqp://'+credentials.username+':'+credentials.password+'@'+str(ip)+':5672/'+vHost))
            #connection = pika.BlockingConnection(parameters)
            connection = pika.BlockingConnection(pika.ConnectionParameters(str(ip), virtual_host=str(vHost),
                                                                           credentials=credentials))
            channel = connection.channel()
            channel.queue_declare(queue=queueName, durable=True)
            channel.exchange_declare(exchange=exchange, exchange_type='topic', durable=True, auto_delete = True)
            channel.queue_bind(exchange=exchange, queue=queueName, routing_key=routing_key)
            channel.basic_publish(exchange=exchange, routing_key=routing_key, body=message)
            connection.close()
        except Exception as e:
            logging.debug(e)

    @staticmethod
    def addUser(ip, credentials, userToAdd):
        user_pass=base64.encodestring('%s:%s' % (credentials.username, credentials.password)).replace('\n', '')
        connection =  httplib.HTTPConnection(ip+":"+str(15672))
        logging.debug('Adding user ' +  str(userToAdd.password))
        body_content =  '{"password":"' + str(userToAdd.password) + '","tags":"policymaker"}'
        headers={
                'Content-Type':'application/json; charset=utf-8',
                'Authorization': "Basic %s" % user_pass
        }
        logging.debug('Calling ' +  str( '/api/users/' + userToAdd.username))
        connection.request('PUT', '/api/users/' + userToAdd.username, body=body_content,headers=headers)
        result = connection.getresponse()
        logging.debug(result.status)
        logging.debug(result.msg)

    @staticmethod
    def removeUser(ip, credentials, userToAdd):
        user_pass=base64.encodestring('%s:%s' % (credentials.username, credentials.password)).replace('\n', '')
        connection =  httplib.HTTPConnection(ip+":"+str(15672))
        logging.debug('Removing user ' +  str(userToAdd.password))
        body_content =  ''
        headers={
                'Content-Type':'application/json; charset=utf-8',
                'Authorization': "Basic %s" % user_pass
        }

        connection.request('DELETE', '/api/users/' + userToAdd.username, body=body_content,headers=headers,)
        result = connection.getresponse()
        logging.debug(result.status)
        logging.debug(result.msg)

    @staticmethod
    def addSystemQueueHost(ip, credentials, system):
        user_pass=base64.encodestring('%s:%s' % (credentials.username, credentials.password)).replace('\n', '')
        connection =  httplib.HTTPConnection(ip+":"+str(15672))
        logging.debug('Adding vHost ' +  str(system.name))
        body_content =  ''
        headers={
                'Content-Type':'application/json; charset=utf-8',
                'Authorization': "Basic %s" % user_pass
        }

        connection.request('PUT', '/api/vhosts/' + str(system.name), body=body_content,headers=headers)
        result = connection.getresponse()
        logging.debug(result.status)
        logging.debug(result.msg)

    @staticmethod
    def removeSystemQueueHost(ip, credentials, system):
        user_pass=base64.encodestring('%s:%s' % (credentials.username, credentials.password)).replace('\n', '')
        connection =  httplib.HTTPConnection(ip+":"+str(15672))
        logging.debug('Adding vHost ' +  str(system.name))
        body_content =  ''
        headers={
                'Content-Type':'application/json; charset=utf-8',
                'Authorization': "Basic %s" % user_pass
        }

        connection.request('DELETE', '/api/vhosts/' + system.name, body=body_content,headers=headers)
        result = connection.getresponse()
        logging.debug(result.status)
        logging.debug(result.msg)


    @staticmethod
    def addUserAccessToSystem(ip, credentials, userToAdd, system):
        user_pass=base64.encodestring('%s:%s' % (credentials.username, credentials.password)).replace('\n', '')
        connection =  httplib.HTTPConnection(ip+":"+str(15672))
        logging.debug('Adding user %s access to vhost %s' %(userToAdd.username, system.name))
        body_content = '{"scope":"client","configure":".*","write":".*","read":".*"}'
        headers={
                'Content-Type':'application/json; charset=utf-8',
                'Authorization': "Basic %s" % user_pass
        }

        connection.request('PUT', '/api/permissions/' + system.name + '/'  + userToAdd.username, body=body_content,headers=headers)
        result = connection.getresponse()
        logging.debug(result.status)
        logging.debug(result.msg)


    @staticmethod
    def removeUserAccessToSystem(ip, credentials, userToAdd, system):
        user_pass=base64.encodestring('%s:%s' % (credentials.username, credentials.password)).replace('\n', '')
        connection =  httplib.HTTPConnection(ip+":"+str(15672))
        logging.debug('Adding user %s access to vhost %s'  %(userToAdd.username, system.name))
        body_content = ''
        headers={
                'Content-Type':'application/json; charset=utf-8',
                'Authorization': "Basic %s" % user_pass
        }

        connection.request('DELETE', '/api/permissions/' + system.name + '/'  + userToAdd.username , body=body_content,headers=headers)
        result = connection.getresponse()
        logging.debug(result.status)
        logging.debug(result.msg)


class MailUtil(object):

    @staticmethod
    def sendMail(to, user, password,smtpServerName, smtpServerPort, subject, content):
        if to:
            smtpserver = smtplib.SMTP(smtpServerName,smtpServerPort)
            smtpserver.ehlo()
            smtpserver.starttls()
            smtpserver.ehlo() # extra characters to permit edit
            smtpserver.login(user, password)
            header = 'To:' + to + '\n' + 'From: ' + to + '\n' + 'Subject: ' + subject  + '\n'
            msg = header + '\n ' + content +'\n\n'
            smtpserver.sendmail(user, to, msg)
            smtpserver.close()

#not sure if IO was performance bottleneck
# class DBUtil(object):
#     @staticmethod
#     def copySQLiteDB(dbURL1, dbURL2):
#         conn1 = sqlite3.connect(dbURL1)
#         conn2 = sqlite3.connect(dbURL2)
#         sqlitebck.copy(conn1, conn2)
#     @staticmethod
#     def scheduleBackup(dbURL1, dbURL2, backupIntervalInSeconds):
#        DBUtil.copySQLiteDB(dbURL1,dbURL2)
#        t = Timer(backupIntervalInSeconds, DBUtil.scheduleBackup, args=[dbURL1,dbURL2,backupIntervalInSeconds ])
#        t.start()


class ThreadFunction(Thread):
    # with **kwargs you can call with functionToRun=FUNCTION, arg1=X, arg2=y, and then call FUNCTION( **kwargs)
    # and the arguments values will be set correctly
    def __init__(self, functionToRun, **kwargs):
        Thread.__init__(self)
        self.functionToRun = functionToRun
        self.kwargs = kwargs

    def run(self):
       self.functionToRun(**self.kwargs)

#logging.basicConfig(level=logging.DEBUG)

#QueueUtil.removeSystemQueueHost("128.130.172.216", pika.PlainCredentials('mela', 'mela'), Unit(id="SystemA"))


# QueueUtil.addUser("128.130.172.216", pika.PlainCredentials('mela', 'mela'), User(username="AAAA", password="BBBBB"))


#QueueUtil.addSystemQueueHost("128.130.172.216", pika.PlainCredentials('mela', 'mela'), Unit(id="SystemA"))
#QueueUtil.addUserAccessToSystem("128.130.172.216", pika.PlainCredentials('mela', 'mela'), User(username="AAAA", password="BBBBB"), Unit(id="SystemA"))

#QueueUtil.removeUserAccessToSystem("128.130.172.216", pika.PlainCredentials('mela', 'mela'), User(username="AAAA", password="BBBBB"),Unit(id="SystemA"))


#QueueUtil.removeUser("128.130.172.216", pika.PlainCredentials('mela', 'mela'), User(username="AAAA", password="BBBBB"))
