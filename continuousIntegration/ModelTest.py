#!/usr/bin/env python
__author__ = 'TU Wien'
__copyright__ = "Copyright 2015, TU Wien, Distributed Systems Group"
__license__ = "Apache LICENSE"
__version__ = "2.0"
__maintainer__ = "Daniel Moldovan"
__email__ = "d.moldovan@dsg.tuwien.ac.at"
__status__ = "Prototype"

#to contain tests to ensure functionality is not broken when updating code
import json, uuid
from lib.Model import UnitType, Unit, TestDescription, Event
 
class ModelTests(object):
	def testEventModel(self):
	  u1 = Unit("UnitA","UnitA", type=UnitType.SoftwareContainer)
	  u2 = Unit("UnitA","UnitB", type=UnitType.SoftwareContainer)
	  e = Event("E2")
	  e.addTarget(u1,u2)
	  print(e)
	  assert e.__str__() == "{'id='E2, on='[{'id='UnitA, name='UnitA, type=SoftwareContainer, uuid=None}, {'id='UnitB, name='UnitA, type=SoftwareContainer, uuid=None}]}"

 

if __name__=='__main__':
	ModelTests().testEventModel()
