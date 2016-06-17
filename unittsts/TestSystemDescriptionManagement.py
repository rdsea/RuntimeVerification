#!/usr/bin/env python
__author__ = 'TU Wien'
__copyright__ = "Copyright 2015, TU Wien, Distributed Systems Group"
__license__ = "Apache LICENSE"
__version__ = "2.0"
__maintainer__ = "Daniel Moldovan"
__email__ = "d.moldovan@dsg.tuwien.ac.at"
__status__ = "Prototype"

import unittest, yaml, pickle, pika
from lib.Model import Unit, UnitType, CommunicationLink, Link
from lib.Engines import SystemStructureManagementEngine, TestDispatchEngine
from lib.Utils import QueueUtil

#class used to test and debug the platform API which uses strings, from system structure processing to test strategy specification

class TestStringMethods(unittest.TestCase):

     def testAdditiion(self):
        vmLB = Unit(id="VM.LoadBalancer", type=UnitType.VirtualMachine)
        haproxy = Unit(id="HAProxy", type=UnitType.Process)
        proxyConfigService = Unit(id="ConfigService", type=UnitType.Process)
        vmLB.consistsOf(proxyConfigService)

        print yaml.dump(vmLB.containedUnits, default_flow_style=False)
        print yaml.dump(haproxy.containedUnits, default_flow_style=False)



        self.assertTrue(vmLB.containedUnits)
        self.assertFalse(len(haproxy.containedUnits) > 0)

        #vmLB.consistsOf(proxyConfigService)
        #self.assertTrue(vmLB.containedUnits)
        #self.assertFalse(haproxy.containedUnits)

     def test_add_instance(self):
        vmLB = Unit(id="VM.LoadBalancer", type=UnitType.VirtualMachine)
        haproxy = Unit(id="HAProxy", type=UnitType.Process)
        proxyConfigService = Unit(id="ConfigService", type=UnitType.Process)

        vmLB.hosts(proxyConfigService, haproxy)

        mqtt = Unit(id="LoadBalancer", type=UnitType.Composite, containedUnits=[vmLB, haproxy, proxyConfigService])

        vmEP = Unit(id="VM.EventProcessing", type=UnitType.VirtualMachine)
        dassWS = Unit(id="EventProcessingService", type=UnitType.Process)

        vmEP.hosts(dassWS)
        eventProcessing = Unit(id="EventProcessing", type=UnitType.Composite, containedUnits=[vmEP, dassWS])

        eventProcessing.connectsTo(haproxy)

        service = Unit(id="System", type=UnitType.Composite, containedUnits=[mqtt, eventProcessing])


        runt_time_service = Unit(id="System", type=UnitType.Composite, containedUnits=[]) #pickle.loads(pickle.dumps(service))

        print yaml.dump(service, default_flow_style=False) == yaml.dump(runt_time_service, default_flow_style=False)

        newEventProcessingVM = Unit(id="VM.EventProcessing", type=UnitType.VirtualMachine, uuid="10.9.9.1" )

        engine = SystemStructureManagementEngine()

        pathToNewlyAdded = engine.getPathToUnitByType(service, newEventProcessingVM, path=[])
        lastFromPath = pathToNewlyAdded.pop().id
        print "|"+lastFromPath+"|"
        print "|"+newEventProcessingVM.id+"|"
        self.assertTrue( lastFromPath == newEventProcessingVM.id )


        engine.addUnitInstance(service, runt_time_service, newEventProcessingVM)

        pathToNewlyAdded = engine.getPathToUnitByType(runt_time_service, newEventProcessingVM, path=[])
        lastFromPath = pathToNewlyAdded.pop().id
        print "|"+lastFromPath+"|"
        print "|"+newEventProcessingVM.id+"|"
        self.assertTrue( lastFromPath == newEventProcessingVM.id )

        # print yaml.dump(runt_time_service, default_flow_style=False)


     def test_add_remove(self):
        vmLB = Unit(id="VM.LoadBalancer", type=UnitType.VirtualMachine)
        haproxy = Unit(id="HAProxy", type=UnitType.Process)
        proxyConfigService = Unit(id="ConfigService", type=UnitType.Process)

        vmLB.hosts(proxyConfigService, haproxy)

        mqtt = Unit(id="LoadBalancer", type=UnitType.Composite, containedUnits=[vmLB, haproxy, proxyConfigService])

        vmEP = Unit(id="VM.EventProcessing", type=UnitType.VirtualMachine)
        dassWS = Unit(id="EventProcessingService", type=UnitType.Process)

        vmEP.hosts(dassWS)
        eventProcessing = Unit(id="EventProcessing", type=UnitType.Composite, containedUnits=[vmEP, dassWS])

        eventProcessing.connectsTo(haproxy)

        service = Unit(id="System", type=UnitType.Composite, containedUnits=[mqtt, eventProcessing])


        runt_time_service = Unit(id="System", type=UnitType.Composite, containedUnits=[]) #pickle.loads(pickle.dumps(service))

        print yaml.dump(service, default_flow_style=False) == yaml.dump(runt_time_service, default_flow_style=False)

        newEventProcessingVM = Unit(id="EventProcessingService", type=UnitType.Process, uuid="10.9.9.1-12345" )

        engine = SystemStructureManagementEngine()

        pathToNewlyAdded = engine.getPathToUnitByType(service, newEventProcessingVM, path=[])
        lastFromPath = pathToNewlyAdded.pop().id
        print "|"+lastFromPath+"|"
        print "|"+newEventProcessingVM.id+"|"
        self.assertTrue( lastFromPath == newEventProcessingVM.id )

        engine.addUnitInstance(service, runt_time_service, newEventProcessingVM)
        pathToNewlyAdded = engine.getPathToUnitByType(runt_time_service, newEventProcessingVM, path=[])
        lastFromPath = pathToNewlyAdded.pop().uuid
        print "|"+lastFromPath+"|"
        print "|"+newEventProcessingVM.uuid+"|"
        self.assertTrue( lastFromPath == newEventProcessingVM.uuid )


        engine.removeUnitInstance(runt_time_service, newEventProcessingVM)
        pathToRemoved= engine.getPathToUnitByType(runt_time_service, newEventProcessingVM, path=[])
        print "|"+str(pathToRemoved)+"|"
        self.assertFalse(pathToRemoved)

        newEventProcessingVM = Unit(id="EventProcessingService", type=UnitType.Process, uuid="10.9.9.1-1111" )
        engine.addUnitInstance(service, runt_time_service, newEventProcessingVM)
        pathToNewlyAdded = engine.getPathToUnitByType(runt_time_service, newEventProcessingVM, path=[])
        lastFromPath = pathToNewlyAdded.pop().uuid
        print "|"+lastFromPath+"|"
        print "|"+newEventProcessingVM.uuid+"|"
        self.assertTrue( lastFromPath == newEventProcessingVM.uuid )

     def test_dispatching_tests(self):
        vmLB = Unit(id="VM.LoadBalancer", type=UnitType.VirtualMachine)
        haproxy = Unit(id="HAProxy", type=UnitType.Process)
        proxyConfigService = Unit(id="ConfigService", type=UnitType.Process)

        vmLB.hosts(proxyConfigService, haproxy)

        mqtt = Unit(id="LoadBalancer", type=UnitType.Composite, containedUnits=[vmLB, haproxy, proxyConfigService])

        vmEP = Unit(id="VM.EventProcessing", type=UnitType.VirtualMachine)
        dassWS = Unit(id="EventProcessingService", type=UnitType.Process)

        vmEP.hosts(dassWS)
        eventProcessing = Unit(id="EventProcessing", type=UnitType.Composite, containedUnits=[vmEP, dassWS])

        eventProcessing.connectsTo(haproxy)

        service = Unit(id="service1", type=UnitType.Composite, containedUnits=[mqtt, eventProcessing])


        runt_time_service = Unit(id="service1", type=UnitType.Composite, containedUnits=[]) #pickle.loads(pickle.dumps(service))

        print yaml.dump(service, default_flow_style=False) == yaml.dump(runt_time_service, default_flow_style=False)

        newEventProcessingVM = Unit(id="EventProcessingService", type=UnitType.Process, uuid="10.9.9.1-12345" )

        engine = SystemStructureManagementEngine()
        engine.addUnitInstance(service, runt_time_service, newEventProcessingVM)
        pathToNewlyAdded = engine.getPathToUnitByType(runt_time_service, newEventProcessingVM, path=[])
        lastFromPath = pathToNewlyAdded.pop().uuid
        print "|"+lastFromPath+"|"
        print "|"+newEventProcessingVM.uuid+"|"
        self.assertTrue( lastFromPath == newEventProcessingVM.uuid )

        testDispatcher =  TestDispatchEngine(configPath='/home/daniel-tuwien/Documents/DSG_SVN/papers/MonitoringAndAnalyticsPlatform/python_framework/unittsts/testConfig/tests.simple.specification', queueIP='128.130.172.216')
        credentials = pika.PlainCredentials('service1', 'service1')
        testDispatcher.dispatchTests(runt_time_service, credentials)


if __name__ == '__main__':
    unittest.main()

