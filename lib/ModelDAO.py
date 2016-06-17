#!/usr/bin/env python
from sqlalchemy.orm.exc import NoResultFound

__author__ = 'TU Wien'
__copyright__ = "Copyright 2015, TU Wien, Distributed Systems Group"
__license__ = "Apache LICENSE"
__version__ = "2.0"
__maintainer__ = "Daniel Moldovan"
__email__ = "d.moldovan@dsg.tuwien.ac.at"
__status__ = "Prototype"

#class implementing functionality to store and retrieve internal model from Database

from sqlalchemy import Column, DateTime, String,Boolean, Integer, ForeignKey, func, PickleType, ForeignKeyConstraint, distinct
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from lib.Common import ExecutableTest, TestResult
from lib.Parsers import TestDescriptionParser
import commands, yaml, logging, threading

from lib.Model import Unit, UnitType, CommunicationLink, Link, EventEncounter

Base = declarative_base()

class UnitTypeDAO(Base):
    __tablename__ = 'UnitType'
    type = Column(String, primary_key=True)
    description=Column(String)

    def __str__( self):
        return "{'type='" + self.type + ", description=" + self.description + "}"

    def find_key(self, value, dictionary):
        return reduce(lambda x, y: x if x is not None else y,
                  map(lambda x: x[1] if x[1] == value else None,
                      dictionary.iteritems()))

    def toUnitType(self):
      return self.find_key(self.type, UnitType.__dict__)

    def __eq__(self, other):
        if type(other) is UnitTypeDAO:
            return self.type == other.type
        else:
            return self.type == other

    @staticmethod
    def toDAO(type):
        return UnitTypeDAO(type= str(type), description=str(type))
    # def toUnitType(self):
    #   types = {
    #           "OperatingSystem": UnitType.VirtualMachine ,
    #         "ApplicationContainer": UnitType.AppContainer ,
    #         "SoftwareContainer" :UnitType.SoftwareContainer,
    #        "SoftwarePlatform":UnitType.SoftwarePlatform ,
    #        "SoftwareArtifact": UnitType.SoftwareArtifact ,
    #         "Process":UnitType.Process ,
    #         "Composite":UnitType.Composite  }
    #   return types[self.name]

class SystemDAO(Base):
    __tablename__ = 'System'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(PickleType)

class UnitDAO(Base):
    __tablename__ = 'Unit'
    pk = Column(Integer, primary_key=True) #need this for consistency
    id = Column(String)
    uuid = Column(String)
    name = Column(String)
    type_id = Column(String, ForeignKey('UnitType.type'))
    type = relationship("UnitTypeDAO", primaryjoin = "UnitDAO.type_id == UnitTypeDAO.type", lazy='joined')
    system_id = Column(Integer, ForeignKey('System.id'))
    # hostedUnitAssociations = relationship("HostedUnitAssociation", primaryjoin = "UnitDAO.dbID == HostedUnitAssociation.parent_id")#parent_id is THIS parent

    def __eq__(self, other):
        if type(other) is UnitDAO:
            return self.name == other.name and  self.uuid == other.uuid and self.id == other.id
        elif type(other) is Unit:
            return self.name == other.name and  self.uuid == other.uuid and self.id == other.id

        elif type(other) is UnitType:
            return self.type == other

    def __str__( self):
        return "{'name='" + self.name + ", type=" + str(self.type) + ", uuid=" + self.uuid + "}"

    def toUnit(self):
        unit = Unit(name=self.id, uuid=self.uuid, type=self.type.toUnitType(), containedUnits=[])
        # for association in self.hostedUnitAssociations:
        #     hostedUnit = association.hostedUnit.toUnit()
        #     unit.hostedUnits.append(hostedUnit)
        return unit

    # i need to give the Type fto avoid duplicate types for each unit I insert. so when I add new unit, i need the type
    #otherwise, we do not supply it, so take it from the type field
    @staticmethod
    def toDAO(unit, systemID, typeDAO=None):
        if typeDAO is None:
            typeDAO = UnitTypeDAO.toDAO(unit.type)
        if unit.uuid is None:
            unit.uuid = unit.name
        unitDAO = UnitDAO(id=unit.name,system_id = systemID, name=unit.name,uuid=unit.uuid,type=typeDAO)
        # for hosted in unit.hostedUnits:
        #     assoc = HostedUnitAssociation()
        #     hostedDAO = UnitDAO.toDAO(hosted, systemID)
        #     assoc.hostedUnit = hostedDAO
        #     unitDAO.hostedUnitAssociations.append(assoc)
        return unitDAO

#
# #not used as at run-time the added unit does nopw know parrent. to find ut I always parse static descr
class containedUnitsDAO(Base):
    __tablename__ = 'containedUnits'
    parent_id = Column(Integer, ForeignKey('Unit.id'),  primary_key=True)
    contained_id = Column(Integer, ForeignKey('Unit.id'),  primary_key=True)

class HostedUnitAssociation(Base):
    __tablename__ = 'HostedUnitAssociations'
    parent_id = Column(Integer, ForeignKey('Unit.id'),  primary_key=True)
    hosted_id = Column(Integer, ForeignKey('Unit.id'),  primary_key=True)
    # parent_id = Column(Integer, ForeignKey('Unit.dbID'),  primary_key=True)
    # hosted_id = Column(Integer, ForeignKey('Unit.dbID'),  primary_key=True)
    # hostedUnit = relationship("UnitDAO", primaryjoin = "UnitDAO.dbID == HostedUnitAssociation.hosted_id") #relationship which is Hosted? hosted_id



#models the test itself, the python code to execute
class TestDAO(Base):
    __tablename__ = 'Test'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    meta = Column(PickleType)
    content=Column(String)

    def __eq__(self, other):
        if type(other) is TestDAO:
            return self.name == other.name
        else:
            return other == self

    def toTest(self):
        return ExecutableTest(name=self.name, meta=self.meta, test=self.content)

    @staticmethod
    def toDAO(test):
        return TestDAO(name=test.name, meta=test.meta, content=test.test)

