# #!/usr/bin/env python
# import pickle
#
# __author__ = 'TU Wien'
# __copyright__ = "Copyright 2015, TU Wien, Distributed Systems Group"
# __credits__ = ["Daniel Moldovan"]
# __license__ = "Apache LICENSE"
# __version__ = "2.0"
# __maintainer__ = "Daniel Moldovan"
# __email__ = "d.moldovan@dsg.tuwien.ac.at"
# __status__ = "Prototype"
#
# from lib.Engines import SystemStructureManagementEngine, TestsManagementEngine
# from lib.Common import Message, UnitInstanceInfo, MessageType, TestResult
# from lib.Utils import QueueUtil
# from lib.Model import Unit, UnitType, User
# from lib.ModelDAO import UnitDAO, UnitTypeDAO, UserDAO, DatabaseManagement
# import threading, pika, logging
# from functools import wraps
#
# class Controller(object):
#     def __init__(self, queueCredentials=pika.PlainCredentials("guest", "guest"), simpleConfigPath='./config/tests.simple.specification', queueIP='localhost', dbPath="./test_db.sql"):
#         self.systemStructureManagementEngine = SystemStructureManagementEngine()
#         self.db = DatabaseManagement(dbPath= dbPath)
#         self.testManagementEngine = TestsManagementEngine( self.db, simpleConfigPath=simpleConfigPath,queueIP=queueIP)
#         self.queueIP = queueIP
#         self.queueCredentials = queueCredentials
#
#
#     def check_auth(self,username, password):
#         """This function is called to check if a username /
#         password combination is valid.
#         """
#         return username == 'admin' and password == 'secret'
#
#     def authenticate_user(function):
#         @wraps(function)
#         def decorated(self,user, *args, **kwargs):
#             if not self.db.existsUser(user):
#                 raise ValueError("Credentials for " + user.username + " not correct, or user does not exist")
#             return function(self, user, *args, **kwargs)
#         return decorated
#
#     def authenticate_user_access(function):
#         @wraps(function)
#         def decorated(self,user, system, *args, **kwargs):
#             if not self.db.existsUser(user) and not self.db.hasAccess(user,system):
#                 raise ValueError("Credentials for " + user.username + " not correct, or user does not exist, or does not have access to the system")
#             return function(self, user, system, *args, **kwargs)
#         return decorated
#
#
#     def addUser(self, user):
#         if self.db.existsUser(user):
#                 raise ValueError("User " + user.username + " allready exists")
#         else:
#             user_dao = UserDAO.toDAO(user)
#             self.db.add(user_dao)
#             QueueUtil.addUser(self.queueIP, self.queueCredentials, user)
#
#     @authenticate_user_access
#     def dispatchTests(self, user, system):
#          self.testManagementEngine.dispatchTests(system, pika.PlainCredentials(user.username, user.password))
#
#     @authenticate_user
#     def removeUser(self, user):
#         if not self.db.existsUser(user):
#                 raise ValueError("User " + user.username + " does not exists")
#         else:
#             user_dao = UserDAO.toDAO(user)
#             self.db.remove(user_dao)
#             QueueUtil.removeUser(self.queueIP, self.queueCredentials, user)
#
#     @authenticate_user
#     def addSystem(self, user, system):
#         user_dao = UserDAO.toDAO(user)
#         static_system_dao = UnitDAO.toDAO(system)
#         run_time_structure = UnitDAO.toDAO(Unit(name=system.name,uuid=system.name,type=static_system_dao.type))
#         if not self.db.existsUser(user):
#             raise ValueError("Credentials for " + user.username + " not correct, or user does not exist")
#         self.db.add(static_system_dao)
#         self.db.add(run_time_structure)
#         user_dao.managedServices.append(static_system_dao)
#
#         QueueUtil.addSystemQueueHost(self.queueIP, self.queueCredentials,system)
#         QueueUtil.addUserAccessToSystem(self.queueIP, self.queueCredentials, user, system)
#
#         QueueUtil.listenToMessages(self.queueIP, system.name, binding_keys=system.name + ".lifecycle.alive",
#                                    credentials=pika.PlainCredentials(user.username, user.password), exchange=system.name, queueName="alive",
#                                    callback=self.handleReceivedAliveMessage, arguments={})
#         QueueUtil.listenToMessages(self.queueIP, system.name, binding_keys=system.name + ".lifecycle.dead",
#                                    credentials=pika.PlainCredentials(user.username, user.password), exchange=system.name, queueName="dead",
#                                    callback=self.handleReceivedDeadMessage, arguments={})
#         return run_time_structure
#
#     @authenticate_user_access
#     def removeSystem(self, user, system):
#
#         static_system_dao = UnitDAO(id=system.name,uuid='',type=system.type) #static description has no UUID
#         run_time_structure = UnitDAO(id=system.name,uuid=system.name,type=system.type)
#
#         self.db.removeUnitByIDAndUUID(static_system_dao)
#         self.db.removeUnitByIDAndUUID(run_time_structure)
#         QueueUtil.removeQueue(self.queueIP, system.name, credentials=pika.PlainCredentials(user.username, user.password), queueName="alive")
#         QueueUtil.removeQueue(self.queueIP, system.name, credentials=pika.PlainCredentials(user.username, user.password), queueName="dead")
#         QueueUtil.removeUserAccessToSystem(self.queueIP, self.queueCredentials, user, system)
#         QueueUtil.removeSystemQueueHost(self.queueIP, self.queueCredentials,system)
#
#
#
#     @authenticate_user_access
#     def getRunTimeSystem(self, user, system):
#         return self.db.getUnit(system)
#
#
#
#     #the purpose of this method is to handle i am alive messages send by system units when they register in the
#     ##time structure
#     @authenticate_user_access
#     def addSystemUnit(self, user, system, unit):
#         static_system_unit = Unit(name=system.name, uuid='', type=system.type)
#         #1 update system structure
#         if self.db.existsUnit(static_system_unit):
#             lock = threading.Lock()
#             lock.acquire()
#             try:
#                 # self.db.add(UnitDAO.toDAO(unit))
#                 # unit = self.db.getUnit(unit)
#                 static_system = self.db.getUnit(static_system_unit)
#                 #query on ID because run-time has uuid=id, and static has id empty (should change this for the future)
#                 run_time_system = self.db.getUnit(Unit(name=system.name, uuid=system.name, type=system.type))
#                 run_time_system = self.systemStructureManagementEngine.addUnitInstance(static_system.toUnit(), run_time_system.toUnit(), unit)
#                 #refresh DB description
#                 updated_run_time_system = UnitDAO.toDAO(run_time_system)
#                 self.db.update(updated_run_time_system)
#             finally:
#                 lock.release()
#         else:
#             raise ValueError("System with ID " + str(system.name) + " and UUID " + str(system.uuid) + " does not exist")
#         #2. now we need to start listening to the queue of test results for the added unit
#
#         QueueUtil.listenToMessages(self.queueIP, system.name, binding_keys=unit.name + "." + unit.uuid + ".tests",
#                                    credentials=pika.PlainCredentials(user.username, user.password), exchange=unit.name, queueName=unit.uuid+"-Results", callback=self.handleReceivedTestResults, arguments={})
#
#     #the purpose of this method is to handle i am alive messages send by system units when they de-register from the
#     ##time structure
#     @authenticate_user_access
#     def removeSystemUnit(self, user, system, unit):
#         static_system = Unit(name=system.name, uuid='', type=system.type)
#         #1 update system structure
#         if self.db.existsUnit(static_system):
#             lock = threading.Lock()
#             lock.acquire()
#             try:
#                 static_system = self.db.getUnit(static_system)
#                 run_time_system = self.db.getUnit(Unit(name=system.name, uuid=system.name, type=system.type))
#                 run_time_system = self.systemStructureManagementEngine.removeUnitInstance(run_time_system.toUnit(), unit)
#                 self.db.update(UnitDAO.toDAO(run_time_system))
#             finally:
#                 lock.release()
#         else:
#             raise ValueError("System with ID " + system.name + " and UUID " + system.uuid + " does not exist")
#         #2. if existing delete queue used for tests
#         # QueueUtil.removeQueue(self.queueIP, system.name,   credentials=self.queueCredentials,  queueName=unit.uuid)
#         QueueUtil.removeQueue(self.queueIP, system.name,   credentials=pika.PlainCredentials(user.username, user.password),  queueName=unit.uuid+"-Tests")
#         QueueUtil.removeQueue(self.queueIP, system.name,   credentials=pika.PlainCredentials(user.username, user.password),  queueName=unit.uuid+"-Results")
#
#
#     @authenticate_user_access
#     def getRunTimeSystem(self, user, system):
#         return self.db.getUnit(system)
#
#     @authenticate_user_access
#     def getLastTestsStatus(self, user, system):
#         systemDAO =  self.db.getUnit(system)
#         system = systemDAO.toUnit()
#         for unit in system.toList():
#             unit.testsStatus = {}
#             for testExecution in self.db.getLastTestExecutionsForUnit(unit):
#
#                 testResult = None
#                 test = self.db.getTestForExecution(testResult)
#                 if testExecution.finalized:
#                     testResult = TestResult(testID=test.id, executionID=testExecution.id, executorUnit = self.db.getExecutorUnitForTestExecution(testExecution)
#                         ,targetUnit = self.db.getTargetUnitForTestExecution(testExecution),
#                         successful = False, details="Executing")
#                 else:
#                     testResult = self.db.getTestResultForExecution(testExecution)
#                 unit.testsStatus[test.name]= testResult
#         return system
#
#     def handleReceivedTestResults(self, channel, method, properties, body):
#         message = pickle.loads(body)
#         channel.basic_ack(delivery_tag = method.delivery_tag)
#
#         #process message depending on type
#         if message.type == MessageType.TestResult:
#             raise NotImplementedError("Not implemented yet")
#         else:
#             logging.warn("Received message type " + str(message.type) + " instead of MessageType.UnitInstanceInformation=" + str(MessageType.UnitInstanceInformation))
#
#
#     #ALIVE messages are sent after a unit starts/is created
#     #used in allocating queues for unit tests and adding unit in the run-time system
#     def handleReceivedAliveMessage(self, channel, method, properties, body):
#         message = pickle.loads(body)
#         channel.basic_ack(delivery_tag = method.delivery_tag)
#
#         #process message depending on type
#         if message.type == MessageType.UnitInstanceInformation:
#             unitInstanceInfo = message.body
#             if unitInstanceInfo:
#                  self.addSystemUnit(User(username=unitInstanceInfo.username,password=unitInstanceInfo.password),
#                                     system=Unit(name=unitInstanceInfo.name, uuid=unitInstanceInfo.system, type=UnitType.Composite),
#                                     unit=Unit(name=unitInstanceInfo.name, uuid=unitInstanceInfo.uuid, type=unitInstanceInfo.type))
#             else:
#                  logging.warn("No content received for message " + str(message.type ) )
#         else:
#             logging.warn("Received message type " + str(message.type) + " instead of MessageType.UnitInstanceInformation=" + str(MessageType.UnitInstanceInformation))
#
#     #DEAD messages are sent before th unit is to be destroyed/stopped
#     #used in decoupling any queues allocated and removing the unit from the run-time system
#     def handleReceivedDeadMessage(self, channel, method, properties, body):
#         message = pickle.loads(body)
#         channel.basic_ack(delivery_tag = method.delivery_tag)
#
#         #process message depending on type
#         if message.type == MessageType.UnitInstanceInformation:
#             unitInstanceInfo = message.body
#             if unitInstanceInfo:
#                  self.removeSystem(User(username=unitInstanceInfo.username,password=unitInstanceInfo.password),
#                                     system=Unit(name=unitInstanceInfo.name, uuid=unitInstanceInfo.system, type=UnitType.Composite),
#                                     unit=Unit(name=unitInstanceInfo.name, uuid=unitInstanceInfo.uuid, type=unitInstanceInfo.type))
#             else:
#                  logging.warn("No content received for message " + str(message.type ) )
#         else:
#             logging.warn("Received message type " + str(message.type) + " instead of MessageType.UnitInstanceInformation=" + str(MessageType.UnitInstanceInformation))
