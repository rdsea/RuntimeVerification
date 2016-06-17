#!/usr/bin/env python
import datetime
from lib.ModelDAO import TestExecutionDAO, TestResultDAO, TestDAO, SystemDAO, TestSessionDAO, UnitTypeDAO, UnitDAO

__author__ = 'TU Wien'
__copyright__ = "Copyright 2015, TU Wien, Distributed Systems Group"
__license__ = "Apache LICENSE"
__version__ = "2.0"
__maintainer__ = "Daniel Moldovan"
__email__ = "d.moldovan@dsg.tuwien.ac.at"
__status__ = "Prototype"

import ConfigParser, logging, yaml, pickle
from Utils import QueueUtil, MailUtil
from Model import UnitType, Unit, TestDescription, EventEncounter, EventType
from Common import ExecutableTest, MessageType, Message, TestResult
from threading import Timer
import threading, random


#contains two classes, TestsManagementEngine and SystemStructureManagementEngine
#responsible with functionality for executing tests, and updating system structure

class TestsManagementEngine(object):

    def __init__(self, databaseManagement, systemStructureManagementEngine, queueCredentials, queueIP='localhost'):
        self.queueIP = queueIP
        self.db = databaseManagement
        self.systemStructureManagementEngine = systemStructureManagementEngine
        self.queueCredentials = queueCredentials
        self.systemStructureManagementEngine = SystemStructureManagementEngine()
        self.currentExecutionIndex = self.db.getMaxTestExecutionID() + 1

    #this must find all units targeted by an identifier
    #identifiers are expressed according to follwing grammar  'Type.'  | 'UnitID.' | 'UnitUUID.' followed by string
    def __getUnitsByIdentifier(self, system, identifier):
        if 'Type.' in identifier:
            typeSpec = identifier.split(".")[1]
            if UnitType.isValid(typeSpec):
               return self.db.getUnitByType(UnitType.toType(typeSpec), system)
            else:
               raise Exception('UnitType ' + typeSpec + " in " + identifier + " is not valid")
        elif 'UnitID.' in identifier:
            unitIDs = identifier.split(".")
            #remove first .
            unitIDs.pop(0)
            #fix issue if . is encountered later in the name
            unitID = unitIDs.pop(0)
            for id in unitIDs:
                unitID = unitID + "." + id
            return self.db.getUnitByName(Unit(name=unitID), system)
        elif 'UnitUUID.' in identifier:
            unitUUIDs = identifier.split(".")
            #remove first .
            unitUUIDs.pop(0)
            #fix issue if . is encountered later in the name
            unitUUID = unitUUIDs.pop(0)
            for id in unitUUIDs:
                unitUUID = unitUUID + "." + id
            #force return list
            return [self.db.getUnitByUUID(uuid=unitUUID, system=system)]


    def scheduleTestForPeriodicExecution(self, user, system, testID, testDescription):
        #check if the description was not deleted
        testDescriptionDAO = self.db.getTestDescription(system,TestDAO(id=testID) )
        if testDescriptionDAO is None:
            return
        self.dispatchTest(user, system, testDescriptionDAO, testDescription, 'Periodic execution')
        for periodicTrigger in testDescription.periodTriggers:
            t = Timer(periodicTrigger.getSeconds(), self.scheduleTestForPeriodicExecution, args=[user, system,testDescriptionDAO.test_id, testDescription])
            t.start()


    def __unitMatchesIdentifier(self, identifier, unit):
        if 'Type.' in identifier:
            typeSpec = identifier.split(".")[1]
            if UnitType.isValid(typeSpec):
               return unit.type == typeSpec
            else:
               raise Exception('UnitType ' + typeSpec + " in " + identifier + " is not valid")
        elif 'UnitID.' in identifier:
            unitID = identifier.split(".")[1]
            return unit.id == unitID
        elif 'UnitUUID.' in identifier:
            unitUUID = identifier.split(".")[1]
            return unit.uuid == unitUUID


    def executeTestForEvent(self, user, system, eventEncounter):
       #todo: decide if feature or bug that when one veent is enecountered, we search for more targets
       #so for example, if test mentiones when Event X, Execute on VM types, here we execute on all VMs, not only on event source
       #this is good when we want to test multiple components when changing smt. For example test all VMs from a database cluster after removing/adding one VM from/to cluster
       for testDescriptionDAO in self.db.getTestDescriptions(system):
              testDescription = testDescriptionDAO.toTestDescription()
              for eventTrigger in testDescription.eventTriggers:
                  #check if trigger matches event
                  for event in eventTrigger.events:
                    event_id = event.id
                    if event_id == eventEncounter.type:
                        event_sources = event.on #this is a list [] of event:  "E1" , "E2" on Type.VirtualMachine, UnitUUID., UnitID.
                        for source in event_sources:
                            #removed check to execute only on event source, as this does not work for "Dead" messages
                            #we should be able to say ok, execute on Unit B if Unit A dies, so curently we execute on all units matching execution info
                            #so if I have executor: Type.VirtualMachine for Type.VirtualMachine, Type.VirtualContainer, Type.Process
                            #then I execute on all untis of VM, Container, Process
                            # if self.__unitMatchesIdentifier(source,eventEncounter.sourceUnit):
                            # t = Timer(self.dispatchTestForUnit, args=[user, system,testDescriptionDAO, testDescription, eventEncounter.sourceUnit, 'Event ' + eventEncounter.event_id ])
                            # t.start()
                            self.dispatchTest(user, system,testDescriptionDAO, testDescription, 'Event ' + eventEncounter.type)


    # currently removed it from execution and replaced with test execution: in case for one event you want multiple tests for multiple units
    # def dispatchTestForUnit(self, user, system, testDescriptionDAO, testDescription, targetUnit, reason):
    #
    #     system = self.db.getSystem(system)
    #
    #     system = self.db.getSystem(system)
    #     staticSystemDescription = pickle.loads(system.description)
    #     completeStructure = Unit(name=system.name, type=UnitType.Composite)
    #     systemUnits = self.db.getSystemUnits(system)
    #     for unit in systemUnits:
    #         self.systemStructureManagementEngine.addUnitInstance(staticSystemDescription, completeStructure, unit.toUnit())
    #
    #     testDescriptionDAO = self.db.getTestDescription(system,TestDAO(id=testDescriptionDAO.test_id))
    #     test = self.db.getTestForTestDescription(testDescriptionDAO)
    #
    #     currentExecutionIndex = self.db.getMaxTestExecutionID() #problem if long running it reaches MAX INT
    #
    #     timestamp = datetime.datetime.now()
    #     testSession = TestSessionDAO(timestamp=timestamp, reason = reason, system_id=system.id)
    #
    #     for targetUnitIdentifier in testDescription.executionInfo:
    #         executorUnitIdentifier = testDescription.executionInfo[targetUnitIdentifier]
    #
    #         targetUnits = self.__getUnitsByIdentifier(system,targetUnitIdentifier)
    #         potentialExecutors = self.__getUnitsByIdentifier(system,executorUnitIdentifier)
    #
    #         #I need to find the executor which is connected to the target (maybe, not necesarily)
    #         #so we search:
    #         #            1 if executor si the target
    #         #            2 if executor is something hosted on same parent as the target
    #         #            repeat 1-2 on parent, parent-parent, up to system
    #
    #         # self.containedUnits = [] if containedUnits is None else containedUnits
    #         # self.connectedToLinks = [] if connectedTo is None else connectedTo
    #         # self.hostedOnUnit =  None if hostedOn is None else hostedOn
    #         # self.hostedUnits = []
    #         if targetUnit in targetUnits:
    #             testExecutor = None
    #             currentUnit = targetUnit
    #             #start search
    #             #change search in breadth first search
    #             #we start from System, and take all containedUnits.build the search tree, When find the target.
    #             #we start going back up the tree
    #
    #             runTimePath = self.systemStructureManagementEngine.getPathToUnitByTypeAndUUID(completeStructure, targetUnit,[])
    #             currentUnit = targetUnit
    #             while len(runTimePath) > 1:
    #                 parent = runTimePath.pop()
    #                 if currentUnit in potentialExecutors:
    #                     testExecutor = currentUnit
    #                     break
    #                 else:
    #
    #                     brothers = parent.containedUnits
    #                     for brother in brothers:
    #                         if brother == currentUnit:
    #                             continue
    #                         if brother in potentialExecutors:
    #                            testExecutor = brother
    #                            break
    #                 currentUnit =  parent
    #             if testExecutor is None:
    #                 print("ERROR: test " + test.name + " was not executed for " + targetUnitIdentifier + " as executor " + executorUnitIdentifier + " was not found")
    #             else:
    #                 currentExecutionIndex += 1
    #                 testSession.calledTests.append(self.__sendTestMessage(username=user.username, password=user.password, queueIP = self.queueIP, testDAO = test, targetUnit=targetUnit, executorUnit=testExecutor, system=system,runTimeSystemDescription=completeStructure, executionIndex= (0+currentExecutionIndex)))
    #                 #here I start thread that waits until timeout, and if not finished, marks it in DB as finished with error
    #                 t = Timer(testDescription.timeout, self.markTestAsFailed, args=[(0+currentExecutionIndex),targetUnit])
    #                 t.start()
    #
    #     self.db.add(testSession)

    #used to execute a single test (but multiple instances), from a single test description
    #if test description specifies one test type to be executed on more units, it will execute the test for each specified unit
    # system has the static description, and all the run-time units target this
    def dispatchTest(self, user, system, testDescriptionDAO, testDescription, reason):

        system = self.db.getSystem(system)
        staticSystemDescription = pickle.loads(system.description)
        completeStructure = Unit(name=system.name, type=UnitType.Composite)
        systemUnits = self.db.getSystemUnits(system)
        for unit in systemUnits:
            self.systemStructureManagementEngine.addUnitInstance(staticSystemDescription, completeStructure, unit.toUnit())

        testDescriptionDAO = self.db.getTestDescription(system,TestDAO(id=testDescriptionDAO.test_id))
        test = self.db.getTestForTestDescription(testDescriptionDAO)

        timestamp = datetime.datetime.now()
        testSession = TestSessionDAO(timestamp=timestamp, reason = reason, system_id=system.id)

        for targetUnitIdentifier in testDescription.executionInfo:
            executorUnitIdentifier = testDescription.executionInfo[targetUnitIdentifier]
            #i have appended 'distinct ' in front of executor if it was specified to be distinct from target

            distinct = False
            if executorUnitIdentifier.startswith("distinct"):
                distinct = True
                executorUnitIdentifier = executorUnitIdentifier.replace("distinct ","")

            targetUnits = self.__getUnitsByIdentifier(system,targetUnitIdentifier)
            potentialExecutors = self.__getUnitsByIdentifier(system,executorUnitIdentifier)

            if not targetUnits:
                logging.error("Could not find any target unit  for identifier" + targetUnitIdentifier)
                return
            if not potentialExecutors:
                logging.error("Could not find any potential executor for identifier" + executorUnitIdentifier)
                return


            #I need to find the executor which is connected to the target (maybe, not necesarily)
            #so we search:
            #            1 if executor si the target
            #            2 if executor is something hosted on same parent as the target
            #            repeat 1-2 on parent, parent-parent, up to system


            for targetUnit in targetUnits:
                testExecutor = None

                #start search
                #change search in breadth first search
                #we start from System, and take all containedUnits.build the search tree, When find the target.
                #we start going back up the tree
                if not distinct and targetUnit in potentialExecutors:
                    testExecutor = targetUnit
                else:
                    currentPotentialExecutor = self.systemStructureManagementEngine.getUnitInRunTimeStructure(completeStructure, targetUnit).hostedOnUnit
                    while currentPotentialExecutor:
                        #transforming from UnitDAO to Unit is a mess
                        #current potential extecutors are DAOs while in structure I have units
                        executorDAO  = self.db.getUnitByUUID(currentPotentialExecutor.uuid, system)
                        if executorDAO in potentialExecutors:
                           testExecutor = executorDAO
                           break
                        elif currentPotentialExecutor.hostedUnits:
                            for brother in currentPotentialExecutor.hostedUnits:
                                brotherDAO = self.db.getUnitByUUID(brother.uuid, system)
                                if brotherDAO in potentialExecutors:
                                   testExecutor = brotherDAO
                                   break
                            if not testExecutor:
                                currentPotentialExecutor = currentPotentialExecutor.hostedOnUnit
                            else:
                                break
                        else:
                            currentPotentialExecutor = currentPotentialExecutor.hostedOnUnit
                    #if we found it it must be in potential executors. if not, use random potential executor
                    if not testExecutor:
                        executorIndex = random.randint(0, len(potentialExecutors)-1)
                        #if distinct
                        #get random to avoid loading same unit with test execution
                        #problem is if we have 1 VM and distinct VM requested, we need to avoid execution
                        if distinct and len(potentialExecutors) <= 1 and  potentialExecutors[executorIndex] == targetUnit:
                            return
                        #if we have more than 1 potential executor, then pick a random distinct one.
                        while distinct and potentialExecutors[executorIndex] == targetUnit:
                            executorIndex = random.randint(0, len(potentialExecutors)-1)
                        testExecutor = potentialExecutors[executorIndex]

                # runTimePath = self.systemStructureManagementEngine.getPathToUnitByTypeAndUUID(completeStructure, targetUnit)
                # currentUnit = targetUnit
                # while len(runTimePath) > 1:
                #     parent = runTimePath.pop()
                #     if currentUnit in potentialExecutors:
                #         testExecutor = currentUnit
                #         break
                #     else:
                #
                #         brothers = parent.containedUnits
                #         for brother in brothers:
                #             if brother == currentUnit:
                #                 continue
                #             if brother in potentialExecutors:
                #                testExecutor = brother
                #                break
                #     currentUnit =  parent
                if testExecutor is None:
                    print("ERROR: test " + test.name + " was not executed for " + targetUnit.uuid + " as executor " + executorUnitIdentifier + " was not found")
                else:
                    lock = threading.Lock()
                    lock.acquire(0)
                    self.currentExecutionIndex = self.currentExecutionIndex + 1
                    currentExecutionIndex = self.currentExecutionIndex
                    lock.release()
                    targetUnit = targetUnit.toUnit() #convert from UnitDAO to Unit
                    # testExecutor = testExecutor.toUnit() #TODO: this mess of Unit vs UnitDAO must be fixed
                    testSession.calledTests.append(self.__sendTestMessage(username=user.username, password=user.password,
                                                                          queueIP = self.queueIP, testDAO = test, targetUnit=targetUnit,
                                                                          executorUnit=testExecutor, system=system,runTimeSystemDescription=completeStructure,
                                                                          executionIndex= (0 + currentExecutionIndex)))
                    #here I start thread that waits until timeout, and if not finished, marks it in DB as finished with error
                    t = Timer(testDescription.timeout, self.markTestAsFailed, args=[system, user, (0 + currentExecutionIndex),targetUnit])
                    t.start()

        self.db.add(testSession)

    #if test does not respond in time, mark it as failed until it responds (if at all)
    def markTestAsFailed(self, system, user, executionId, targetUnit):
        executionInfo = self.db.getTestExecutionInfoByID(executionId)
        if not executionInfo.finalized:
            failedResult = TestResult(executionID=executionId,successful = False,targetUnit=targetUnit, testID=executionInfo.test.name,
                                  details="Test did not respond in specified time. Timeout error.", timestamp= datetime.datetime.now(), systemID=system.id)
            #get previous execution state
            test = self.db.getTestByName(executionInfo.test.name)
            prevExecution = self.db.getLastTestExecutionForTest(test_id=test.id, unit_uuid=targetUnit.uuid)
            #record result
            self.db.markTestFinished(failedResult)
            #check if notification required
            mustNotify = False
            if prevExecution:
                prevResult = self.db.getTestResultForExecution(prevExecution.testExecution)
                if prevResult and failedResult.successful != prevResult.successful:
                    mustNotify = True
            else:
                #notify first executions
                mustNotify= True
            if mustNotify:
                self.notifyTestStateChange(failedResult)
                #persist event encounter
                eventEncounter = EventEncounter(type=EventType.TestFailed, timestamp=datetime.datetime.now(),
                                         system = system,
                                         details= str(executionInfo.test.name) +  "," + str(failedResult.targetUnit.uuid) + "," + str(failedResult.details))
                self.db.addEventEncounter(eventEncounter)
                #execute tests for event
                self.executeTestForEvent(user=user, system=system, eventEncounter = eventEncounter)
   #
   # def __init__(self, testID=None, executionID=None, executorUnit=None,targetUnit = None,successful = False, meta = None, details="", timestamp=None):
   #   self.successful = successful
   #   self.meta = {} if meta is None else meta
   #   self.details=details
   #   self.testID = testID
   #   self.executionID = executionID
   #   self.executorUnit = executorUnit
   #   self.targetUnit = executorUnit if targetUnit is None else targetUnit
   #   self.timestamp = datetime.datetime.now() if timestamp is None else timestamp
   #


    #this method was used in past to execute all specified tests at once
    def dispatchTests(self, user, system, reason):
        for testDescriptionDAO in self.db.getTestDescriptions(system):
          testDescription = testDescriptionDAO.toTestDescription()
          for periodicTrigger in testDescription.periodTriggers:
              self.dispatchTest(user, system, testDescriptionDAO, testDescription, reason)
          for eventTrigger in testDescription.eventTriggers:
              print("#TODO: implement event-based trigger mechanisms")

    def __sendTestMessage(self,  username, password, queueIP, testDAO, targetUnit, executorUnit, system, runTimeSystemDescription, executionIndex):
        executableTest = ExecutableTest(name = testDAO.name, executionID = executionIndex, executorUnit = executorUnit.uuid, targetUnit=targetUnit.uuid)
        executableTest.test = testDAO.content


        targetContext = " targetID="
        if "-" in targetUnit.uuid:
            targetContext = targetContext  + "'"+targetUnit.uuid.split("-")[len(targetUnit.uuid.split("-"))-1]+ "'"  #send as target only last ID
        else:
            targetContext = targetContext +  "'" + targetUnit.uuid+ "'"

        executorContext = " executorID="
        if "-" in executorUnit.uuid:
            executorContext = executorContext  +  "'" +executorUnit.uuid.split("-")[len(executorUnit.uuid.split("-"))-1]+ "'"  #send as target only last ID
        else:
            executorContext = executorContext + "'" + executorUnit.uuid+ "'"

        #add in context all parent path IDs
        unitInRTStruct = self.systemStructureManagementEngine.getUnitInRunTimeStructure(runTimeSystemDescription, targetUnit)
        name=" "
        parentContext = ""
        while unitInRTStruct.hostedOnUnit:
             unitInRTStruct = unitInRTStruct.hostedOnUnit
             if unitInRTStruct.uuid:
                name += "host"
                parentContext = parentContext + "\n" + name+"ID="+  "'" + unitInRTStruct.uuid+ "'"

        # add the contextualization variables for the test
        # this enables tests to be written and use the context variables, such as checking if a process is running
        # TODO: still need more contextualization, custom ctx is needed, such as location of log files to inspect, etc, so need a mechanism for custom contextualization
        executableTest.test =  targetContext + "\n" + executorContext + "\n" + parentContext + "\n" + executableTest.test

        #TODO:fix this problem with mixing DAO with Model Units
        unitUnderTest = targetUnit
        executorUnit = executorUnit
        testExecutionDAO = TestExecutionDAO(id=executionIndex, test_id = testDAO.id, target_unit_uuid = unitUnderTest.uuid
                            ,target_unit_type_id = self.db.getUnitType(UnitTypeDAO(type=unitUnderTest.type)).type ,target_unit_name = unitUnderTest.name , #here if I use UnitTypeDAO(type= also for unit under test i get problems. issue comes from finding units to test, but did not pinpoint it
                            executor_unit_uuid =  executorUnit.uuid ,executor_unit_type_id = executorUnit.type.type
                            ,executor_unit_name =  executorUnit.name,
                            finalized= False, system_id=system.id)
        self.db.add(testExecutionDAO)

        message = Message(type=MessageType.Test, content=executableTest)

        QueueUtil.sendMessage(queueIP, system.name, unitUnderTest.name,
                              system.name + "." + executorUnit.uuid + ".tests" , username, password,
                              executorUnit.uuid + "-Tests", pickle.dumps(message))

        return testExecutionDAO


    def handleReceivedTestResults(self, channel, method, properties, body):
        channel.basic_ack(delivery_tag = method.delivery_tag)
        message = pickle.loads(body)

        #process message depending on type
        if message.type == MessageType.TestResult:

            #check if previous result was of diff nature, and inform of change
            testResult = message.content
            #add timestamp
            testResult.timestamp = datetime.datetime.now()
            if testResult:
                #convert from string to Unit
                testResult.targetUnit = Unit(uuid=testResult.targetUnit, name=testResult.targetUnit)
                #get previous state
                test = self.db.getTestByName(testResult.testID)
                prevExecution = self.db.getLastTestExecutionForTest(test_id=test.id, unit_uuid=testResult.targetUnit.uuid)
                #mark test as finished, and record test result
                self.db.markTestFinished(testResult)
                mustNotify = False
                if prevExecution:
                    prevResult = self.db.getTestResultForExecution(prevExecution.testExecution)
                    if prevResult and testResult.successful != prevResult.successful:
                    #check if need to inform that test status has changes
                        mustNotify = True
                else:
                    #notify first executions
                    mustNotify = True
                if mustNotify:
                    self.notifyTestStateChange(testResult)
                    user = self.db.getUserByUsername(testResult.username)
                    system = self.db.getSystemByName(testResult.systemID)

                    #persist event encounter
                    type = EventType.TestFailed
                    if testResult.successful:
                        type = EventType.TestPassed

                    eventEncounter = EventEncounter(type=type, timestamp=datetime.datetime.now(),
                                             system = system,
                                             details= str(testResult.testID) +  "," + str(testResult.targetUnit.uuid) + "," + str(testResult.details))
                    self.db.addEventEncounter(eventEncounter)
                    #execute tests for event
                    self.executeTestForEvent(user=user, system=system, eventEncounter = eventEncounter)

            else:
                logging.warn("No content received for message " + str(message.type ) )
        else:
            logging.warn("Received message type " + str(message.type) + " instead of MessageType.UnitInstanceInformation=" + str(MessageType.UnitInstanceInformation))

    def notifyTestStateChange(self, testResult):
        #for backward compatibility
        if testResult.username:
            user = self.db.getUserByUsername(testResult.username)
            if user is None:
               return
            if testResult.systemID:
                subject = "[Run-Time Verification Platform] [ System: " + testResult.systemID + "] [ Unit " + str(testResult.targetUnit.uuid) + "] Test " + str(testResult.testID) + " changed state to " + str(testResult.successful)
            else: #for backward compatibility as system ID in result was added later
                subject = "[Run-Time Verification Platform] Test " + str(testResult.testID) + " changed state to " + str(testResult.successful)
            content = "Test " + str(testResult.testID)  + " for " + str(testResult.targetUnit) + " executed by " +   str(testResult.executorUnit)
            content = content + "\n State: " + str(testResult.successful)
            content = content + "\n Details: " + str(testResult.details)
            content = content + "\n Meta: " + str(testResult.meta)
            #TODO: solve issue with default tests which have no user, so we do not know who to report to
            MailUtil.sendMail(user.mailAddress, user.mailUsername, user.mailPassword,user.smtpServerName, user.smtpServerPort, subject, content)