#models the description of how.when/and on what to execute
class TestDescriptionDAO(Base):
    __tablename__ = 'TestDescription'
    id = Column(Integer, primary_key=True)
    test_id = Column(Integer, ForeignKey('Test.id'))
    system_id = Column(Integer, ForeignKey('System.id'))
    name = Column(String)
    rawTextDescription = Column(String)
    test = relationship("TestDAO", primaryjoin = "TestDescriptionDAO.test_id == TestDAO.id", lazy='joined')

    @staticmethod
    def toDAO(system, testDescription, originalTextDescription):
        return TestDescriptionDAO(system_id=system.id, name=testDescription.name, rawTextDescription=originalTextDescription)

    def toTestDescription(self):
        return TestDescriptionParser().parseTestDescriptionFromText(self.rawTextDescription)
#
#
# #executor: Type.VirtualMachine for Type.VirtualContainer, Type.Process
# #so we will create one execution info for each from to entry.
# class TestExecutorInfoDAO(Base):
#     __tablename__ = 'TestExecutorInfoDAO'
#     id = Column(Integer, primary_key=True)
#     test_description_id = Column(Integer, ForeignKey('TestDescription.id'))
#     targetInfo = Column(String)
#     executorInfo = Column(String)
#
#     #targetIdentifier is not an ID, but currently a more complex string
#     #ForExample Type.VirtualContainer, UnitID.NODENAME, or UnitUUID.10.9.9.95
#     @staticmethod
#     def toDAO(targetIdentifier, executorIdentifier):
#         dao =  TestExecutorInfoDAO(name=testDescription.name, timeout=testDescription.timeout)
#
#
#
# class PeriodicExecutionTriggerDAO(Base):
#     __tablename__ = 'PeriodicExecutionTrigger'
#     id = Column(Integer, primary_key=True)
#     test_description_id = Column(Integer, ForeignKey('TestDescription.id'))
#     period = Column(Integer) #integer
#     periodUnit = Column(String) #supports s,m,h,d (second, minute, hour, day)
#
#
# #we can specify event:  "E1" , "E2" on Type.VirtualMachine
# #so we will create one EventBasedExecutionTriggerDAO for each E1 on Type, E2 on Type, etc
# class EventBasedExecutionTriggerDAO(Base):
#     __tablename__ = 'EventBasedExecutionTrigger'
#     id = Column(Integer, primary_key=True)
#     test_description_id = Column(Integer, ForeignKey('TestDescription.id'))
#     event = Column(String)
#     eventTarget = Column(String)
#


class TestResultDAO(Base):
    __tablename__ = 'TestResult'
    id = Column(Integer, primary_key=True)
    test_id = Column(Integer, ForeignKey('Test.id'))
    execution_id = Column(Integer, ForeignKey('TestExecution.id'))
    testExecution = relationship("TestExecutionDAO", primaryjoin = "TestResultDAO.execution_id == TestExecutionDAO.id", lazy='joined')
    test = relationship("TestDAO",uselist=False, primaryjoin = "TestResultDAO.test_id == TestDAO.id", lazy='joined')
    system_id=Column(Integer, ForeignKey('System.id'))
    successful = Column(Boolean)
    details = Column(String)
    timestamp = Column(DateTime)

    def toTestResult(self):
        return TestResult(testID=self.test_id, executionID=self.execution_id,
                          targetUnit=Unit(uuid=self.testExecution.target_unit_uuid,name=self.testExecution.target_unit_name, type = UnitType.toType(self.testExecution.target_unit_type_id)),#type=db.getUnitTypeByID(self.testExecution.target_unit_type_id)),
                          executorUnit=Unit(uuid=self.testExecution.executor_unit_uuid,name=self.testExecution.executor_unit_name, type = UnitType.toType(self.testExecution.executor_unit_type_id)), #type=db.getUnitTypeByID(self.testExecution.executor_unit_type_id)),
                          successful=self.successful, details= self.details, timestamp = self.timestamp)

    @staticmethod
    def toTestResultDAO(testResult, targetUnitID, executorUnitID):
        return TestResultDAO(test_id=testResult.test_id, execution_id=testResult.executionID, successful = testResult.successful,
                             details = testResult.details, timestamp = testResult.timestamp)


#just holds latest text execution info for each test
#used to speed up retrieval of last executions
class LastTestExecutions(Base):
    #TODO: add System ID here to avoid not issues with same UUID in different systems
    print "TODO: add System ID in LastTestExecutions in ModelDAO to avoid not issues with same UUID in different system"
    __tablename__ = 'LastTestExecutions'
    unit_uuid = Column(Integer, ForeignKey('Unit.uuid'), primary_key=True)
    test_id = Column(Integer, ForeignKey('Test.id'), primary_key=True)
    test_execution_id = Column(Integer, ForeignKey('TestExecution.id'), primary_key=True)
    testExecution = relationship("TestExecutionDAO", primaryjoin = "LastTestExecutions.test_execution_id == TestExecutionDAO.id", lazy='joined')
    system_id=Column(Integer, ForeignKey('System.id'))


#the thing here is that if I have direct foreign key relationships to units. the units dissapear as the system is elastic. so, i loose data
class TestExecutionDAO(Base):
    __tablename__ = 'TestExecution'
    id = Column(Integer, primary_key=True)
    test_id = Column(Integer, ForeignKey('Test.id'))

    target_unit_uuid= Column(Integer, ForeignKey('Unit.uuid'))
    target_unit_type_id = Column(Integer, ForeignKey('Unit.type_id'))
    target_unit_name = Column(Integer, ForeignKey('Unit.name'))

    executor_unit_uuid = Column(Integer, ForeignKey('Unit.uuid'))
    executor_unit_type_id = Column(Integer, ForeignKey('Unit.type_id'))
    executor_unit_name = Column(Integer, ForeignKey('Unit.name'))

    system_id=Column(Integer, ForeignKey('System.id'))

    test = relationship("TestDAO", uselist=False, primaryjoin = "TestExecutionDAO.test_id == TestDAO.id", lazy='joined')

    finalized = Column(Boolean)

    # @staticmethod
    # def toTestExecutionDAO(testResult):
    #     return TestExecutionDAO(test_id=testResult.test_id, id = testResult.executionID, target_unit_uuid = testResult.targetUnit.uuid
    #                             ,target_unit_type_id = testResult.targetUnit.type.type ,target_unit_name = testResult.targetUnit.name ,
    #                             executor_unit_uuid = testResult.executorUnit.uuid ,executor_unit_type_id = testResult.executorUnit.type.type
    #                             ,executor_unit_name = testResult.executorUnit.name,
    #                             finalized= False)

