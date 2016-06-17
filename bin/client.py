#!/usr/bin/env python
import base64
import httplib

__author__ = 'TU Wien'
__copyright__ = "Copyright 2015, TU Wien, Distributed Systems Group"
__license__ = "Apache LICENSE"
__version__ = "2.0"
__maintainer__ = "Daniel Moldovan"
__email__ = "d.moldovan@dsg.tuwien.ac.at"
__status__ = "Prototype"

import pickle
from lib.ModelDAO import *
from lib.Model import *


def addSystem(ip, port, user, system):
    connection = httplib.HTTPConnection(ip + ":" + str(port))
    body_content = pickle.dumps(system)
    auth = base64.encodestring('%s:%s' % (user.username, user.password)).replace('\n', '')
    headers = {
        'Content-Type': 'application/octet-stream',
        'Authorization': 'Basic %s' % auth
    }
    connection.request('PUT', "/systems", body=body_content, headers=headers, )
    result = connection.getresponse()
    print result.read()


def adClient(ip, port, user ):
    connection = httplib.HTTPConnection(ip + ":" + str(port))
    headers = {    }
    connection.request('PUT', "/users/" + user.username + "/" + user.password,   headers=headers, )
    result = connection.getresponse()
    print result.read()


# if __name__ == '__main__':
#     vmLB = Unit(name="VM.LoadBalancer", type=UnitType.VirtualMachine)
#     haproxy = Unit(name="HAProxy", type=UnitType.Process)
#     proxyConfigService = Unit(name="ConfigService", type=UnitType.Process)
#     vmLB.hosts(proxyConfigService, haproxy)
#
#     mqtt = Unit(name="LoadBalancer", type=UnitType.Composite, containedUnits=[vmLB, haproxy, proxyConfigService])
#
#     vmEP = Unit(name="VM.EventProcessing", type=UnitType.VirtualMachine)
#     dassWS = Unit(name="EventProcessingService", type=UnitType.Process)
#
#     vmEP.hosts(dassWS)
#     eventProcessing = Unit(name="EventProcessing", type=UnitType.Composite, containedUnits=[vmEP, dassWS])
#
#     eventProcessing.connectsTo(haproxy)
#
#     system = Unit(name="TestSystem", type=UnitType.Composite, containedUnits=[eventProcessing, mqtt])
#
#     myuser = User(username="daniel",password="daniel")
#     adClient("128.131.172.45", 5001, myuser)
#     addSystem("128.131.172.45", 5001, myuser, system)

if __name__ == '__main__':
    vmLB = Unit(name="VM.LoadBalancer", type=UnitType.VirtualMachine)
    haproxy = Unit(name="HAProxy", type=UnitType.Process)
    proxyConfigService = Unit(name="ConfigService", type=UnitType.Process)
    vmLB.hosts(proxyConfigService, haproxy)

    mqtt = Unit(name="LoadBalancer", type=UnitType.Composite, containedUnits=[vmLB, haproxy, proxyConfigService])

    vmEP = Unit(name="VM.EventProcessing", type=UnitType.VirtualMachine)
    dassWS = Unit(name="EventProcessingService", type=UnitType.Process)
    docker = Unit(name="Docker.EventProcessing", type=UnitType.Container)

    vmEP.hosts(docker)
    docker.hosts(dassWS)
    eventProcessing = Unit(name="EventProcessing", type=UnitType.Composite, containedUnits=[vmEP,docker, dassWS])

    eventProcessing.connectsTo(haproxy)

    system = Unit(name="TestSystem", type=UnitType.Composite, containedUnits=[eventProcessing, mqtt])

    a = UnitType.__dict__

    myuser = User(username="daniel",password="daniel")
    adClient("128.131.172.45", 5001, myuser)
    addSystem("128.131.172.45", 5001, myuser, system)
