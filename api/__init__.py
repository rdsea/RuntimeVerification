#!/usr/bin/env python
import ConfigParser
import commands
import logging
from datetime import timedelta
import pika
from lib.Control import Controller
from lib.Model import User
from os import listdir
from os.path import isfile, join
from lib.ModelDAO import TestDAO

__author__ = 'TU Wien'
__copyright__ = "Copyright 2015, TU Wien, Distributed Systems Group"
__license__ = "Apache LICENSE"
__version__ = "2.0"
__maintainer__ = "Daniel Moldovan"
__email__ = "d.moldovan@dsg.tuwien.ac.at"
__status__ = "Prototype"

#file which initializes the platform, injects dependencies, and starts everything

from flask import Flask
import os
import sys


app = Flask(__name__)

pid = str(os.getpid())
pidfile = "/tmp/health-management.pid"

#create pid file
if not os.path.isfile(pidfile):
    file(pidfile, 'w').write(pid)

app.secret_key = 'H3althM@nagementS!i2stem'
#expire session
app.permanent_session_lifetime = timedelta(hours=3)

queueIP = 'localhost'
queueCredentials = User(username='guest', password='guest')

centralIP = 'localhost'
centralPublicIP = None
centralPort= 5001
dbBackupInterval = 60

profilingEnabled = False

databasePath ="./runtime/system_db.sql"
loggingPath = "./runtime/log.log"
# testsSimpleConfigPath = "./config/tests.simple.specification"
# testsComplexConfigPath = "./config/tests.complex.specification"

#loading system configuration
config = ConfigParser.RawConfigParser()
config.read("./config/config.properties")

QueueConfigSection = "QueueProperties"
OverallPropertiesSection = "OverallProperties"
TemporaryFilesPropertiesSection = "TemporaryFilesProperties"

#load dynamic configuration
if config.has_section(QueueConfigSection):
   if config.has_option(QueueConfigSection, "rabbitMQ.ip"):
       queueIP = config.get(QueueConfigSection, "rabbitMQ.ip")

   if config.has_option(QueueConfigSection, "rabbitMQ.credentials"):
       credentials = config.get(QueueConfigSection, "rabbitMQ.credentials").split(":")
       queueCredentials = User(username=credentials[0].strip(), password=credentials[1].strip())

   if config.has_option(QueueConfigSection, "database.location"):
       databasePath = config.get(QueueConfigSection, "database.location")

   if config.has_option(QueueConfigSection, "database.backup.interval"):
       databasePath = config.get(QueueConfigSection, "database.backup.interval")

if config.has_section(OverallPropertiesSection):
     if config.has_option(OverallPropertiesSection, 'health.central.ip'):
         centralIP = config.get(OverallPropertiesSection, 'health.central.ip')
     if config.has_option(OverallPropertiesSection, 'health.central.ip.public'):
         centralPublicIP = config.get(OverallPropertiesSection, 'health.central.ip.public')
     else:
         centralPublicIP = centralIP
     if config.has_option(OverallPropertiesSection, 'health.central.port'):
         centralPort=int(config.get(OverallPropertiesSection, 'health.central.port'))

     if config.has_option(OverallPropertiesSection, 'health.central.profiling'):
         if config.get(OverallPropertiesSection, 'health.central.profiling') == 'True':
           profilingEnabled = True


if config.has_section(TemporaryFilesPropertiesSection):
     if config.has_option(TemporaryFilesPropertiesSection, 'database.location'):
         databasePath=config.get(TemporaryFilesPropertiesSection, 'database.location')
     if config.has_option(TemporaryFilesPropertiesSection, 'logging.location'):
         loggingPath=config.get(TemporaryFilesPropertiesSection, 'logging.location')

#ensure we start fresh
if config.has_section(OverallPropertiesSection):
    if config.has_option(OverallPropertiesSection, 'health.central.start.fresh'):
        if config.get(OverallPropertiesSection, 'health.central.start.fresh') == 'True':
           commands.getoutput("rm " + databasePath)

#start with fresh log
commands.getoutput("rm " + loggingPath)

FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
# logging.basicConfig( filename=loggingPath, format=FORMAT, level=logging.DEBUG)
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
#avoid pika chatter
logging.getLogger('pika').setLevel(logging.WARNING)

controller = Controller(queueCredentials= pika.PlainCredentials(queueCredentials.username, queueCredentials.password),
                        queueIP=queueIP, dbPath=databasePath, dbBackupInterval=dbBackupInterval)

#add generic tests in DB
testsPath = "./tests/generic"

testFiles = [ f for f in listdir(testsPath) if isfile(join(testsPath,f)) ]
for testFileName in testFiles:
    with open(join(testsPath,testFileName), "r") as testFile:
        content = testFile.read()
        test = TestDAO(name=testFileName, content=content)
        if not controller.db.existsTest(test):
            controller.db.add(test)
        else:
            existingTest = controller.db.getTest(test)
            existingTest.content=content
            controller.db.update(existingTest)


logging.info("Health management platform started on http://" + centralPublicIP + ":" + str(centralPort))


import api.artifactRepository
import api.systemManagementRestAPI
import api.uiManagement