#the frame just aggregates all tests executed in a certain execution step
class TestSessionDAO(Base):
    __tablename__ = 'TestSession'
    id = Column(Integer, primary_key=True)
    system_id=Column(Integer, ForeignKey('System.id'))
    timestamp = Column(DateTime) #fir objects of type such as datetime.datetime.now()
    reason = Column(String)
    calledTests = relationship(
        'TestExecutionDAO',
        secondary='SessionTests',
        primaryjoin = "TestSessionDAO.id == SessionTestsDAO.session_id",
        secondaryjoin = "TestExecutionDAO.id == SessionTestsDAO.test_execution_id",
        cascade="all, delete-orphan",
        single_parent=True, lazy='joined'
    )


class SessionTestsDAO(Base):
    __tablename__ = 'SessionTests'
    session_id = Column(Integer, ForeignKey('TestSession.id'),  primary_key=True)
    test_execution_id = Column(Integer, ForeignKey('TestExecution.id'),  primary_key=True)



class UserDAO(Base):
    __tablename__ = 'User'
    id = Column(Integer, primary_key=True)
    username = Column(String)
    password = Column(String)
    managedSystems = relationship(
        'SystemDAO',
        secondary='UserSystems',
        primaryjoin = "UserDAO.id == UserSystemsDAO.user_id",
        secondaryjoin = "SystemDAO.id == UserSystemsDAO.system_id",
        cascade="all, delete-orphan",
        single_parent=True, lazy='joined'
    )
    managedTests = relationship(
        'TestDAO',
        secondary='UserTests',
        primaryjoin = "UserDAO.id == UserTestsDAO.user_id",
        secondaryjoin = "TestDAO.id == UserTestsDAO.test_id",
        cascade="all, delete-orphan",
        single_parent=True, lazy='joined'
    )
    #notification mail details
    #in the future maybe move in diff table
    mailUsername = Column(String, nullable=True)
    mailPassword =  Column(String, nullable=True)
    mailAddress =  Column(String, nullable=True)
    smtpServerName = Column(String, nullable=True)
    smtpServerPort = Column(Integer, nullable=True)


    @staticmethod
    def toDAO(user):
        dao = UserDAO(username=  user.username, password= user.password)
        if hasattr(user,'notificationMailInfo') and user.notificationMailInfo:
            dao.mailUsername = user.notificationMailInfo.username
            dao.mailPassword = user.notificationMailInfo.password
            dao.mailAdress = user.notificationMailInfo.mailAdress
            dao.smtpServerName = user.notificationMailInfo.smtpServerName
            dao.smtpServerPort = user.notificationMailInfo.smtpServerPort
        return dao
    #departments = relationship('Department', secondary='department_employee_link')


class UserTestsDAO(Base):
    __tablename__ = 'UserTests'
    user_id = Column(Integer, ForeignKey('User.id'),  primary_key=True)
    test_id = Column(Integer, ForeignKey('Test.id'),  primary_key=True)

class UserSystemsDAO(Base):
    __tablename__ = 'UserSystems'
    user_id = Column(Integer, ForeignKey('User.id'),  primary_key=True)
    system_id = Column(Integer, ForeignKey('System.id'),  primary_key=True)

# class SimpleTestsConfigurationDAO(Base):
#     __tablename__ = 'SimpleTestsConfiguration'
#     system_id = Column(Integer, ForeignKey('System.id'),  primary_key=True)
#     config = Column(PickleType)
#
# class ComplexTestsConfigurationDAO(Base):
#     __tablename__ = 'ComplexTestsConfiguration'
#     system_id = Column(Integer, ForeignKey('System.id'),  primary_key=True)
#     config = Column(PickleType)


