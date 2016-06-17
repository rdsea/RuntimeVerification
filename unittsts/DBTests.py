#!/usr/bin/env python
from lib.ModelDAO import DatabaseManagement, TestExecutionDAO, UnitTypeDAO, ParentDAO, AssociationDAO, SystemDAO

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

     def testGetPreviousTestExecutionInfoByCurrentExecutionID(self):


        # self.assertTrue(vmLB.containedUnits)
        # self.assertFalse(len(haproxy.containedUnits) > 0)

        databasePath ="/tmp/A.sql"
        db = DatabaseManagement(dbPath= databasePath)

        # create parent, append a child via association

        p = ParentDAO(name="DDD" )
        a = AssociationDAO( )
        a.child = ParentDAO(name="CHILD" )
        p.children.append(a)

        db.add(p)

        result =None
        session = None
        try:
            session = db.session_maker()
            result = session.query(ParentDAO).all()
            for r in result:
                for c in r.children:
                    print c.child.name
        except Exception as e:
           print e
        finally:
            session.close()
        print result



if __name__ == '__main__':
    unittest.main()

