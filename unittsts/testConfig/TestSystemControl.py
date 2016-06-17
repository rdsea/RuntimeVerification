#!/usr/bin/env python
import json
import time

__author__ = 'TU Wien'
__copyright__ = "Copyright 2015, TU Wien, Distributed Systems Group"
__license__ = "Apache LICENSE"
__version__ = "2.0"
__maintainer__ = "Daniel Moldovan"
__email__ = "d.moldovan@dsg.tuwien.ac.at"
__status__ = "Prototype"

import unittest, yaml, pickle, pika
from lib.Model import Unit, UnitType, CommunicationLink, Link, User
from lib.ModelDAO import *
from lib.Engines import SystemStructureManagementEngine, TestsManagementEngine
from lib.Utils import QueueUtil
from lib.Converters import JSONConverter
from lib.Control import Controller

class TestSystemControl(unittest.TestCase):


     def test_dispatching_tests(self):


        commands.getoutput("rm ./test_db.sql")

        FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
        logging.basicConfig(format=FORMAT)
        logging.basicConfig(level=logging.DEBUG)

        controller = Controller(queueCredentials= pika.PlainCredentials('mela', 'mela'),
                                queueIP='128.130.172.230', dbPath="./test_db.sql")

        user = User(username="a", password="a")
        controller.addUser(user)

        vmLB = Unit(name="VM.LoadBalancer", type=UnitType.VirtualMachine)
        haproxy = Unit(name="HAProxy", type=UnitType.Process)
        proxyConfigService = Unit(name="ConfigService", type=UnitType.Process)
        vmLB.hosts(proxyConfigService, haproxy)

        mqtt = Unit(name="LoadBalancer", type=UnitType.Composite, containedUnits=[vmLB, haproxy, proxyConfigService])

        # controller.addSystem(user, mqtt)
        # retrieved = controller.db.getUnit(mqtt).toUnit()


        vmEP = Unit(name="VM.EventProcessing", type=UnitType.VirtualMachine)
        dassWS = Unit(name="EventProcessingService", type=UnitType.Process)

        vmEP.hosts(dassWS)
        eventProcessing = Unit(name="EventProcessing", type=UnitType.Composite, containedUnits=[vmEP, dassWS])


        eventProcessing.connectsTo(haproxy)


        system =  Unit(name="MYSYSTEEEEM", type=UnitType.Composite, containedUnits=[eventProcessing, mqtt])


        system = controller.addSystem(user,system )

        extracted_run_time = controller.db.getSystem(Unit(name=system.name))



        newEventProcessingservice= Unit(name="EventProcessingService", type=UnitType.Process, uuid="10.9.9.1-12345" )
        controller.addSystemUnit(user, system, newEventProcessingservice)

        extracted_run_time = controller.db.getUnit(Unit(name=newEventProcessingservice.name, type=newEventProcessingservice.type, uuid=newEventProcessingservice.uuid ), system)


        newEventProcessingVM = Unit(name="VM.EventProcessing", type=UnitType.VirtualMachine, uuid="10.9.9.1" )
        controller.addSystemUnit(user, system, newEventProcessingVM)

        newEventProcessingVM1 = Unit(name="VM.EventProcessing", type=UnitType.VirtualMachine, uuid="10.9.9.2" )
        controller.addSystemUnit(user, system, newEventProcessingVM1)

        # print(yaml.dump(system, default_flow_style=False))

        # controller.dispatchTests(user, system)
        # #
        # #
        #
        # #TODO; to implement this
        # status = controller.getLastTestsStatus(user,system)
        #
        # representation =   json.dumps(JSONConverter.systemToJSON(status), separators=(',',':'))
        # print representation


       #TODO: add timestamps on messages and somehow record maybe when what was created





        # time.sleep(10)

        controller.removeSystemUnit(user, system, newEventProcessingservice)

        # time.sleep(10)

        controller.removeSystemUnit(user, system, newEventProcessingVM)


        # time.sleep(10)

        controller.removeSystem(user, system)

        controller.removeUser(user)

        # print(yaml.dump(system, default_flow_style=False))



if __name__ == '__main__':
    unittest.main()