class EventEncounterDAO(Base):
    __tablename__ = 'EventEncounter'
    id = Column(Integer, primary_key=True)
    eventType = Column(String)
    details = Column(String)
    timestamp = Column(DateTime)
    system_id = Column(Integer, ForeignKey('System.id'))
    system = relationship("SystemDAO", primaryjoin = "EventEncounterDAO.system_id == SystemDAO.id", lazy='joined')

    @staticmethod
    def toDAO(encounter):
        return EventEncounterDAO(eventType = encounter.type, timestamp = encounter.timestamp,
                                 system_id = encounter.system.id, details = encounter.details)
    def toEventEncounter(self):
        return EventEncounter(type=self.eventType, timestamp=self.timestamp, system = self.system, details=self.details)


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class DatabaseManagement(object):
    def __init__(self, dbPath="./test_db.sql"):
        # creator = lambda: sqlite3.connect('file::memory:?cache=shared')
        engine = create_engine('sqlite:///' + dbPath, connect_args={'check_same_thread':False}) #,creator = creator)
        self.session_maker = sessionmaker()
        self.session_maker.configure(bind=engine)
        Base.metadata.create_all(engine)

    def add(self, object):
        session = None
        try:
            session = self.session_maker()
            session.add(object)
            session.commit()
        except Exception as e:
            logging.exception(e,exc_info=True)
            session.rollback()
        finally:
            session.close()

    def remove(self, object):
        session = None
        try:
            session = self.session_maker()
            session.delete(object)
            session.commit()
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()

    def removeSystem(self, system):
        session = None
        try:
            session = self.session_maker()
            systemDAO = self.getSystem(system)
            units = self.getSystemUnits(systemDAO)
            for unit in units:
                testExecutions = self.getAllTestExecutionsForUnit(unit)
                for testExecution in testExecutions:
                    session.delete(testExecution)
                session.delete(unit)
            session.delete(systemDAO)
            session.commit()
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()


    def removeUnit(self, unit, system):
        session = None
        try:
            session = self.session_maker()
            unitDAO = self.getUnit(unit, system)
            if unitDAO:
               # leave test executions for unit here, for historical purposes
               # or if really want to delete, also detele test execution results for consistency

               # testExecutions = self.getAllTestExecutionsForUnit(unitDAO)
               # for testExecution in testExecutions:
               #    session.delete(testExecution)
               session.delete(unitDAO)
               session.commit()
            else:
               logging.warn("Trying to delete inexistent unit " + unit.__str__())
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()

    def getEntity(self, entityClass, id):
        result =None
        session = None
        try:
            session = self.session_maker()
            result = session.query(entityClass).filter(entityClass.id == id).one()
        except NoResultFound:
            #just eat this exception
            print("No result found")
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result

    def existsUser(self, user):
        result =None
        session = None
        try:
            session = self.session_maker()
            result = len(session.query(UserDAO).filter(UserDAO.username == user.username).filter(UserDAO.password == user.password).all()) > 0
        except NoResultFound:
            #just eat this exception
            pass
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result

    def getUser(self, user):
        result =None
        session = None
        try:
            session = self.session_maker()
            result = session.query(UserDAO).filter(UserDAO.username == user.username).filter(UserDAO.password == user.password).one()
        except NoResultFound:
             pass
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result

    def getUserByUsername(self, username):
        result =None
        session = None
        try:
            session = self.session_maker()
            result = session.query(UserDAO).filter(UserDAO.username == username).one()
        except NoResultFound:
             pass
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result

    def getAllUsers(self):
        result =[]
        session = None
        try:
            session = self.session_maker()
            result = session.query(UserDAO).all()
        except NoResultFound:
            #just eat this exception
            pass
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result

    def getUserByID(self, id):
        result =None
        session = None
        try:
            session = self.session_maker()
            result = session.query(UserDAO).filter(UserDAO.id == id).one()
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result

    def addEventEncounter(self, encounter):
        self.add(EventEncounterDAO.toDAO(encounter = encounter))

    #used in reporting test results to user
    def getUserTestsDaoForTestID(self, id):
        result =None
        session = None
        try:
            session = self.session_maker()
            result = session.query(UserTestsDAO).filter(UserTestsDAO.test_id == id).one()
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result


    def getUserForTestID(self, testName):
        result =None
        session = None
        test = self.getTestByName(testName)
        userTestsDao = self.getUserTestsDaoForTestID(test.id)
        try:
            session = self.session_maker()
            result = session.query(UserDAO).filter(UserDAO.id == userTestsDao.user_id).one()
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result

    def existsUsername(self, user):
        result =None
        session = None
        try:
            session = self.session_maker()
            result = len(session.query(UserDAO).filter(UserDAO.username == user.username).all()) > 0
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result

    def existsUnit(self, unit, system):
        result =None
        session = None
        try:
            session = self.session_maker()
            result = len(session.query(UnitDAO).filter(UnitDAO.uuid == unit.uuid).filter(UnitDAO.name == unit.name ).filter(UnitDAO.system_id == system.id ).all()) > 0
        except Exception as e:
            logging.exception(e)
        finally:
            session.close()
        return result


    def existsSystem(self, system):
        result =None
        session = None
        try:
            session = self.session_maker()
            result = len(session.query(SystemDAO).filter(SystemDAO.name == system.name).all()) > 0
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result

    def hasAccess(self, user, system):
        result =None
        session = None
        try:
            session = self.session_maker()
            result = len(session.query(UserDAO).filter(UserDAO.managedSystems.any(SystemDAO.name == system.name)).filter(UserDAO.username == user.username ).filter(UserDAO.password == user.password).all()) > 0
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result

    # def getUnit(self, unit):
    #    return session.query(UnitDAO).filter(UnitDAO.uuid == unit.uuid).filter(UnitDAO.name == unit.name ).one()

    def getUnitParent(self, unit, system):
        result =None
        session = None
        try:
            unit = self.getUnit(unit=unit,system=system)
            session = self.session_maker()
            parentID = session.query(containedUnitsDAO).filter(containedUnitsDAO.contained_id == unit.id).one()
            result = session.query(UnitDAO).filter(UnitDAO.id == parentID).filter(UnitDAO.system_id == system.id ).one()
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result

    def getUnit(self, unit, system):
        result =None
        session = None
        try:
            session = self.session_maker()
            result = session.query(UnitDAO).filter(UnitDAO.uuid == unit.uuid).filter(UnitDAO.name == unit.name ).filter(UnitDAO.system_id == system.id ).one()
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result

    def getUnitByUUID(self, uuid, system):
        result =None
        session = None
        try:
            session = self.session_maker()
            result = session.query(UnitDAO).filter(UnitDAO.uuid == uuid).filter(UnitDAO.system_id == system.id ).one()
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result


    def getUnitByType(self, type, system):
        result =None
        session = None
        try:
            session = self.session_maker()
            result = session.query(UnitDAO).filter(UnitDAO.type.has(UnitTypeDAO.type == type)).filter(UnitDAO.system_id == system.id).all()
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result

    def getUnitByName(self, unit, system):
        result =None
        session = None
        try:
            session = self.session_maker()
            result = session.query(UnitDAO).filter(UnitDAO.name == unit.name ).filter(UnitDAO.system_id == system.id ).all()
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result


    def getUnitsForHost(self,host):
        result =[]
        session = None
        try:
            session = self.session_maker()
            result = session.query(UnitDAO).filter(host.uuid in UnitDAO.uuid).one()
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result

    def getUnitsForHostByType(self,host, unitType):
        result =[]
        session = None
        try:
            session = self.session_maker()
            result = session.query(UnitDAO).filter(host.uuid in UnitDAO.uuid).filter(UnitDAO.type.any(unitType in UnitTypeDAO.type)).one()
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result

    def getUnitsForHostByTypeAndName(self,host, unitType, name):
        result =[]
        session = None
        try:
            session = self.session_maker()
            result = session.query(UnitDAO).filter(host.uuid in UnitDAO.uuid).filter(UnitDAO.name == name).filter(UnitDAO.type.any(unitType in UnitTypeDAO.type)).one()
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result


    def getSystemUnits(self, system):
        result =[]
        session = None
        try:
            session = self.session_maker()
            result = session.query(UnitDAO).filter(UnitDAO.system_id == system.id ).all()
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result

    def getSystemDescription(self, system):
        result =None
        session = None
        try:
            session = self.session_maker()
            result = session.query(UnitDAO).filter(UnitDAO.system_id == system.id ).filter(UnitDAO.name == system.name).one()
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result

    def getSystem(self, system):
        result =None
        session = None
        try:
            session = self.session_maker()
            result = session.query(SystemDAO).filter(SystemDAO.name == system.name).one()
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result

    def getSystemByName(self, name):
        result =None
        session = None
        try:
            session = self.session_maker()
            result = session.query(SystemDAO).filter(SystemDAO.name == name).one()
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result

    def getTest(self, test):
        result =None
        session = None
        try:
            session = self.session_maker()
            result = session.query(TestDAO).filter(TestDAO.name == test.name).one()
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result

    def getTestByName(self, name):
        result =None
        session = None
        try:
            session = self.session_maker()
            result = session.query(TestDAO).filter(TestDAO.name == name).one()
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result

    def existsTest(self, test):
        result =None
        session = None
        try:
            session = self.session_maker()
            result = len(session.query(TestDAO).filter(TestDAO.name ==test.name).all()) > 0
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result


    def getTestForExecution(self, testExecution):
        result =None
        session = None
        try:
            session = self.session_maker()
            result = session.query(TestDAO).filter(TestDAO.id==testExecution.test_id).one()
        except NoResultFound:
            #just eat this exception
            print("No result found")
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result

    def getTestExecutionInfo(self, info):
        result =None
        session = None
        try:
            session = self.session_maker()
            result = session.query(TestExecutionDAO).filter(TestExecutionDAO.id == info.id).one()
        except NoResultFound:
            #just eat this exception
            print("No result found")
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result

    def getTestExecutionInfoByID(self, id):
        result =None
        session = None
        try:
            session = self.session_maker()
            result = session.query(TestExecutionDAO).filter(TestExecutionDAO.id == id).one()
        except NoResultFound:
            #just eat this exception
            print("No result found")
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result


    def getPreviousTestExecutionInfoByCurrentExecutionID(self, executionID, targetUnit):
        result = None
        session = None
        try:
            session = self.session_maker()
            prevExecutionID = session.query(func.max(TestExecutionDAO.id)).filter(TestExecutionDAO.target_unit_uuid == targetUnit.uuid).filter(TestExecutionDAO.id < executionID).one()[0]
            result = session.query(TestExecutionDAO).filter(TestExecutionDAO.id == prevExecutionID).one()
        except NoResultFound:
            #just eat this exception
            print("No result found")
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result


    def getUnitType(self, type):
        result =None
        session = None
        try:
            session = self.session_maker()
            result = session.query(UnitTypeDAO).filter(UnitTypeDAO.type == type.type).one()
        except NoResultFound:
            #just eat this exception
            print("No result found")
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result


    def existsUnitType(self, type):
        result =None
        session = None
        try:
            session = self.session_maker()
            result = session.query(UnitTypeDAO).filter(UnitTypeDAO.type == type.type).all()
        except NoResultFound:
            #just eat this exception
            print("No result found")
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return len(result) > 0

    def getMaxTestExecutionID(self):
        result =None
        session = None
        try:
            session = self.session_maker()
            result = session.query(func.max(TestExecutionDAO.id)).one()[0]
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        if  result is not None:
           return result
        else:
           return 0

    def getLastTestExecutionsForUnit(self, targetUnit):
        result =[]
        session = None
        try:
             session = self.session_maker()
             lastExecutionEntries = session.query(LastTestExecutions).filter(LastTestExecutions.unit_uuid==targetUnit.uuid).all()
             for executionEntry  in lastExecutionEntries:
                   result.append(executionEntry.testExecution)
        except NoResultFound:
            #just eat this exception
            pass
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result

    def deleteLastTestExecutionsForUnit(self, system, targetUnit):
        result =[]
        session = None
        try:
             session = self.session_maker()
             result = session.query(LastTestExecutions).filter(LastTestExecutions.unit_uuid==targetUnit.uuid).all()

        except NoResultFound:
            #just eat this exception
            pass
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()

        for executionEntry in result:
            self.remove(executionEntry)

        return result

    def getLastTestSessionForSystem(self, system):
        result =[]
        session = None
        try:
             session = self.session_maker()
             maxSessionIDForSystem = session.query(func.max(TestSessionDAO.id)).filter(TestSessionDAO.system_id == system.id).one()[0]
             result = session.query(TestSessionDAO).filter(TestSessionDAO.system_id == system.id).filter(TestSessionDAO.id == maxSessionIDForSystem).one()

        except NoResultFound:
            #just eat this exception
            pass
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result

    def getAllTestSessionsForSystem(self, system):
        result =[]
        session = None
        try:
             session = self.session_maker()
             result = session.query(TestSessionDAO).filter(TestSessionDAO.system_id == system.id).all()
        except NoResultFound:
            #just eat this exception
            pass
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result

    def deleteAllTestSessionsForSystem(self, system):
        session = None
        try:
             session = self.session_maker()
             session.query(TestSessionDAO).filter(TestSessionDAO.system_id == system.id).delete()
             session.commit()
        except NoResultFound:
            #just eat this exception
            pass
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()

    def deleteAllTestExecutionsForSystem(self, system):
        session = None
        try:
             session = self.session_maker()
             session.query(TestExecutionDAO).filter(TestExecutionDAO.system_id == system.id).delete()
             session.commit()
        except NoResultFound:
            #just eat this exception
            pass
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()

    def getAllEventsForSystem(self, system):
        result =[]
        session = None
        try:
             session = self.session_maker()
             result = session.query(EventEncounterDAO).filter(EventEncounterDAO.system_id == system.id).all()
        except NoResultFound:
            #just eat this exception
            pass
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result

    def deleteAllEventsForSystem(self, system):
        session = None
        try:
             session = self.session_maker()
             session.query(EventEncounterDAO).filter(EventEncounterDAO.system_id == system.id).delete()
             session.commit()
        except NoResultFound:
            #just eat this exception
            pass
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()

    def getTestSessionsForSystemByReason(self, system, reason):
        result =[]
        session = None
        try:
             session = self.session_maker()
             result = session.query(TestSessionDAO).filter(TestSessionDAO.system_id == system.id).filter(TestSessionDAO.reason == reason).all()
        except NoResultFound:
            #just eat this exception
            pass
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result


    def getAllTestExecutionsForUnit(self, targetUnit, system):
        targetUnit = UnitDAO.toDAO(targetUnit,system.id)
        result =[]
        session = None
        try:
            session = self.session_maker()
            result = session.query(TestExecutionDAO).filter(TestExecutionDAO.target_unit_uuid==targetUnit.uuid).all()
        except NoResultFound:
            #just eat this exception
            pass
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result
     # #
     # return TestResult(testID=self.test_id, executionID=self.execution_id,
     #                      targetUnit=Unit(uuid=self.testExecution.target_unit_uuid,name=self.testExecution.target_unit_name,type=self.testExecution.target_unit_type),
     #                      executorUnit=Unit(uuid=self.testExecution.executor_unit_uuid,name=self.testExecution.executor_unit_name,type=self.testExecution.executor_unit_type),
     #                      successful=self.successful, details= self.details, timestamp = self.timestamp)
     #


    def getAllTestResultsForUnitByUUID(self, system, targetUnit, testReason=None):
        targetUnit = UnitDAO.toDAO(targetUnit,system.id)
        result =[]
        if not type:
            return result
        session = None
        try:
            session = self.session_maker()
            if testReason is None:
               result = session.query(TestResultDAO).filter(TestResultDAO.testExecution.has(TestExecutionDAO.target_unit_uuid == targetUnit.uuid)).all()
            else:
               result = []
               #else get session, and for all session tests, get result
               sessions = session.query(TestSessionDAO).filter(TestSessionDAO.system_id == system.id).filter(TestSessionDAO.reason == testReason).all()
               for session in sessions:
                   for execution in session.calledTests:
                       result.append(session.query(TestResultDAO).filter(TestResultDAO.testExecution.has(TestExecutionDAO.target_unit_uuid == targetUnit.uuid)).filter(TestResultDAO.execution_id == execution.id).one())
        except NoResultFound:
            #just eat this exception
            pass
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result

    def getAllTestResultsForUnitByName(self, system, targetUnit, testReason=None):
        targetUnit = UnitDAO.toDAO(targetUnit,system.id)
        result =[]
        session = None
        try:
            session = self.session_maker()
            if testReason is None:
               result = session.query(TestResultDAO).filter(TestResultDAO.testExecution.has(TestExecutionDAO.target_unit_name ==  targetUnit.name)).all()
            else:
               result = []
               #else get session, and for all session tests, get result
               sessions = session.query(TestSessionDAO).filter(TestSessionDAO.system_id == system.id).filter(TestSessionDAO.reason == testReason).all()
               for session in sessions:
                   for execution in session.calledTests:
                       result.append(session.query(TestResultDAO).filter(TestResultDAO.testExecution.has(TestExecutionDAO.target_unit_name ==  targetUnit.name)).filter(TestResultDAO.execution_id == execution.id).one())

        except NoResultFound:
            #just eat this exception
            pass
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result


    def getAllTestResultsForUnitByType(self,  system, targetUnit, testReason=None):
        type = self.getUnitType(UnitTypeDAO.toDAO(targetUnit.type))
        result =[]
        #can happen epescially for Composite at the system level. If nobody defined the level, there are
        #no resutls for it as nobody added it in the DB.
        #can be fixed by authomatically add in DB all types when starting thing
        if type is None:
            return result
        session = None
        try:
            session = self.session_maker()
            if testReason is None:
               result = session.query(TestResultDAO).filter(TestResultDAO.testExecution.has(TestExecutionDAO.target_unit_type_id == type.type)).all()
            else:
               result = []
               #else get session, and for all session tests, get result
               sessions = session.query(TestSessionDAO).filter(TestSessionDAO.system_id == system.id).filter(TestSessionDAO.reason == testReason).all()
               for session in sessions:
                   for execution in session.calledTests:
                       result.append(session.query(TestResultDAO).filter(TestResultDAO.testExecution.has(TestExecutionDAO.target_unit_type_id ==  type.type)).filter(TestResultDAO.execution_id == execution.id).one())
        except NoResultFound:
            #just eat this exception
            pass
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result


    def getAllTestExecutionsForUnit(self, targetUnit):
        result =[]
        session = None
        try:
            session = self.session_maker()
            result = session.query(TestExecutionDAO).filter(TestExecutionDAO.target_unit_uuid==targetUnit.uuid).all()
        except NoResultFound:
            #just eat this exception
            pass
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result

    def getAllTestExecutionsForUnitByUUID(self, system, targetUnit ):
        targetUnit = UnitDAO.toDAO(targetUnit,system.id)
        result =[]
        session = None
        try:
            session = self.session_maker()
            result = session.query(TestExecutionDAO).filter(TestExecutionDAO.target_unit_uuid == targetUnit.uuid).all()
        except NoResultFound:
            #just eat this exception
            pass
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result

    def deleteAllTestExecutionsForUnit(self, system, targetUnit ):
        targetUnit = UnitDAO.toDAO(targetUnit,system.id)
        result =[]
        try:
            for execution in self.getAllTestExecutionsForUnitByUUID(system,targetUnit):
               self.remove(execution)
        except Exception as e:
            logging.exception(e)

    def getAllTestExecutionsForUnitByName(self, system, targetUnit):
        targetUnit = UnitDAO.toDAO(targetUnit,system.id)
        result =[]
        session = None
        try:
            session = self.session_maker()
            result = session.query(TestExecutionDAO).filter(TestExecutionDAO.target_unit_name == targetUnit.name).all()
        except NoResultFound:
            #just eat this exception
            pass
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result

    def getAllTestExecutionsForUnitByType(self,  system, targetUnit):
        type = self.getUnitType(UnitTypeDAO.toDAO(targetUnit.type))
        result =[]

        if not type:
            return result
        session = None
        try:
            session = self.session_maker()
            result = session.query(TestExecutionDAO).filter(TestExecutionDAO.target_unit_type_id == type.type).all()
        except NoResultFound:
            #just eat this exception
            pass
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result


    def getTestExecutionsForUnitByUUID(self, system, targetUnit, test_id ):
        targetUnit = UnitDAO.toDAO(targetUnit,system.id)
        result =[]
        session = None
        try:
            session = self.session_maker()
            result = session.query(TestExecutionDAO).filter(TestExecutionDAO.test_id == test_id).filter(TestExecutionDAO.target_unit_uuid == targetUnit.uuid).all()
        except NoResultFound:
            #just eat this exception
            pass
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result

    def getTestExecutionsForUnitByName(self, system, targetUnit,test_id):
        targetUnit = UnitDAO.toDAO(targetUnit,system.id)
        result =[]
        session = None
        try:
            session = self.session_maker()
            result = session.query(TestExecutionDAO).filter(TestExecutionDAO.test_id == test_id).filter(TestExecutionDAO.target_unit_name == targetUnit.name).all()
        except NoResultFound:
            #just eat this exception
            pass
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result

    def getTestExecutionsForUnitByType(self,  system, targetUnit,test_id):
        targetUnit = UnitDAO.toDAO(targetUnit, system.id)
        result =[]
        session = None
        try:
            session = self.session_maker()
            result = session.query(TestExecutionDAO).filter(TestExecutionDAO.test_id == test_id).filter(TestExecutionDAO.target_unit_type_id == targetUnit.type.type).all()
        except NoResultFound:
            #just eat this exception
            pass
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result

    def getTestResultForExecution(self, execution):
        result =None
        session = None
        try:
            session = self.session_maker()
            result = session.query(TestResultDAO).filter(TestResultDAO.execution_id==execution.id).one()
        except NoResultFound:
            #just eat this exception
            pass
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result

    def deleteAllTestResultsForSystem(self, system):
        session = None
        try:
            session = self.session_maker()
            session.query(TestResultDAO).filter(TestResultDAO.system_id==system.id).delete()
            session.commit()
        except NoResultFound:
            #just eat this exception
            pass
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()

    def getAllTestResultForExecution(self, execution):
        result =[]
        session = None
        try:
            session = self.session_maker()
            result = session.query(TestResultDAO).filter(TestResultDAO.execution_id==execution.id).all()
        except NoResultFound:
            #just eat this exception
            pass
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result

    def hasTestResultForExecution(self, execution):
        result =None
        session = None
        try:
            session = self.session_maker()
            result = session.query(TestResultDAO).filter(TestResultDAO.execution_id==execution.id).all()
        except NoResultFound:
            #just eat this exception
            pass
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return len(result) > 0

    def getTargetUnitForTestExecution(self, execution):
        result =None
        session = None
        try:
            session = self.session_maker()
            result = session.query(UnitDAO).filter(UnitDAO.id == execution.target_unit_id).one()
        except NoResultFound:
            #just eat this exception
            pass
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result


    def getGenericTests(self):
        result =[]
        session = None
        try:
            session = self.session_maker()
            # create subquery
            subquery = session.query(UserTestsDAO.test_id)
            # select all from table_a not in subquery
            result = session.query(TestDAO).filter(~TestDAO.id.in_(subquery)).all()
        except NoResultFound:
            #just eat this exception
            pass
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result

    def getUnitTypeByID(self, id):
        result = None
        session = None
        try:
            session = self.session_maker()
            result = session.query(UnitTypeDAO).filter(UnitTypeDAO.type == id).one()
        except NoResultFound:
            #just eat this exception
            pass
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result

    #takes whole object as parameter, querry by example
    def getUnitType(self, type):
        result = None
        session = None
        try:
            session = self.session_maker()
            result = session.query(UnitTypeDAO).filter(UnitTypeDAO.type == type.type).one()
        except NoResultFound:
            #just eat this exception
            pass
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result

    def existsTestDescription(self, system, test):
        result =None
        session = None
        try:
            session = self.session_maker()
            result = session.query(TestDescriptionDAO).filter(TestDescriptionDAO.test_id == test.id).filter(TestDescriptionDAO.system_id == system.id).all()
        except NoResultFound:
            #just eat this exception
            pass
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return len(result) > 0

    def getTestDescriptionForTest(self, system, test):
        result = None
        session = None
        try:
            session = self.session_maker()
            result = session.query(TestDescriptionDAO).filter(TestDescriptionDAO.test_id == test.id).filter(TestDescriptionDAO.system_id == system.id).one()
        except NoResultFound:
            #just eat this exception
            pass
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result

    def removeDescriptionsForTest(self, system, test):
        result = None
        session = None
        try:
            session = self.session_maker()
            result = session.query(TestDescriptionDAO).filter(TestDescriptionDAO.test_id == test.id).filter(TestDescriptionDAO.system_id == system.id).all()
        except NoResultFound:
            #just eat this exception
            pass
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        for r in result:
            self.remove(r)

    def getAllTestDescriptionsForSystem(self, system):
        result = None
        session = None
        try:
            session = self.session_maker()
            result = session.query(TestDescriptionDAO).filter(TestDescriptionDAO.system_id == system.id).all()
        except NoResultFound:
            #just eat this exception
            pass
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result

    def getTestDescription(self, system, test):
        result = None
        session = None
        try:
            session = self.session_maker()
            result = session.query(TestDescriptionDAO).filter(TestDescriptionDAO.test_id == test.id).filter(TestDescriptionDAO.system_id == system.id).one()
        except NoResultFound:
            #just eat this exception
            pass
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result


    def getTestDescriptionByID(self, id):
        result = None
        session = None
        try:
            session = self.session_maker()
            result = session.query(TestDescriptionDAO).filter(TestDescriptionDAO.id == id).one()
        except NoResultFound:
            #just eat this exception
            pass
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result

    def getTestDescriptions(self, system):
        result = None
        session = None
        try:
            session = self.session_maker()
            result = session.query(TestDescriptionDAO).filter(TestDescriptionDAO.system_id == system.id).all()
        except NoResultFound:
            #just eat this exception
            pass
        except Exception as e:
            logging.exception(e)
        finally:
            session.close()
        return result

    def getLastTestExecutionForTest(self, test_id, unit_uuid):
        result = None
        session = None
        try:
            session = self.session_maker()
            result = session.query(LastTestExecutions).filter(LastTestExecutions.test_id == test_id).filter(LastTestExecutions.unit_uuid==unit_uuid).one()
        except NoResultFound:
            #just eat this exception
            pass
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result

    def getLastTestExecutionAfterExecutionID(self, test_execution_id):
        result = None
        session = None
        try:
            session = self.session_maker()
            result = session.query(LastTestExecutions).filter(LastTestExecutions.test_execution_id == test_execution_id).one()
        except NoResultFound:
            #just eat this exception
            pass
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result

    def getAllLastTestExecutionForTest(self, test_id, unit_uuid):
        result = None
        session = None
        try:
            session = self.session_maker()
            result = session.query(LastTestExecutions).filter(LastTestExecutions.test_id == test_id).filter(LastTestExecutions.unit_uuid==unit_uuid).all()
        except NoResultFound:
            #just eat this exception
            pass
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result

    def removeLastTestExecutionForTest(self, test_id):
        result = None
        session = None
        try:
            session = self.session_maker()
            result = session.query(LastTestExecutions).filter(LastTestExecutions.test_id == test_id).all()
        except NoResultFound:
            #just eat this exception
            pass
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        for execution in result:
            self.remove(execution)
        return


    def getTestForTestDescription(self, testDescription):
        result = None
        session = None
        try:
            session = self.session_maker()
            result = session.query(TestDAO).filter(TestDAO.id == testDescription.test_id).one()
        except NoResultFound:
            #just eat this exception
            pass
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()
        return result





    # def getExecutorUnitForTestExecution(self, execution):
    #     result =None
    #     session = None
    #     try:
    #         session = self.session_maker()
    #         result = session.query(UnitDAO).filter(UnitDAO.id == execution.executor_unit_id).one()
    #     except Exception as e:
    #         logging.exception(e)
    #     finally:
    #         session.close()
    #     return result

    # def getSimpleTestsConfiguration(self, system):
    #     result = None
    #     session = None
    #     try:
    #         session = self.session_maker()
    #         result = session.query(SimpleTestsConfigurationDAO).filter(SimpleTestsConfigurationDAO.system_id == system.id).one()
    #     except Exception as e:
    #         logging.exception(e)
    #     finally:
    #         session.close()
    #     return result
    #
    # def getComplexTestsConfiguration(self, system):
    #     result = None
    #     session = None
    #     try:
    #         session = self.session_maker()
    #         result = session.query(ComplexTestsConfigurationDAO).filter(ComplexTestsConfigurationDAO.system_id == system.id).one()
    #     except Exception as e:
    #         logging.exception(e)
    #     finally:
    #         session.close()
    #     return result

    #
    # def updateSimpleTestsConfiguration(self, system, simpleTestsConfigurationDAO):
    #     result = None
    #     session = None
    #     try:
    #         session = self.session_maker()
    #         result = session.query(SimpleTestsConfigurationDAO).filter(SimpleTestsConfigurationDAO.system_id == system.id).one()
    #         result.config = simpleTestsConfigurationDAO.config
    #         session.close()
    #     except Exception as e:
    #         #if exception means no row found for one
    #         self.add(simpleTestsConfigurationDAO)
    #         logging.exception(e)
    #     finally:
    #         session.close()
    #     return result
    #
    # def updateComplexTestsConfiguration(self, system, complexTestsConfigurationDAO):
    #     result = None
    #     session = None
    #     try:
    #         session = self.session_maker()
    #         result = session.query(ComplexTestsConfigurationDAO).filter(ComplexTestsConfigurationDAO.system_id == system.id).one()
    #         result.config = complexTestsConfigurationDAO.config
    #         session.close()
    #     except Exception as e:
    #         self.add(complexTestsConfigurationDAO)
    #         logging.exception(e)
    #     finally:
    #         session.close()
    #     return result

    def update(self, existing_object):
        session = None
        try:
            session = self.session_maker()
            session.merge(existing_object)
            session.commit()
        except Exception as e:
            logging.exception(e)
            session.rollback()
        finally:
            session.close()

    def markTestFinished(self, testResult):

        system = self.getSystem(SystemDAO(name=testResult.systemID))

        #mark test as finished
        executionInfo = self.getTestExecutionInfoByID(testResult.executionID)
        executionInfo.finalized = True
        self.update(executionInfo)

        #if multiple answers for same test things get messy
        lock = threading.Lock()
        lock.acquire(0)

        #if I have added fake result for "not responded in time" ensure we update it
        #not sure why it still adds two, one for not respnded in time and one for responded, so just remove both if there
        for testResultDAO in self.getAllTestResultForExecution(executionInfo):
           self.remove(testResultDAO)

        testResultDAO = TestResultDAO(test_id=executionInfo.test_id, execution_id=testResult.executionID, successful = testResult.successful,
                             details = testResult.details, system_id = system.id)
        self.add(testResultDAO)

        #make sure we remove all prev executions. not sure why but somewhere we add more. so this solves simptom not cause
        for lastExec in self.getAllLastTestExecutionForTest(test_id=executionInfo.test_id, unit_uuid=executionInfo.target_unit_uuid):
           self.remove(lastExec)

        lastExec = LastTestExecutions(unit_uuid=executionInfo.target_unit_uuid,test_id=executionInfo.test_id, test_execution_id=testResult.executionID, system_id=system.id)
        self.add(lastExec)

        lock.release()

