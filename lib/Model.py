#!/usr/bin/env python
__author__ = 'TU Wien'
__copyright__ = "Copyright 2015, TU Wien, Distributed Systems Group"
__license__ = "Apache LICENSE"
__version__ = "2.0"
__maintainer__ = "Daniel Moldovan"
__email__ = "d.moldovan@dsg.tuwien.ac.at"
__status__ = "Prototype"

#file containing the main model classes

import json, uuid, base64


class User(object):
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.notificationMailInfo = None

class NotificationMailInfo(object):
    def __init__(self, mailAdress, username, password,smtpServerName, smtpServerPort ):
        self.username = username
        self.password = password
        self.mailAdress = mailAdress
        self.smtpServerName = smtpServerName
        self.smtpServerPort = smtpServerPort

class Link(object):
    def __init__(self, end_1, end2):
        self.end_1 = end_1
        self.end_2 = end2


class CommunicationLink(Link):
    direct = 1
    reverse = 2
    bidirectional = 3

    def __init__(self, end_1, end2, type=direct):
        super(CommunicationLink, self).__init__(end_1, end2)
        self.type = type


# class DeploymentStackLink(Link):
#     hosted_on = 1
#
#     def __init__(self, end_1, end2, type=hosted_on):
#         super(DeploymentStackLink, self).__init__(end_1, end2)
#         self.type = type


class UnitType(object):
    PhysicalMachine = "PhysicalMachine"
    VirtualMachine = "VirtualMachine"
    VirtualContainer = "VirtualContainer"
    SoftwareContainer = "SoftwareContainer"
    SoftwarePlatform = "SoftwarePlatform"
    SoftwareArtifact = "SoftwareArtifact"
    Gateway = "Gateway"
    PhysicalDevice = "PhysicalDevice"
    Process = "Process"
    Service = "Service"
    Composite = "Composite"

    @staticmethod
    def isValid(type):
        return type in UnitType.__dict__.keys()

    @staticmethod
    def toType(type):
        if UnitType.isValid(type):
           return UnitType.__dict__[type]
        else:
           return None



class EventType(object):
    Added = "Added"
    Removed = "Removed"
    Timeout = "Timeout"
    TestFailed = "TestFailed"
    TestPassed = "TestPassed"

    @staticmethod
    def isValid(type):
        return type in EventType.__dict__.keys()

    @staticmethod
    def toType(type):
        if EventType.isValid(type):
           return EventType.__dict__[type]
        else:
           return None



#
# class System(object):
#     def __init__(self,name):
#         self.name=name
#         self.units=[]
#
#     def contains(self,unit):
#         self.units.append(unit)
#
#     def removeUnit(self,unit):
#         self.units.remove(unit)
#
#     def containsAll(self,units):
#         self.units.extend(units)



class Unit(object):
    def __init__(self, name, type=UnitType.Composite, uuid=None, connectedTo=None, hostedOn=None, hostedUnits=None, containedUnits=None, id =None):
        self.name = name
        self.type = type
        self.uuid = uuid
        self.containedUnits = [] if containedUnits is None else containedUnits
        self.connectedToLinks = [] if connectedTo is None else connectedTo
        self.hostedOnUnit =  None if hostedOn is None else hostedOn
        self.id =  name if id is None else id
        self.hostedUnits = []


    def __eq__(self, other):
        if type(other) is Unit:
            return self.name == other.name and  self.uuid == other.uuid and self.type == other.type
        else:
            return self.type == other

    def __str__( self):
        return "{' name='" + str(self.name) + ", type=" + str(self.type) + ", uuid=" + str(self.uuid) + "}"
    def __repr__(self):
        return self.__str__()

    def toList(self):
        list = [self]
        toProcess = [self]
        while toProcess:
            currentUnit = toProcess.pop(0)
            for containedUnit in currentUnit.containedUnits:
                toProcess.append(containedUnit)
                list.append(containedUnit)
        return list

    def clone(self):
       return  Unit(name = self.name, type=self.type,
                uuid=self.uuid, connectedTo=self.connectedToLinks,
              hostedOn=self.hostedOnUnit,
              hostedUnits=self.hostedUnits,
              containedUnits=self.containedUnits, id =self.id)

    def connectsToUnits(self, connectionType, *units):
        for unit in units:
            self.connectedToLinks.append(CommunicationLink(self, unit, type=connectionType))

    def connectsTo(self, unit, connectionType=CommunicationLink.direct):
         self.connectedToLinks.append(CommunicationLink(self, unit, type=connectionType))

    def hostedOn(self, unit):
        self.hostedOnUnit = unit

    def removeHosted(self, *units):
        for u in units:
            u.hostedOn(None)
            self.hostedUnits.remove(u)

    def hosts(self, *units):
        for u in units:
            u.hostedOn(self)
            self.hostedUnits.append(u)

    def consistsOf(self, *units):
        for unit in units:
            self.containedUnits.append(unit)

    def removeUnits(self, *units):
        for unit in units:
            self.containedUnits.remove(unit)

    def toList(self):
        result = []
        result.append(self)
        for child in self.containedUnits:
            result.extend(child.toList())
        return result

    def toJSON(self):
        jsonString = "{\"id=\":" + self.name + ", \"type\":" + self.type + ", \"uuid\":" + self.uuid
        units = ""
        if self.containedUnits:
            units = "\"containedUnits\": ["
            for unit in self.containedUnits:
                units = units + unit.toJSON()
            units=units[:len(units)-1]
            units = units + "]"
            jsonString  = jsonString + units

        if self.hostedUnits:
            units = "\"hostedUnits\": ["
            for unit in self.hostedUnits:
                units = units + unit.toJSON()
            units=units[:len(units)-1]
            units = units + "]"

        jsonString  = jsonString + units
        jsonString  = jsonString +   "}"

        return jsonString


