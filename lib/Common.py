#!/usr/bin/env python
import datetime
import os, psutil
from threading import Timer

__author__ = 'TU Wien'
__copyright__ = "Copyright 2015, TU Wien, Distributed Systems Group"
__license__ = "Apache LICENSE"
__version__ = "2.0"
__maintainer__ = "Daniel Moldovan"
__email__ = "d.moldovan@dsg.tuwien.ac.at"
__status__ = "Prototype"

#contains classes representing the model for sending tests to be executed to the
#remote executor as messages

class TestResult(object):

   def __init__(self, systemID = None, username= None, testID=None, executionID=None, executorUnit=None,targetUnit = None,successful = False, meta = None, details="", timestamp=None):
     self.successful = successful
     self.meta = {} if meta is None else meta
     self.details=details
     self.testID = testID
     self.executionID = executionID
     self.systemID = systemID
     self.username = username
     self.executorUnit = executorUnit
     self.targetUnit = executorUnit if targetUnit is None else targetUnit
     self.timestamp = datetime.datetime.now() if timestamp is None else timestamp

class ExecutableTest(object):

   # name = test name
   # executionID = each test execution should have a unique ID to be able to reference the test result
   # executorUnit = unit executing the test
   # targetUnit = unit targeted by the test (can be same or different to executorUnit). For example
   # one can run on one VM a test for health of Process/Docker
   def __init__(self, name, executionID, executorUnit, targetUnit= None, test="", meta=None):
     self.meta = {} if meta is None else meta
     self.name = name
     self.test = None if test is None else test
     self.executionID = executionID
     self.executorUnit = executorUnit
     self.targetUnit = executorUnit if targetUnit is None else targetUnit

class UnitInstanceInfo(object):

   def __init__(self, id, uuid, system, type, meta=None, username="guest", password="guest"):
     self.meta = {} if meta is None else meta
     self.id = id
     self.uuid = uuid
     self.type = type
     self.system = system
     self.username = username
     self.password = password

class EventEncounterInfo(object):
    def __init__(self, event_id, timestamp, sourceUnit):
        self.event_id = event_id
        self.timestamp = timestamp
        self.sourceUnit = sourceUnit

class MessageType(object):
        Configuration  = 0
        Test  = 1
        TestResult = 2
        UnitInstanceInformation = 3
        Event = 4


class Message(object):

    def __init__(self, type=MessageType.Test, content= None, meta=None):
     self.meta = {} if meta is None else meta
     self.type = type
     self.content = content


class SimplePerformanceLogger(object):

 def __init__(self,logPath, openMode='w'):
   self.pid = os.getpid()
   self.logPath = logPath
   #ensure we start with fresh file
   file = open(logPath, openMode)
   file.write("RAM!CPU"'\n')
   file.close()

 def logPerformance(self, loggingInterval):
   file = open(self.logPath, 'a')
   process = psutil.Process(self.pid)
   mem = process.memory_info().rss
   cpu = process.cpu_percent(interval=1)
   file.write(str(mem) + "!" + str(cpu) + '\n')
   file.close()
   t = Timer(loggingInterval, self.logPerformance, args=[loggingInterval])
   t.start()