class SystemStructureManagementEngine(object):
    # the idea behind this is to take the uuid of the instance, which is asssumed to be under format parent1.parent2.unitInstanceID, and use the "." separated IDs to find
    # where we should add it
    # as this will be added by a queue message, as messages might arive unsorted (e.g., alive process before alive hosting VM), will also create empty slots for the not finded parents

    def removeUnitInstance(self, runTimeSystemStructure, unit):
        runTimePath = self.getPathToUnitByType(runTimeSystemStructure, unit, [])
        if len(runTimePath) == 0:
            logging.warn("Allready removed " + yaml.dump(unit, default_flow_style=False))
        else:
            runTimePath.pop()  # remove element we searched for from the path
            parent = runTimePath.pop()
            parent.removeUnits(unit)
            if unit.hostedOnUnit:
                unit.hostedOnUnit.removeHosted(unit)
        return runTimeSystemStructure

    def addUnitInstance(self, systemDescription, runTimeSystemStructure, unit):
        # Maybe I will also need to add the relationships sometime, but currently adding only for the unit I am adding.
        # So, if I add unit, but 2 parents missing, I add parents, but do not connect them with relationships except as containedUnits

        #so, if I have 3 level VM - Process - Service, then I have VM_UUID-ProcessUUID-ServiceUUID, so actually I need here to take last UUID, and then join rest
        ids = unit.uuid.split("-")
        ids.pop()

        completeIDs = []
        #now , superparent is ID[0], mini-super is ID[0] + - + id[1], miniminisuper is  ID[0] + - + id[1]+ - + id[2] , etc
        for i,id in enumerate(ids):
            completeIDCurrent = ids[0]
            for j in range(1,i+1):
                completeIDCurrent = completeIDCurrent + "-" + ids[j]
            completeIDs.append(completeIDCurrent)
        ids = completeIDs

        pathInStaticDescription = self.getOnlyCompletePathToUnit(systemDescription, unit, [])

        #if not found, do not bother
        if pathInStaticDescription == []:
            return

        #remove itself
        pathInStaticDescription.pop()

        if len(pathInStaticDescription) > 0 :
            parentComplexUnitInStatic = pathInStaticDescription.pop()
        else:
            parentComplexUnitInStatic = systemDescription

        runtimeELParent = runTimeSystemStructure

        #ensure we have the static path represented in the run-time once
        #both paths have at least the system in them, so start from next and see
        for i in range(1,len(pathInStaticDescription)-1):
            staticElement = pathInStaticDescription[i]
            if not staticElement in runtimeELParent.containedUnits:
                similarElements = filter(lambda instance: instance.name == staticElement.name and instance.type == staticElement.type, runtimeELParent.containedUnits)
                runtimeElement = Unit(name=staticElement.name, type=staticElement.type,   id=staticElement.name+"_" + str(len(similarElements)))
                runtimeELParent.consistsOf(runtimeElement)
                runtimeELParent = runtimeElement

        #now in the run-time structure I have all up to and including the parent to my parent (popped static twice)
        #so now I take all the instances of the parrent type and name, and see if any matches what I want, and is not allready used by some other instance

        parentParent = runtimeELParent

        if parentParent.containedUnits:
            potentialParents = filter(lambda instance: instance.name == parentComplexUnitInStatic.name and instance.type == parentComplexUnitInStatic.type, parentParent.containedUnits)
            added  = False
            for parent in potentialParents:
                if self.checkIfComplexUnitInstanceMatchesDesired(parent, ids, unit):
                   template = self.getUnitTemplate(systemDescription, unit)
                   self.fillInstance(parent, ids, unit, template)
                   added = True
                   break
            #if no child of parent matches what I want, create another one and add it
            if not added:
                newParentInstance = Unit(name=parentComplexUnitInStatic.name, type=parentComplexUnitInStatic.type, id=parentComplexUnitInStatic.name+"_" + str(len(potentialParents)))
                template = self.getUnitTemplate(systemDescription, unit)
                self.fillInstance(newParentInstance, ids, unit, template)
                parentParent.consistsOf(newParentInstance)
        else:
            #else I need to create my parent, and addmyself to it
            newParentInstance = Unit(name=parentComplexUnitInStatic.name, type=parentComplexUnitInStatic.type, id=parentComplexUnitInStatic.name+"_" + str(0))
            template = self.getUnitTemplate(systemDescription, unit)
            self.fillInstance(newParentInstance, ids, unit, template)
            parentParent.consistsOf(newParentInstance)

        return  runTimeSystemStructure

    def __back__addUnitInstance(self, systemDescription, runTimeSystemStructure, unit):
        # Maybe I will also need to add the relationships sometime, but currently adding only for the unit I am adding.
        # So, if I add unit, but 2 parents missing, I add parents, but do not connect them with relationships except as containedUnits

        ids = unit.uuid.split("-")
        ids.pop()
        pathInStaticDescription = self.getPathToUnitByType(systemDescription, unit, [])
        #remove itself
        pathInStaticDescription.pop()

        parentComplexUnitInStatic = pathInStaticDescription.pop()
        runTimePath = self.getPathToUnitByType(runTimeSystemStructure, parentComplexUnitInStatic, [])

        added = False

         #if allready here, ignore
        if len(runTimePath) > 0 :
            if runTimePath[len(runTimePath)-1] == unit:
               return runTimeSystemStructure
            else:
                #else check in its children
                lastInPath = runTimePath[len(runTimePath)-1]
                for child in lastInPath.containedUnits:
                    if child == unit:
                        #need to update the fields from unit being added (in case we added an empty one before)
                        child.id = unit.id
                        child.uuid = unit.uuid
                        child.name = unit.name
                        return runTimeSystemStructure

        #if runtime path is empty, means we start from root and add things
        if len(runTimePath) == 0:
            runTimePath.append(runTimeSystemStructure)

            #go through static description and see if we need to add smt to run-time
            for i in range(len(pathInStaticDescription)):
                #if len == i  means current runTimePath is empty, so we add one to the parrent
                if len(runTimePath) == i:
                    parentOfRunTime = runTimePath[i-1]
                    staticUnit = pathInStaticDescription[i]
                    newRunTimeUnit = Unit(name=staticUnit.name, type=staticUnit.type, uuid=staticUnit.id, id=staticUnit.id)
                    parentOfRunTime.consistsOf(newRunTimeUnit)
                    runTimePath.append(newRunTimeUnit)
                    # template = self.getUnitTemplate(systemDescription, unit)
                    # self.fillInstance(complexInstance, ids, unit, template)

            #with the above for we completed the run-time structure with the required path up to the parent of the complex element
            #now need to check if instances of parentComplexUnitInStatic exists, if yes then if we need to add to them the unit
            lastRuntimeElement = runTimePath[len(runTimePath)-1]
            # currentComplexInstanceIndex = 0;
            for complexElement in lastRuntimeElement.containedUnits:
                if complexElement.type == UnitType.Composite:
                    if self.checkIfComplexUnitInstanceMatchesDesired(complexElement, ids, unit):
                        template = self.getUnitTemplate(systemDescription, unit)
                        self.fillInstance(complexElement, ids, unit, template)
                        added = True
                        break

        else:
            lastRunTimePathElement = runTimePath[len(runTimePath)-1]
            if lastRunTimePathElement.type == UnitType.Composite and lastRunTimePathElement.type == parentComplexUnitInStatic.type and  lastRunTimePathElement.name == parentComplexUnitInStatic.name:
                if self.checkIfComplexUnitInstanceMatchesDesired(lastRunTimePathElement, ids, unit):
                    template = self.getUnitTemplate(systemDescription, unit)
                    self.fillInstance(lastRunTimePathElement, ids, unit, template)
                    added = True
        #if we did not find any ok enough complex element to add it to before, create its own instance
        if not added:
            #if not added we should search suitable parent actually: i.e. if more unit instances exist with
            lastRunTimePathElement = runTimePath[len(runTimePath)-1]
            potentialParents = filter(lambda instance: instance.name == parentComplexUnitInStatic.name and instance.type == parentComplexUnitInStatic.type, lastRunTimePathElement.containedUnits)
            for instance in potentialParents:
                if self.checkIfComplexUnitInstanceMatchesDesired(instance, ids, unit):
                    template = self.getUnitTemplate(systemDescription, unit)
                    self.fillInstance(lastRunTimePathElement, ids, unit, template)
                    added = True
            if not added:
              newComplexElementInstance = Unit(name=parentComplexUnitInStatic.name, type=parentComplexUnitInStatic.type, id=parentComplexUnitInStatic.name+"_" + str(len(potentialParents)))
              template = self.getUnitTemplate(systemDescription, unit)
              self.fillInstance(newComplexElementInstance, ids, unit, template)
              lastRunTimePathElement.consistsOf(newComplexElementInstance)
        return  runTimeSystemStructure



        #check what do we need to add in this run-time path to match the static one


    # def addUnitInstance(self, systemDescription, runTimeSystemStructure, unit):
    #     # Maybe I will also need to add the relationships sometime, but currently adding only for the unit I am adding.
    #     # So, if I add unit, but 2 parents missing, I add parents, but do not connect them with relationships except as containedUnits
    #
    #     ids = unit.uuid.split("-")
    #     ids.pop()
    #     # 1. Find Complex unit to which this unit must be added
    #     path = self.getPathToUnitByType(systemDescription, unit, [])
    #     composite = None
    #     for element in reversed(path):
    #         if element.type == UnitType.Composite:
    #             composite = element
    #             break
    #     # only keep path from composite onward
    #     # pathFromComposite = path[path.index(composite)+1:]
    #     runTimePath = self.getPathToUnitByType(runTimeSystemStructure, unit, [])
    #
    #     # if we found at least one instance of the composite at run-time ok, else need to create first composite instance
    #     if len(runTimePath) == 0:
    #         # here maybe we have more composites in one, so we go each composite backwards
    #         # and if not found,create it
    #         addedThingsPath = []
    #         condition = True
    #         currentCompositeIndex = path.index(composite)
    #         while condition:
    #             instanceName = composite.name
    #             compositeUnitInstance = Unit(name=instanceName, type=UnitType.Composite)
    #             addedThingsPath.append(compositeUnitInstance)  # in end we have smalles in front, and largest in end
    #             currentCompositeIndex = currentCompositeIndex - 1
    #             composite = path[currentCompositeIndex]
    #             runTimePath = self.getPathToUnitByType(runTimeSystemStructure, composite, [])
    #             condition = (len(runTimePath) == 0 and currentCompositeIndex >= 0)
    #         # going through the added and adding first in second, then second in third, etc, to create the final composite structure
    #         megaCompositeThing = addedThingsPath[0]
    #         for i in range(1, len(addedThingsPath)):
    #             addedElement = addedThingsPath[i]
    #             # issue if we add a process, the VM does not consists of it, it just hosts it
    #             # however, if we add a VM to a Complex Unit such as EventProcessing, the unit does not host it, consists of it
    #             if (addedElement.type == UnitType.Composite):
    #                 addedElement.consistsOf(megaCompositeThing)
    #             else:
    #                 addedElement.hosts(megaCompositeThing)
    #             megaCompositeThing = addedElement
    #         if runTimePath:
    #             parent = runTimePath[len(runTimePath) - 1]
    #             if (parent.type == UnitType.Composite):
    #                 parent.consistsOf(megaCompositeThing)
    #             else:
    #                 parent.hosts(megaCompositeThing)
    #         else:
    #             runTimePath.append(megaCompositeThing)
    #             runTimeSystemStructure.containedUnits = []
    #             runTimeSystemStructure.consistsOf(megaCompositeThing)
    #
    #     # anyway here we check if existing complex units have the specified path: e;g; if instance 1 of unit has correct VM, for adding current Java process
    #     # if not, we need to create another instance of the complex crap
    #
    #     #remove the element itself
    #     added = False
    #     for complexInstance in runTimePath[len(runTimePath) - 1].containedUnits:
    #         if self.checkIfComplexUnitInstanceMatchesDesired(complexInstance, ids, unit):
    #             template = self.getUnitTemplate(systemDescription, unit)
    #             self.fillInstance(complexInstance, ids, unit, template)
    #             added = True
    #             break;
    #     # if none matched, we need to add it in first
    #     if not added:
    #         # then add it in first complex unit not having such instances
    #         for complexInstance in runTimePath[len(runTimePath) - 1].containedUnits:
    #             template = self.getUnitTemplate(systemDescription, unit)
    #             self.fillInstance(complexInstance, ids, unit, template)
    #             added = True
    #             break;
    #
    #     if not added:
    #         logging.error("Could not add " + yaml.dump(unit, default_flow_style=False))
    #         logging.error("In run-time structure " + yaml.dump(runTimeSystemStructure, default_flow_style=False))
    #         logging.error("W.r.t. static structure " + yaml.dump(systemDescription, default_flow_style=False))
    #
    #     return runTimeSystemStructure

    # the unit to add description contains the relationships such as hosted on, which can be used to determine the type of the
    def checkIfComplexUnitInstanceMatchesDesired(self, instance, desiredPath,
                                                 unitToAdd):  # unitToAdd not used, left to future extention
        # desiredPath is a list
        matchedCount = 0
        for desired in desiredPath:
            for unit in instance.containedUnits:
                if unit.uuid == desired:
                    matchedCount = matchedCount + 1
                    break

        #also check that complex unit instance does not allready house exactly the instance of what I try to add
        # removed to merge composite instances in one
        # #if "-" means instance has parent, so let it stay more on same parent. otherwise, each instance is standalone
        # if unitToAdd.uuid and "-" in unitToAdd.uuid:
        #     countInstances = filter(lambda instance: instance.name == unitToAdd.name and instance.type == unitToAdd.type and instance.uuid == unitToAdd.uuid, instance.containedUnits)
        # else:
        #      #allow lonly one VM per complex unit
        #     countInstances = filter(lambda instance: instance.name == unitToAdd.name and instance.type == unitToAdd.type, instance.containedUnits)


        # return len(countInstances) == 0 and (matchedCount > 0 or len(desiredPath) == 0)
        return (matchedCount > 0 or len(desiredPath) == 0)

        # the unit to add description contains the relationships such as hosted on, which can be used to determine the type of the

    def fillInstance(self, instance, desiredPath, unitToAdd,
                     unitToAddTemplate):  # unitToAdd not used, left to future extention
        # desiredPath is a list
        # we first add the necesary units hosting the one we want to add
        instance.consistsOf(unitToAdd)
        if desiredPath:
            while desiredPath:
                desiredUnitUUID = desiredPath.pop()
                exists = False
                for unit in instance.containedUnits:
                    if unit.uuid == desiredUnitUUID:
                        exists = True
                        unit.hosts(unitToAdd)
                        return
                if not exists:
                    addedEmpty = Unit(name=unitToAddTemplate.hostedOnUnit.name, type=unitToAddTemplate.hostedOnUnit.type,
                                      uuid=desiredUnitUUID)
                    addedEmpty.hosts(unitToAdd)
                    instance.consistsOf(addedEmpty)
                    unitToAdd = addedEmpty
                    unitToAddTemplate = unitToAddTemplate.hostedOnUnit

    #returns just the unit in run-time structure
    #usefull for understanding hosted on and hosts
    def getUnitInRunTimeStructure(self, root, unit):
        path = []
        path.append(root)
        while path:
          currentUnit = path.pop()
          if unit.type == currentUnit.type and unit.name == currentUnit.name and unit.uuid == currentUnit.uuid:
            return currentUnit
          else:
            for child in currentUnit.containedUnits:
                path.append(child)


    #the difference is that here the element MUST be found, otherwise returns empty
    def getOnlyCompletePathToExistingUnit(self, root, unit):
        path = []
        visited = []
        path.append(root)
        while path:
          currentUnit = path.pop()
          path.append(currentUnit)
          visited.append(currentUnit)
          if unit.type == currentUnit.type and unit.name == currentUnit.name:
            return path
          else:
              childPushed = False
              for child in currentUnit.containedUnits:
                  if not child in visited:
                      path.append(child)
                      childPushed = True
                      break

              #if we reach here no unvisited child so must go back 1 leve
              if not childPushed:
                  path.pop()

    #used when updating structure, so a bit weird    def getOnlyCompletePathToUnit(self, currentUnit, unit, path):
    def getOnlyCompletePathToUnit(self, currentUnit, unit, path):
        if unit.type == currentUnit.type and unit.name == currentUnit.name:
            path.append(currentUnit)
            return path
        elif currentUnit.containedUnits:
            for child in currentUnit.containedUnits:
                childPath = self.getOnlyCompletePathToUnit(child, unit, [currentUnit])
                if len(childPath) > 0:
                    path.extend(childPath)
                    return path
                    # if I reached this, means nothing found, so return path so far
        if len(path) > 0:
            path.pop(len(path)-1)
        return path

    #used when updating structure, so a bit weird    def getOnlyCompletePathToUnit(self, currentUnit, unit, path):
    def getPathToUnitByTypeAndUUID(self, currentUnit, unit, path):

        if unit.type == currentUnit.type and unit.uuid == currentUnit.uuid:
            path.append(currentUnit)
            return path
        elif currentUnit.containedUnits:
            for child in currentUnit.containedUnits:
                childPath = self.getPathToUnitByTypeAndUUID(child, unit, [currentUnit])
                if len(childPath) > 0:
                    path.extend(childPath)
                    return path
                    # if I reached this, means nothing found, so return path so far
        return path

    #here we want to find out what is the structure path to which the child belongs to.
    def getUnitTemplate(self, currentUnit, unit):
        if unit.type == currentUnit.type and unit.name == currentUnit.name:
            return currentUnit
        elif currentUnit.containedUnits:
            for child in currentUnit.containedUnits:
                childPath = self.getUnitTemplate(child, unit)
                if childPath is not None:
                    childPath.hostedOn = currentUnit
                    return childPath
                    # if I reached this, means nothing found, so return path so far
            return None
        else:
            return None


