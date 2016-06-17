#!/usr/bin/env python
__author__ = 'TU Wien'
__copyright__ = "Copyright 2015, TU Wien, Distributed Systems Group"
__license__ = "Apache LICENSE"
__version__ = "2.0"
__maintainer__ = "Daniel Moldovan"
__email__ = "d.moldovan@dsg.tuwien.ac.at"
__status__ = "Prototype"

#This file provides a set of REST services for retrieving contextualized
#scripts to install and run the local test executor, i.e., the piece of code running locally on/near each system unit
#and executing tests

from lib.ModelDAO import SystemDAO


from flask import  Response, request
from lib.Model import UnitType, User
from api import queueIP,  controller,app,centralPublicIP, centralPort


#this returns a bash script used to run a text executor for a particular instance of a system unit
@app.route('/artifacts/ubuntu12-14-python2/remote-executor/executor/<system_id>/<unit_type>/<unit_id>/<unit_uuid>', methods = ['GET'])
def getExecutorForubuntu1214Python2(system_id,unit_type, unit_id, unit_uuid):
    auth = request.authorization
    user = User(username=auth.username, password= auth.password)
    system = SystemDAO(name=system_id)
    if not controller.db.hasAccess(user, system):
        message = "User not authorized"
        return Response(message, mimetype='text/x-python', status=403)


    path = ".//resources/artifacts/ubuntu-12-14/python2/remote-executor/testsExecutor.py"
    with open (path, "r") as myfile:
       USERNAME=user.username
       PASSWORD =user.password
       SERVICE_NAME=system_id
       UNIT_ID=unit_id

       data=myfile.read()
       data = data.replace("HEALTH_CENTRAL_QUEUE_IP='localhost'", "HEALTH_CENTRAL_QUEUE_IP='" + str(queueIP)+"'")
       data = data.replace("USERNAME=''", "USERNAME='" + str(USERNAME)+"'")
       data = data.replace("PASSWORD=''", "PASSWORD='" + str(PASSWORD)+"'")
       data = data.replace("SYSTEM_NAME=''", "SYSTEM_NAME='" + str(SERVICE_NAME)+"'")
       data = data.replace("UNIT_UUID=''", "UNIT_UUID='" + str(unit_uuid)+"'")
       data = data.replace("UNIT_ID=''", "UNIT_ID='" + str(UNIT_ID)+"'")
       data = data.replace("UNIT_TYPE=''", "UNIT_TYPE='" + str(unit_type)+"'")
    return Response(data, mimetype='text/x-python')

#returns the common library having utils used by the executor and central platform
#important such that the executor can execute tests
@app.route('/artifacts/ubuntu12-14-python2/remote-executor/common/common', methods = ['GET'])
def getCommon():
    global ip
    path = "./lib/Common.py"
    with open (path, "r") as myfile:
       data=myfile.read()
    return Response(data, mimetype='text/x-python')


#returns the common library having model classes used by the executor and central platform
#important such that the executor can execute tests
@app.route('/artifacts/ubuntu12-14-python2/remote-executor/common/model', methods = ['GET'])
def getModel():
    global ip
    path = "./lib/Model.py"
    with open (path, "r") as myfile:
       data=myfile.read()
    return Response(data, mimetype='text/x-python')


@app.route('/artifacts/ubuntu12-14-python2/remote-executor/installer/<system_id>/<unit_type>/<unit_ID>', methods = ['GET'])
def getInstallerForubuntu1214Python2(system_id, unit_ID, unit_type):

    auth = request.authorization
    user = User(username=auth.username, password= auth.password)
    system = SystemDAO(name=system_id)
    if not controller.db.hasAccess(user, system):
        message = "User not authorized"
        return Response(message, mimetype='text/x-python', status=403)

    path = ".//resources/artifacts/ubuntu-12-14/python2/remote-executor/install.sh"
    with open (path, "r") as myfile:
       data=myfile.read()
       data = data.replace("HEALTH_CENTRAL_IP='localhost'", "HEALTH_CENTRAL_IP='" + str(centralPublicIP)+"'")
       data = data.replace("HEALTH_CENTRAL_PORT=*", "HEALTH_CENTRAL_PORT='" + str(centralPort)+"'")
       data = data.replace("USERNAME=''", "USERNAME='" + str(auth.username)+"'")
       data = data.replace("PASSWORD=''", "PASSWORD='" + str(auth.password)+"'")
       data = data.replace("UNIT_ID=''", "UNIT_ID='" + str(unit_ID)+"'")
       data = data.replace("UNIT_TYPE=''", "UNIT_TYPE='" + str(unit_type)+"'")
       data = data.replace("SYSTEM_NAME=''", "SYSTEM_NAME='" + str(system_id)+"'")
    return Response(data, mimetype='text/x-python')