class EventEncounter(object):
    def __init__(self, system, type, timestamp, details):
        self.type = type
        self.details = details
        self.timestamp = timestamp
        self.system = system

# used to mark events which are detected on different things



class Event(object):
    def __init__(self, id):
        self.id = id
        self.on = []

# for now, the parameter is a unit identifier, not the full unit description
    def addTarget(self, *units):
      for u in units:
        self.on.append(u)

    def removeTarget(self,  *units):
      for u in units:
        self.on.remove(u)

    def __str__( self):
        return "{'id='" + str(self.id) + ", on='" + str(self.on) + "}"
    def __repr__(self):
        return self.__str__()

# we get from each test description its triggers
# and for each trigger we create this object to use it in asynhcronous monitoring of
# and detecting of triggers, and executing the correct tests
class Trigger(object):
    def __init__(self, uuid=uuid.uuid4().int, tests = None):
        self.uuid = uuid
        self.tests = [] if tests is None else tests

    def addTests(self, *tests):
      for t in tests:
        self.tests.append(t)

    def removeTests(self, *tests):
      for t in tests:
        self.tests.remove(t)

# event:  "E1" , "E2" on Level.VirtualMachine
class EventTrigger(Trigger):
    def __init__(self, events=None):
        super(EventTrigger, self).__init__()
        self.events = [] if events is None else events

    def addEvents(self, *events):
      for e in events:
        self.events.append(e)

    def removeEvents(self,  *events):
      for e in events:
        self.events.remove(e)

    def __str__( self):
        description = ""
        for event in self.events:
            description = description + "\n event: " + event.id + " on " + str(event.on)
        return description

    def __repr__(self):
        return self.__str__()
# every:  1s
class PeriodicTrigger(Trigger):
    def __init__(self, period=1, timeUnit='s'):
        super(PeriodicTrigger, self).__init__()
        self.period=int(period)
        self.timeUnit=timeUnit

    def __str__( self):
        description = "period: " + str(self.period) + " " +  str(self.timeUnit)
        return description

    def getSeconds(self):
        # 's' | 'm' | 'h' | 'd'
        seconds = 0
        if self.timeUnit == 's':
            seconds= self.period
        elif self.timeUnit == 'm':
            seconds= self.period * 60
        elif self.timeUnit == 'h':
            seconds= self.period * 3600
        elif self.timeUnit == 'm':
            seconds= self.period * 3600*24
        return int(seconds)

    def __repr__(self):
        return self.__str__()

class TestDescription(object):
    def __init__(self, name=None, timeout = 60,  eventTriggers=None, periodTriggers=None):
        self.name = name
        self.eventTriggers = [] if eventTriggers is None else eventTriggers
        self.periodTriggers = [] if periodTriggers is None else periodTriggers
        self.executionInfo = dict() # key: targetIdentifier, value: list<Executors>
        self.timeout = timeout #timeout in seconds in which test must respond, and if it does not, it is considered to fail

    def addPeriodTrigger(self, *triggers):
      for t in triggers:
        self.periodTriggers.append(t)

    def addEventTrigger(self, *triggers):
      for t in triggers:
        self.eventTriggers.append(t)


    def removePeriodTrigger(self, *triggers):
      for t in triggers:
        self.periodTriggers.remove(t)


    def removeEventTrigger(self, *triggers):
      for t in triggers:
        self.eventTriggers.remove(t)

    def addExecutor(self, executorIdentifier, *targetIdentifiers):
      for t in targetIdentifiers:
          self.executionInfo[t] = executorIdentifier


    def removeExecutor(self, *targetIdentifiers):
        for t in targetIdentifiers:
           self.executionInfo.pop(t)

    def __str__( self):
        description = "Description=\n name='" + str(self.name) + "\n description='" + str(self.description)
        description = description + "\n ExecutionInfo=\n'"
        for executor in self.executionInfo:
            description = description+ "\n" + "executor:" + str(executor) + " for "
            for target in self.executionInfo[executor]:
                description = description + str(target) + ","
        description = description + "\n Triggers=\n'"
        for trigger in self.periodTriggers:
                  description =  description + "\n" + str(trigger)
        for trigger in self.periodTriggers:
                  description =  description + "\n" + str(eventTriggers)
        return description

    def __repr__(self):
        return self.__str__()