class TestAnalysisEngine(object):
    def __init__(self, databaseManagement):
        self.db = databaseManagement

    def getSuccessRateForSystem(self, static_system_description, system__run_time_structure):
        system = self.db.getSystem(SystemDAO(name=static_system_description.name))


        static_system_units = static_system_description.toList()
        system__run_time_units = system__run_time_structure.toList()

        #remove head unit representing system
        static_system_units.pop(0)
        system__run_time_units.pop(0)

        rateByType = {}
        rateByName = {}
        rateByUUID = {}

        for unit in static_system_units:
            rateByTypeForUnit  = self.getSuccessRateForUnitByType(system,unit.clone())
            rateByNameForUnit  = self.getSuccessRateForUnitByName(system,unit.clone())
            if rateByTypeForUnit:
                #here we can have multiple instances for same type, so if we allready computed, ignore rest
                if not unit.type in rateByType:
                   rateByType[unit.type] = rateByTypeForUnit

            if rateByNameForUnit:
                if not unit.name in rateByName:
                    rateByName[unit.name] = rateByNameForUnit

        for unit in system__run_time_units:
            if unit.uuid:
               rateByUUIDForUnit = self.getSuccessRateForUnitByUUID(system,unit)
               rateByUUID[unit.uuid] = rateByUUIDForUnit

        system__run_time_structure.testResultsAnalysis = {}

        system__run_time_structure.testResultsAnalysis['byType'] = rateByType
        system__run_time_structure.testResultsAnalysis['byName'] = rateByName
        system__run_time_structure.testResultsAnalysis['byUUID'] = rateByUUID

        return system__run_time_structure

    def getSuccessRateForSystemByUUID(self, static_system_description, system__run_time_structure):
        system = self.db.getSystem(SystemDAO(name=static_system_description.name))


        static_system_units = static_system_description.toList()
        system__run_time_units = system__run_time_structure.toList()

        #remove head unit representing system
        static_system_units.pop(0)
        system__run_time_units.pop(0)

        rateByUUID = {}

        for unit in system__run_time_units:
            if unit.uuid:
               rateByUUIDForUnit = self.getSuccessRateForUnitByUUID(system,unit)
               rateByUUID[unit.uuid] = rateByUUIDForUnit

        system__run_time_structure.testResultsAnalysis = {}

        system__run_time_structure.testResultsAnalysis['byUUID'] = rateByUUID

        return system__run_time_structure


    def getSuccessRateForSystemByName(self, static_system_description, system__run_time_structure):
        system = self.db.getSystem(SystemDAO(name=static_system_description.name))


        static_system_units = static_system_description.toList()
        system__run_time_units = system__run_time_structure.toList()

        #remove head unit representing system
        static_system_units.pop(0)
        system__run_time_units.pop(0)

        rateByName = {}

        for unit in static_system_units:
            rateByNameForUnit  = self.getSuccessRateForUnitByName(system,unit)

            if rateByNameForUnit:
                if not unit.name in rateByName:
                    rateByName[unit.name] = rateByNameForUnit
        system__run_time_structure.testResultsAnalysis = {}
        system__run_time_structure.testResultsAnalysis['byName'] = rateByName

        return system__run_time_structure

    def getSuccessRateForSystemByType(self, static_system_description, system__run_time_structure):
        system = self.db.getSystem(SystemDAO(name=static_system_description.name))


        static_system_units = static_system_description.toList()
        system__run_time_units = system__run_time_structure.toList()

        #remove head unit representing system
        static_system_units.pop(0)
        system__run_time_units.pop(0)

        rateByType = {}

        for unit in static_system_units:
            rateByTypeForUnit  = self.getSuccessRateForUnitByType(system,unit)
            if rateByTypeForUnit:
                #here we can have multiple instances for same type, so if we allready computed, ignore rest
                if not unit.type in rateByType:
                   rateByType[unit.type] = rateByTypeForUnit
        system__run_time_structure.testResultsAnalysis = {}
        system__run_time_structure.testResultsAnalysis['byType'] = rateByType

        return system__run_time_structure

    def getSuccessRateForUnitByType(self, system, unit, testReason = None):
        results = self.db.getAllTestResultsForUnitByType(system, unit, testReason)
        executions = self.db.getAllTestExecutionsForUnitByType(system, unit)
        return self.__analyzeSuccessRate(unit, results, executions)

    def getSuccessRateForUnitByName(self,system, unit, testReason = None):
        results = self.db.getAllTestResultsForUnitByName(system, unit, testReason)
        executions = self.db.getAllTestExecutionsForUnitByName(system, unit)
        return self.__analyzeSuccessRate(unit, results, executions)

    def getSuccessRateForUnitByUUID(self,system, unit, testReason = None):
        results = self.db.getAllTestResultsForUnitByUUID(system, unit, testReason)
        executions = self.db.getAllTestExecutionsForUnitByUUID(system, unit)
        return self.__analyzeSuccessRate(unit, results, executions)

    def __analyzeSuccessRate(self, unit, results, executions):

        #unit get all test executions

        unit.testResultsAnalysis = {}
        resultsDict = {}
        executionsDict = {}

        for result in results:
            #if test was deleted in the meantime, the result is still there, but the test is not
            if not result.test:
                continue
            else:
                if not result.test.name in resultsDict:
                    resultsDict[result.test.name] = []
                resultsDict[result.test.name].append(result)



        for execution in executions:
            #if test was deleted in the meantime, the result is still there, but the test is not
            if not execution.test:
                continue
            else:
                if not execution.test.name in executionsDict:
                    executionsDict[execution.test.name] = []
                executionsDict[execution.test.name].append(execution)

        results = resultsDict
        for test_name, resultsForID in results.iteritems():
            successful = filter(lambda execution: execution.successful,resultsForID)
            finished = filter(lambda result: result.finalized, executionsDict[test_name] )
            unit.testResultsAnalysis[test_name] = {'successful':len(successful), 'total':len(executionsDict[test_name]), 'finished':len(finished)}
        return unit


        # resultsForTestType = {result.test_id: result for result in results}.values()

    # def getSuccessRateforUnitByUUID(self, runTimeSystemStructure, unit):
    #
    # def getSuccessRateforUnitByName(self, runTimeSystemStructure, unit):