@app.route('/artifacts/ubuntu12-14-python2/local-executor/installer/<system_id>/<unit_type>/<unit_ID>', methods = ['GET'])
def getInstallerForubuntu1214Python2Local(system_id, unit_ID, unit_type):

    auth = request.authorization
    user = User(username=auth.username, password= auth.password)
    system = SystemDAO(name=system_id)
    if not controller.db.hasAccess(user, system):
        message = "User not authorized"
        return Response(message, mimetype='text/x-python', status=403)

    path = ".//resources/artifacts/ubuntu-12-14/python2/local-executor/install.sh"
    with open (path, "r") as myfile:
       data=myfile.read()
       data = data.replace("HEALTH_CENTRAL_IP='localhost'", "HEALTH_CENTRAL_IP='" + str(centralPublicIP)+"'")
       data = data.replace("HEALTH_CENTRAL_PORT=*", "HEALTH_CENTRAL_PORT='" + str(centralPort)+"'")
       data = data.replace("USERNAME=''", "USERNAME='" + str(auth.username)+"'")
       data = data.replace("PASSWORD=''", "PASSWORD='" + str(auth.password)+"'")
       data = data.replace("UNIT_ID=''", "UNIT_ID='" + str(unit_ID)+"'")
       data = data.replace("UNIT_TYPE=''", "UNIT_TYPE='" + str(unit_type)+"'")
       data = data.replace("SYSTEM_NAME=''", "SYSTEM_NAME='" + str(system_id)+"'")
    return Response(data, mimetype='text/x-python')

@app.route('/artifacts/ubuntu12-14-python2/local-executor/installernoapt/<system_id>/<unit_type>/<unit_ID>', methods = ['GET'])
def getInstallerForubuntu1214Python2LocalNoApt(system_id, unit_ID, unit_type):

    auth = request.authorization
    user = User(username=auth.username, password= auth.password)
    system = SystemDAO(name=system_id)
    if not controller.db.hasAccess(user, system):
        message = "User not authorized"
        return Response(message, mimetype='text/x-python', status=403)

    path = ".//resources/artifacts/ubuntu-12-14/python2/local-executor/install_no_apt.sh"
    with open (path, "r") as myfile:
       data=myfile.read()
       data = data.replace("HEALTH_CENTRAL_IP='localhost'", "HEALTH_CENTRAL_IP='" + str(centralPublicIP)+"'")
       data = data.replace("HEALTH_CENTRAL_PORT=*", "HEALTH_CENTRAL_PORT='" + str(centralPort)+"'")
       data = data.replace("USERNAME=''", "USERNAME='" + str(auth.username)+"'")
       data = data.replace("PASSWORD=''", "PASSWORD='" + str(auth.password)+"'")
       data = data.replace("UNIT_ID=''", "UNIT_ID='" + str(unit_ID)+"'")
       data = data.replace("UNIT_TYPE=''", "UNIT_TYPE='" + str(unit_type)+"'")
       data = data.replace("SYSTEM_NAME=''", "SYSTEM_NAME='" + str(system_id)+"'")
    return Response(data, mimetype='text/x-python')




#gets the UUID sender. the UUID sender is a component which sends the UUID (e.g.m instance ID) of the system unit
#for which it executes tests
@app.route('/artifacts/ubuntu12-14-python2/remote-executor/uuidsender', methods = ['GET'])
def getUUIDSenderForubuntu1214Python2():

    path = ".//resources/artifacts/ubuntu-12-14/python2/remote-executor/sendUUID.py"
    with open (path, "r") as myfile:
       data=myfile.read()
    return Response(data, mimetype='text/x-python')


@app.route('/artifacts/ubuntu12-14-python2/remote-executor/service', methods = ['GET'])
def getServiceForubuntu1214Python2():
    path = ".//resources/artifacts/ubuntu-12-14/python2/remote-executor/executor-service"
    with open (path, "r") as myfile:
       data=myfile.read()
    return Response(data, mimetype='text/x-python')

#used to download custom files
@app.route('/artifacts/<partialPath>', methods = ['GET'])
def getGenericFile(partialPath):
    path = ".//resources/artifacts/"+ partialPath
    path = path.replace("%","/")
    with open (path, "r") as myfile:
       data=myfile.read()
    return Response(data, mimetype='text/plain')

