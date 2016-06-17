#!/usr/bin/env python
import commands
from lib.Control import Controller
from lib.ModelDAO import DatabaseManagement, TestExecutionDAO, UnitTypeDAO, SystemDAO, UnitDAO, HostedUnitAssociation

__author__ = 'TU Wien'
__copyright__ = "Copyright 2015, TU Wien, Distributed Systems Group"
__license__ = "Apache LICENSE"
__version__ = "2.0"
__maintainer__ = "Daniel Moldovan"
__email__ = "d.moldovan@dsg.tuwien.ac.at"
__status__ = "Prototype"

import unittest, yaml, pickle, pika
from lib.Model import Unit, UnitType, CommunicationLink, Link
from lib.Engines import SystemStructureManagementEngine, TestsManagementEngine
from lib.Utils import QueueUtil

#class used to test and debug the database interraction

class TestDB(unittest.TestCase):

     def testCreateDeleteUnit(self):


        # self.assertTrue(vmLB.containedUnits)
        # self.assertFalse(len(haproxy.containedUnits) > 0)

        commands.getoutput("rm /tmp/A.sql")
        databasePath ="/tmp/A.sql"
        db = DatabaseManagement(dbPath= databasePath)

        vmLB = Unit(name="VM.LoadBalancer", type=UnitType.VirtualMachine)
        haproxy = Unit(name="HAProxy", type=UnitType.Process)
        proxyConfigService = Unit(name="ConfigService", type=UnitType.Process)

        vmLB.hosts(proxyConfigService, haproxy)

        mqtt = Unit(name="LoadBalancer", type=UnitType.Composite, containedUnits=[vmLB, haproxy, proxyConfigService])

        vmEP = Unit(name="VM.EventProcessing", type=UnitType.VirtualMachine)
        dassWS = Unit(name="EventProcessingService", type=UnitType.Process)

        vmEP.hosts(dassWS)
        eventProcessing = Unit(name="EventProcessing", type=UnitType.Composite, containedUnits=[vmEP, dassWS])

        eventProcessing.connectsTo(haproxy)

        service = Unit(name="System", type=UnitType.Composite, containedUnits=[mqtt, eventProcessing])

        system_dao = SystemDAO(name=service.name, description = pickle.dumps(service))

        db.add(system_dao)

        system_dao = SystemDAO(name=service.name, description = pickle.dumps(service))

        system = db.getSystem(system_dao)

        db.add(UnitDAO.toDAO(vmLB,system.id))

        unit = db.getUnit(UnitDAO.toDAO(vmLB,system.id),system)

        print unit.name

if __name__ == '__main__':
    unittest.main()

