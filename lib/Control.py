#!/usr/bin/env python
import ConfigParser
import StringIO
from datetime import datetime
import io
import pickle

__author__ = 'TU Wien'
__copyright__ = "Copyright 2015, TU Wien, Distributed Systems Group"
__credits__ = ["Daniel Moldovan"]
__license__ = "Apache LICENSE"
__version__ = "2.0"
__maintainer__ = "Daniel Moldovan"
__email__ = "d.moldovan@dsg.tuwien.ac.at"
__status__ = "Prototype"

#this file contains the main logic implementing the platform's functionality
#a Controller object is instantiated once per platform initialization, and used by all platform classes.

from lib.Engines import SystemStructureManagementEngine, TestsManagementEngine, TestAnalysisEngine
from lib.Common import MessageType, TestResult, EventEncounterInfo
from lib.Utils import QueueUtil, MailUtil, ThreadFunction#, DBUtil
from lib.Model import Unit, UnitType, User, EventEncounter, EventType
from lib.ModelDAO import UnitDAO, UserDAO, DatabaseManagement, SystemDAO, TestResultDAO,  TestDescriptionDAO, \
    UnitTypeDAO
from lib.Parsers import TestDescriptionParser
import threading, pika, logging
import time, datetime
from functools import wraps


class Controller(object):
    def __init__(self, queueCredentials=pika.PlainCredentials("guest", "guest"), queueIP='localhost', dbPath="./test_db.sql", dbBackupInterval = 60):
        # self.queueListeningArgs = {} #dict to dicts of arguments passed to each queue listener. can be used to inform the listening threads to interrupt or anything else
        self.queue = QueueUtil()
        self.systemStructureManagementEngine = SystemStructureManagementEngine()
        self.db = DatabaseManagement(dbPath= dbPath)
        #move in memory
        #start backing up DB
        # DBUtil.copySQLiteDB(dbPath,"file::memory:?cache=shared")
        # DBUtil.scheduleBackup("file::memory:?cache=shared", dbPath, dbBackupInterval)
        self.testManagementEngine = TestsManagementEngine( self.db, systemStructureManagementEngine=self.systemStructureManagementEngine,
                                                         queueCredentials=queueCredentials, queueIP=queueIP)
        self.testAnalysisEngine = TestAnalysisEngine( self.db)
        self.queueIP = queueIP
        self.queueCredentials = queueCredentials
        # self.__reattachListenerToSystems()
        # self.__registerTestForPeriodicExecution()


    def __registerTestForPeriodicExecution(self):
        for user in self.db.getAllUsers():
          for system in user.managedSystems:
              for testDescriptionDAO in self.db.getTestDescriptions(system):
                  testDescription = testDescriptionDAO.toTestDescription()
                  for periodicTrigger in testDescription.periodTriggers:
                      self.testManagementEngine.scheduleTestForPeriodicExecution(user, system,testDescriptionDAO.test_id,testDescription)


    def __reattachListenerToSystems(self):
        for user in self.db.getAllUsers():
            for system in user.managedSystems:
                QueueUtil.addSystemQueueHost(self.queueIP, self.queueCredentials,system)
                QueueUtil.addUserAccessToSystem(self.queueIP, self.queueCredentials, user, system)

                self.queue.listenToMessages(self.queueIP, system.name, binding_keys=[system.name + ".lifecycle.alive"],
                                           username=user.username,password=user.password, exchange=system.name, queueName="alive",
                                           callback=self.handleReceivedAliveMessage)
                self.queue.listenToMessages(self.queueIP, system.name, binding_keys=[system.name + ".lifecycle.dead"],
                                    username=user.username,password=user.password, exchange=system.name, queueName="dead",
                                    callback=self.handleReceivedDeadMessage)

                self.queue.listenToMessages(self.queueIP, system.name, binding_keys=[system.name + ".events"],
                                             username=user.username,password=user.password, exchange=system.name, queueName="events",
                                            callback=self.handleReceivedEventMessage)

                #ensure we start with fresh Result queues, so delete all previous result queues
                for unit in self.db.getSystemUnits(system):
                   self.queue.removeQueue(self.queueIP, system.name,  queueName=unit.uuid+"-Results", username=user.username,password=user.password)

                for unit in self.db.getSystemUnits(system):
                   self.queue.listenToMessages(self.queueIP, system.name, binding_keys=[system.name + "." + unit.uuid + ".results"],
                                    username=user.username,password=user.password,exchange=unit.name, queueName=unit.uuid+"-Results", callback=self.testManagementEngine.handleReceivedTestResults, )




    # method used to check if any method annotated with this authenticate_user is called by a user
    # having the right to call it
    def authenticate_user(function):
        @wraps(function)
        def decorated(self,user, *args, **kwargs):
            if not self.db.existsUser(user):
                raise ValueError("Credentials for " + user.username + " not correct, or user does not exist")
            return function(self, user, *args, **kwargs)
        return decorated

    def authenticate_user_access(function):
        @wraps(function)
        def decorated(self,user, system, *args, **kwargs):
            #reduced first check to reduce performance load
            # if not self.db.existsUser(user) or not self.db.hasAccess(user,system):
            if not self.db.hasAccess(user,system):
                raise ValueError("Credentials for " + user.username + " not correct, or user does not exist, or does not have access to the system")
            return function(self, user, system, *args, **kwargs)
        return decorated

    def addUser(self, user):
        if self.db.existsUser(user):
                raise ValueError("User " + user.username + " allready exists")
        else:
            user_dao = UserDAO.toDAO(user)
            self.db.add(user_dao)
            QueueUtil.addUser(self.queueIP, self.queueCredentials, user)

    def emailPassword(self, username):
        user = self.db.getUserByUsername(username)
        if user:
           MailUtil.sendMail(user.mailAddress, user.mailUsername, user.mailPassword,user.smtpServerName, user.smtpServerPort, "[Run-Time Verification Platform] Password", user.password)

    @authenticate_user_access
    def dispatchTests(self, user, system, reason):
         self.testManagementEngine.dispatchTests(user, system, reason)

    @authenticate_user
    def removeUser(self, user):
        if not self.db.existsUser(user):
                raise ValueError("User " + user.username + " does not exists")
        else:
            user_dao = self.db.getUser(UserDAO.toDAO(user))
            systems = user_dao.managedSystems
            for system in systems:
                self.removeSystem(user, system)
            self.db.remove(user_dao)
            #TODO: remove all user systems
            QueueUtil.removeUser(self.queueIP, self.queueCredentials, user)

    @authenticate_user
    def addSystem(self, user, system):

        user_dao = UserDAO.toDAO(user)
        system_dao = SystemDAO(name=system.name, description = pickle.dumps(system))
        if not self.db.existsUser(user):
            return "Credentials for " + user.username + " not correct, or user does not exist"
        self.db.add(system_dao)

        user_dao = self.db.getUser(user_dao) #retrieve the suer form the database to add to it the new managed service

        # managedSystemRelationship = UserSystemsDAO(user_id=user_dao.id,system_id=system_dao.id)
        # self.db.add(managedSystemRelationship)

        user_dao.managedSystems.append(system_dao)
        self.db.update(user_dao)

        QueueUtil.addSystemQueueHost(self.queueIP, self.queueCredentials,system)
        QueueUtil.addUserAccessToSystem(self.queueIP, self.queueCredentials, user, system)

        self.queue.listenToMessages(self.queueIP, system.name, binding_keys=[system.name + ".lifecycle.alive"],
                                    username=user.username,password=user.password, exchange=system.name, queueName="alive",
                                   callback=self.handleReceivedAliveMessage)
        self.queue.listenToMessages(self.queueIP, system.name, binding_keys=[system.name + ".lifecycle.dead"],
                                    username=user.username,password=user.password, exchange=system.name, queueName="dead",
                                   callback=self.handleReceivedDeadMessage)
        self.queue.listenToMessages(self.queueIP, system.name, binding_keys=[system.name + ".events"],
                                     username=user.username,password=user.password, exchange=system.name, queueName="events",
                                    callback=self.handleReceivedEventMessage)


        return system_dao

    @authenticate_user_access
    def removeSystem(self, user, system):

        static_system_dao = SystemDAO(name= system.name) #static description has no UUID

        system_units = self.db.getSystemUnits(static_system_dao)
        events = self.db.deleteAllEventsForSystem(system)
        events = self.db.deleteAllTestSessionsForSystem(system)
        result = self.db.deleteAllTestExecutionsForSystem(system)
        result = self.db.deleteAllTestResultsForSystem(system)

        for unit in system_units:
            self.removeSystemUnit(user, unit)
        self.db.removeSystem(static_system_dao)

        self.queue.removeQueue(self.queueIP, system.name,  username=user.username,password=user.password, queueName="alive")
        self.queue.removeQueue(self.queueIP, system.name,  username=user.username,password=user.password, queueName="dead")
        self.queue.removeQueue(self.queueIP, system.name,  username=user.username,password=user.password, queueName="events")

        QueueUtil.removeUserAccessToSystem(self.queueIP, self.queueCredentials, user, system)
        QueueUtil.removeSystemQueueHost(self.queueIP, self.queueCredentials,system)


    @authenticate_user
    def getGenericTests(self, user):
        return self.db.getGenericTests()

    @authenticate_user
    def getUserTests(self, user):
        user = self.db.getUser(UserDAO.toDAO(user))
        return user.managedTests

    @authenticate_user_access
    def getRunTimeSystem(self, user, system):
        return self.db.getUnit(system)

    #the purpose of this method is to handle i am alive messages send by system units when they register in the
    ##time structure
    @authenticate_user_access
    def addSystemUnit(self, user, system, unit):
        static_system_unit = SystemDAO(name=system.name)
        #1 update system structure
        if self.db.existsSystem(static_system_unit):
            lock = threading.Lock()
            lock.acquire()
            try:
                # self.db.add(UnitDAO.toDAO(unit))
                # unit = self.db.getUnit(unit)
                static_system = self.db.getSystem(static_system_unit)
                #check if type allready inserted, and if yes, do not add it again
                unitTypeDAO = UnitTypeDAO.toDAO(unit.type)
                if self.db.existsUnitType(unitTypeDAO):
                    unitTypeDAO = self.db.getUnitTypeByID(unitTypeDAO.type)
                unitDAO = UnitDAO.toDAO(unit, static_system.id, unitTypeDAO)
                if not self.db.existsUnit(unitDAO, static_system):
                    self.db.add(unitDAO)
            finally:
                lock.release()
        else:
           logging.warn("System with ID " + str(system.name) + " and UUID " + str(system.uuid) + " does not exist")
        #2. now we need to start listening to the queue of test results for the added unit

        queueResultsListeningArgs =  self.queue.listenToMessages(self.queueIP, system.name, binding_keys=[system.name + "." + unit.uuid + ".results"],
                                    username=user.username,password=user.password, exchange=unit.name, queueName=unit.uuid+"-Results", callback=self.testManagementEngine.handleReceivedTestResults)

    #the purpose of this method is to handle i am deade messages send by system units when they de-register from the
    ##time structure
    @authenticate_user_access
    def removeSystemUnit(self, user, system, unit):
        static_system = SystemDAO(name=system.name)
        #1 update system structure
        if self.db.existsSystem(static_system):
            static_system = self.db.getSystem(static_system)

            unitDAO = UnitDAO.toDAO(unit, static_system.id, UnitTypeDAO.toDAO(unit.type))

            if self.db.existsUnit(unitDAO, static_system):
                lock = threading.Lock()
                lock.acquire()
                try:
                    #removing all execution history when unit dissapears to ensure we get fresh events
                    self.db.deleteAllTestExecutionsForUnit(static_system, unitDAO)
                    self.db.deleteLastTestExecutionsForUnit(static_system,unitDAO)
                    self.db.removeUnit(unitDAO, static_system)
                finally:
                    lock.release()

                self.queue.removeQueue(self.queueIP, system.name,   username=user.username,password=user.password,  queueName=unit.uuid+"-Tests")
                self.queue.removeQueue(self.queueIP, system.name,  username=user.username,password=user.password,  queueName=unit.uuid+"-Results")

            else:
                logging.warn("Unit with ID " + unitDAO.name + " and UUID " + unitDAO.uuid + " does not exist")
        else:
            logging.warn("System with ID " + system.name + " and UUID " + system.uuid + " does not exist")



    @authenticate_user_access
    def getRunTimeSystem(self, user, system):
        return self.db.getSystem(system)

    #this method builds the system tree representing all instances of system units
    @authenticate_user_access
    def getLatestCompleteSystemStructure(self, user, system):
        systemDescription = self.db.getSystem(system)
        staticSystemDescription = pickle.loads(systemDescription.description)
        completeStructure = Unit(name=system.name, type=UnitType.Composite)
        systemUnits = self.db.getSystemUnits(systemDescription)
        for unit in systemUnits:
            self.systemStructureManagementEngine.addUnitInstance(staticSystemDescription, completeStructure, unit.toUnit())
        return completeStructure



    #this method builds the system tree representing all instances of system units
    @authenticate_user_access
    def getStaticSystemStructure(self, user, system):
        systemDescription = self.db.getSystem(system)
        staticSystemDescription = pickle.loads(systemDescription.description)
        return staticSystemDescription

    #this method builds the system tree representing all instances of system units
    @authenticate_user_access
    def getAllEventsForSystem(self, user, system):
        systemDescription = self.db.getSystem(system)
        events = self.db.getAllEventsForSystem(systemDescription)
        return events


    @authenticate_user_access
    def getTestsForSystemAsPickledObject(self, user, system):
        systemDescription = self.db.getSystem(system)
        testDescriptions = self.db.getAllTestDescriptionsForSystem(systemDescription)
        #pickle tests to string
        output = io.BytesIO()
        pickle.dump(testDescriptions, output, pickle.HIGHEST_PROTOCOL)
        contents = output.getvalue()
        output.close()
        return contents


    @authenticate_user_access
    def deleteEventsForSystem(self, user, system):
        systemDescription = self.db.getSystem(system)
        events = self.db.getAllEventsForSystem(systemDescription)
        for event in events:
            self.db.remove(event)
        return events


    @authenticate_user_access
    def getLastTestSessionStatus(self, user, system):
        systemDAO =  self.getLatestCompleteSystemStructure(user, system)
        units = []
        units.append(systemDAO)

        testsSession = self.db.getLastTestSessionForSystem(self.db.getSystem(system))

        if not testsSession: #if no test session for system
            return systemDAO

        testExecutions = testsSession.calledTests


        while len(units) > 0:
            currentUnit = units.pop(0)
            currentUnit.testsStatus = {}
            for child in currentUnit.containedUnits:
                units.append(child)

            for testExecution in testExecutions:
                if currentUnit.id == testExecution.target_unit_id:
                    if not testExecution.finalized:
                        testExecutorInfo = Unit( uuid= testExecution.executor_unit_uuid ,
                                                 id=testExecution.executor_unit_type_id,
                                                name=testExecution.executor_unit_name)
                        testResult = TestResultDAO(test_id=testExecution.test_id, execution_id=testExecution.id, executorUnit =testExecutorInfo
                            ,targetUnit = self.db.getTargetUnitForTestExecution(testExecution),
                            successful = False, details="Executing")
                    else:
                        testResult = self.db.getTestResultForExecution(testExecution)
                    test = testResult.test
                    currentUnit.testsStatus[test.name]= testResult.toTestResult()

        systemDAO.testSession = {}
        systemDAO.testSession['timestamp'] = testsSession.timestamp
        systemDAO.testSession['reason'] = testsSession.reason
        return systemDAO


    @authenticate_user_access
    def getLastTestsStatus(self, user, system):
        systemDAO =  self.getLatestCompleteSystemStructure(user, system)
        toProcess = []
        units = []
        toProcess.append(systemDAO)

        #flatten out structure tree
        while len(toProcess) > 0:
            currentUnit = toProcess.pop(0)
            units.append(currentUnit)
            currentUnit.testsStatus = {}
            for child in currentUnit.containedUnits:
                toProcess.append(child)

        threads = []
        #add results for each test in seperate thread
        for unit in units:
            thread = ThreadFunction(functionToRun=self.__addTestResultForUnit,currentUnit = unit)
            threads.append(thread)
            thread.setDaemon(True)

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        return systemDAO

    def __addTestResultForUnit(self, currentUnit):
      prev = time.time()
      testExecutions = self.db.getLastTestExecutionsForUnit(currentUnit)
      after = time.time()
      for testExecution in testExecutions:
        if not testExecution.finalized:
            testResult = TestResultDAO(test_id=testExecution.test_id, execution_id=testExecution.id,
                successful = False, details="Executing")
        else:
            prev = time.time()
            testResult = self.db.getTestResultForExecution(testExecution)
            after = time.time()

        test = testResult.test
        currentUnit.testsStatus[test.name]= testResult.toTestResult()

    @authenticate_user_access
    def getSuccessRateAnalysis(self, user, system):
        system_run_time_structure =  self.getLatestCompleteSystemStructure(user, system)
        systemDescription = self.db.getSystem(system)
        static_system_description = pickle.loads(systemDescription.description)

        successAnalysis = self.testAnalysisEngine.getSuccessRateForSystem( static_system_description, system_run_time_structure)
        return successAnalysis


    @authenticate_user_access
    def getSuccessRateAnalysisByUUID(self, user, system):
        system_run_time_structure =  self.getLatestCompleteSystemStructure(user, system)
        systemDescription = self.db.getSystem(system)
        static_system_description = pickle.loads(systemDescription.description)

        successAnalysis = self.testAnalysisEngine.getSuccessRateForSystemByUUID( static_system_description, system_run_time_structure)
        return successAnalysis


    @authenticate_user_access
    def getSuccessRateAnalysisByName(self, user, system):
        system_run_time_structure =  self.getLatestCompleteSystemStructure(user, system)
        systemDescription = self.db.getSystem(system)
        static_system_description = pickle.loads(systemDescription.description)

        successAnalysis = self.testAnalysisEngine.getSuccessRateForSystemByName( static_system_description, system_run_time_structure)
        return successAnalysis


    @authenticate_user_access
    def getSuccessRateAnalysisByType(self, user, system):
        system_run_time_structure =  self.getLatestCompleteSystemStructure(user, system)
        systemDescription = self.db.getSystem(system)
        static_system_description = pickle.loads(systemDescription.description)

        successAnalysis = self.testAnalysisEngine.getSuccessRateForSystemByType( static_system_description, system_run_time_structure)
        return successAnalysis

    # @authenticate_user_access
    # def addSimpleTestsConfig(self, user, system, testContent):
    #
    #     cfg = SimpleTestsConfigurationDAO(system_id=system.id,config=pickle.dumps(testContent))
    #     self.db.updateSimpleTestsConfiguration(system, cfg)

    @authenticate_user_access
    def addTestDescription(self, user, system, test, testDescriptionText):
        testDescription = TestDescriptionParser().parseTestDescriptionFromText(testDescriptionText)
        dao = TestDescriptionDAO.toDAO(system, testDescription, testDescriptionText)
        dao.test_id = test.id
        if self.db.existsTestDescription(system=system, test=test):
            self.db.removeDescriptionsForTest(system=system, test=test)
        self.db.add(dao)
        self.testManagementEngine.scheduleTestForPeriodicExecution(user, system, test.id, testDescription)


    @authenticate_user_access
    def getTestDescription(self, user, system, test):
        if self.db.existsTestDescription(system=system, test=test):
             return self.db.getTestDescriptionForTest(system=system, test=test).rawTextDescription
        else:
            with open("./resources/templates/default/testDescription") as file:
                text = file.read()
            return text

    @authenticate_user
    def loadSystemDescriptionTemplate(self, user):
         with open("./resources/templates/default/systemDescription") as file:
            text = file.read()
         return text


    @authenticate_user_access
    def deleteTestDescription(self, user, system, test):
        self.db.removeLastTestExecutionForTest(test.id)
        if self.db.existsTestDescription(system=system, test=test):
             return self.db.removeDescriptionsForTest(system=system, test=test)


    #ALIVE messages are sent after a unit starts/is created
    #used in allocating queues for unit tests and adding unit in the run-time system
    def handleReceivedAliveMessage(self, channel, method, properties, body):
        message = pickle.loads(body)
        channel.basic_ack(delivery_tag = method.delivery_tag)

        #process message depending on type
        if message.type == MessageType.UnitInstanceInformation:
            unitInstanceInfo = message.content
            if unitInstanceInfo:
                 user=User(username=unitInstanceInfo.username,password=unitInstanceInfo.password)
                 system=Unit(name=unitInstanceInfo.system, type=UnitType.Composite)
                 system = self.db.getSystem(system)
                 unit=Unit(name=unitInstanceInfo.id, uuid=unitInstanceInfo.uuid, type=unitInstanceInfo.type)
                 self.addSystemUnit(user=user, system = system, unit=unit)

                 #persist event encounter
                 eventEncounter = EventEncounter(type=EventType.Added, timestamp=datetime.datetime.now(),
                                                 system = system,
                                                 details=str(unitInstanceInfo.uuid))
                 self.db.addEventEncounter(eventEncounter)

                 self.testManagementEngine.executeTestForEvent(user=user, system=system, eventEncounter = eventEncounter)

                 #notify user that something was added
                 subject = "[Run-Time Verification Platform] [ System: " + unitInstanceInfo.system + "] [ Unit " + str(unitInstanceInfo.uuid) + "] ADDED"
                 content = "Added signal received for Unit with"
                 content = content + "\n ID: " + str(unitInstanceInfo.id)
                 content = content + "\n Type: " + str(unitInstanceInfo.type)
                 content = content + "\n UUID: " + str(unitInstanceInfo.uuid)
                 user = self.db.getUser(user)
                 MailUtil.sendMail(user.mailAddress, user.mailUsername, user.mailPassword,user.smtpServerName, user.smtpServerPort, subject, content)
            else:
                 logging.warn("No content received for message " + str(message.type ) )
        else:
            logging.warn("Received message type " + str(message.type) + " instead of MessageType.UnitInstanceInformation=" + str(MessageType.UnitInstanceInformation))

    #DEAD messages are sent before th unit is to be destroyed/stopped
    #used in decoupling any queues allocated and removing the unit from the run-time system
    def handleReceivedDeadMessage(self, channel, method, properties, body):
        message = pickle.loads(body)
        channel.basic_ack(delivery_tag = method.delivery_tag)

        #process message depending on type
        if message.type == MessageType.UnitInstanceInformation:
            unitInstanceInfo = message.content
            if unitInstanceInfo:
                 user=User(username=unitInstanceInfo.username,password=unitInstanceInfo.password)
                 system=Unit(name=unitInstanceInfo.system, type=UnitType.Composite)
                 system = self.db.getSystem(system)
                 unit=Unit(name=unitInstanceInfo.id, uuid=unitInstanceInfo.uuid, type=unitInstanceInfo.type)
                 self.removeSystemUnit(user=user, system = system, unit=unit)
                 #persist event encounter
                 eventEncounter = EventEncounter(type=EventType.Removed, timestamp=datetime.datetime.now(),
                                                 system = system,
                                                 details=str(unitInstanceInfo.uuid))
                 self.db.addEventEncounter(eventEncounter)

                 self.testManagementEngine.executeTestForEvent(user=user, system=system, eventEncounter = eventEncounter)

                 #notify user that something was removed
                 subject = "[Run-Time Verification Platform] [ System: " + unitInstanceInfo.system + "] [Unit " + str(unitInstanceInfo.uuid) + "] REMOVED"
                 content = "Added signal received for Unit with"
                 content = content + "\n ID: " + str(unitInstanceInfo.id)
                 content = content + "\n Type: " + str(unitInstanceInfo.type)
                 content = content + "\n UUID: " + str(unitInstanceInfo.uuid)
                 user = self.db.getUser(user)
                 MailUtil.sendMail(user.mailAddress, user.mailUsername, user.mailPassword,user.smtpServerName, user.smtpServerPort, subject, content)
            else:
                 logging.warn("No content received for message " + str(message.type ) )
        else:
            logging.warn("Received message type " + str(message.type) + " instead of MessageType.UnitInstanceInformation=" + str(MessageType.UnitInstanceInformation))

    #custom events can be sent to signal changes in the system, that might need to trigger test executions
    def handleReceivedEventMessage(self, channel, method, properties, body):
        message = pickle.loads(body)
        channel.basic_ack(delivery_tag = method.delivery_tag)

        #process message depending on type
        if message.type == MessageType.Event:
            eventEncounterInfo = message.content
            if eventEncounterInfo:
               system=Unit(name=eventEncounterInfo.sourceUnit.system, type=UnitType.Composite)
               user=User(username=eventEncounterInfo.sourceUnit.username,password=eventEncounterInfo.sourceUnit.password)
               unit=Unit(name=eventEncounterInfo.sourceUnit.id, uuid=eventEncounterInfo.sourceUnit.uuid, type=eventEncounterInfo.sourceUnit.type)
               eventEncounter = EventEncounter(event_id=eventEncounterInfo.event_id, timestamp=eventEncounterInfo.timestamp, sourceUnit = unit)
               self.testManagementEngine.executeTestForEvent(user=user, system=system, eventEncounter = eventEncounter)
            else:
                 logging.warn("No content received for message " + str(message.type ) )
        else:
            logging.warn("Received message type " + str(message.type) + " instead of MessageType.Event=" + str(MessageType.Event))
