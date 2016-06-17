#!/usr/bin/env python
from functools import wraps
import json
import pickle
from lib.Converters import JSONConverter

from lib.ModelDAO import SystemDAO

__author__ = 'TU Wien'
__copyright__ = "Copyright 2015, TU Wien, Distributed Systems Group"
__license__ = "Apache LICENSE"
__version__ = "2.0"
__maintainer__ = "Daniel Moldovan"
__email__ = "d.moldovan@dsg.tuwien.ac.at"
__status__ = "Prototype"

# has all REST services invoked from Javascript from the Web User Interface

from flask import request, Response, session, flash, redirect, url_for, render_template
from api import *


def authenticate_user():
    user = None
    if session.get('logged_in'):
        user = controller.db.getUserByID(session['userID'])
    else:
        auth = request.authorization
        if auth:
            user = User(username=auth.username, password=auth.password)
        else:
            return None
    return user


@app.route('/users/<username>/<password>', methods=['PUT'])
def addUser(username, password):
    userToAdd = User(username=username, password=password)
    if controller.db.existsUsername(userToAdd):
        message = "Username allready exists. Please choose another username and retry "
        return Response(message, mimetype='text/x-python', status=412)
    else:
        controller.addUser(userToAdd)
        message = "User successfully added"
        return Response(message, mimetype='text/x-python', status=200)


@app.route('/users', methods=['DELETE'])
def deleteUser():
    auth = request.authorization
    user = User(username=auth.username, password=auth.password)
    if not controller.db.existsUsername(user):
        message = "Username does not exists"
        return Response(message, mimetype='text/x-python', status=412)
    else:
        controller.removeUser(user)
        message = "User successfully removed"
        return Response(message, mimetype='text/x-python', status=200)


@app.route('/systems', methods=['PUT'])
def addSystem():
    systemDescription = pickle.loads(request.data)

    user = authenticate_user()
    if not user:
        return Response("Not logged in", mimetype='text/json', status=403)

    controller.addSystem(user, systemDescription)
    message = "System successfully added"
    return Response(message, mimetype='text/x-python', status=200)


#
# @app.route('/systems/<system_name>/tests/configuration/simple', methods=['PUT'])
# def addSimpleTestsConfig(system_name):
#     testContent = pickle.loads(request.data)
#     user = authenticate_user()
#     if not user :
#         return Response("Not logged in", mimetype='text/json', status=403)
#     controller.addSimpleTestsConfig(user, controller.db.getSystem(SystemDAO(name=system_name)), testContent)
#     message ="Tests config updated"
#     return Response(message, mimetype='text/x-python', status=200)
#
# @app.route('/systems/<system_name>/tests/configuration/complex', methods=['PUT'])
# def addComplexTestsConfig(system_name):
#     testContent = pickle.loads(request.data)
#     user = authenticate_user()
#     if not user:
#         return Response("Not logged in", mimetype='text/json', status=403)
#     controller.addComplexTestsConfig(user, controller.db.getSystem(SystemDAO(name=system_name)), testContent)
#     message ="Tests config updated"
#     return Response(message, mimetype='text/x-python', status=200)


@app.route('/status/<system_name>/<test_name>/description', methods=['GET'])
def getTestDescription(system_name, test_name):
    user = authenticate_user()
    message = controller.getTestDescription(user, controller.db.getSystem(SystemDAO(name=system_name))
                                            , controller.db.getTest(TestDAO(name=test_name)))
    return Response(message, mimetype='text/json', status=200)


@app.route('/systems/<system_name>', methods=['DELETE'])
def deleteSystem(system_name):
    user = authenticate_user()
    if not user:
        return Response("Not logged in", mimetype='text/json', status=403)
    controller.removeSystem(user, SystemDAO(name=system_name))
    message = "System successfully removed"
    return Response(message, mimetype='text/x-python', status=200)


@app.route('/systems/<system_name>/structure/runtime', methods=['GET'])
def getLatestCompleteSystemStructure(system_name):
    user = authenticate_user()
    if not user:
        return Response("Not logged in", mimetype='text/json', status=403)
    systemDescription = controller.getLatestCompleteSystemStructure(user, SystemDAO(name=system_name))
    message = json.dumps(JSONConverter.systemToJSONAfterHosted(systemDescription))
    return Response(message, mimetype='text/json', status=200)

@app.route('/systems/<system_name>/events/csv', methods=['GET'])
def getSystemEventHistoryAsCSV(system_name):
    user = authenticate_user()
    if not user:
        return Response("Not logged in", mimetype='text/json', status=403)
    events = controller.getAllEventsForSystem(user, SystemDAO(name=system_name))
    message = ""
    for event in events:
        message = message + str(event.id) +  "!" + str(event.eventType) +  "!" + str(event.details) + "!" + str(event.timestamp) + "\n"
    response =  Response(message, mimetype='text/csv', status=200)
    response.headers._list.append(('Content-Disposition','attachment;filename="' + system_name +'_events.csv"'))
    response.content_disposition = 'attachment; filename="' + system_name +'_events.csv"'
    return response\

@app.route('/systems/<system_name>/tests/config', methods=['GET'])
def downloadTestConfig(system_name):
    user = authenticate_user()
    if not user:
        return Response("Not logged in", mimetype='text/json', status=403)
    contents = controller.getTestsForSystemAsPickledObject(user, SystemDAO(name=system_name))
    response =  Response(contents, mimetype='text/other', status=200)
    response.headers._list.append(('Content-Disposition','attachment;filename="' + system_name +'_tests_config.cfg"'))
    response.content_disposition = 'attachment; filename="' + system_name +'_tests_config.cfg"'
    return response

@app.route('/systems/<system_name>/events', methods=['DELETE'])
def deleteSystemEventHistoryAsCSV(system_name):
    user = authenticate_user()
    if not user:
        return Response("Not logged in", mimetype='text/json', status=403)
    controller.deleteEventsForSystem(user, SystemDAO(name=system_name))
    message = "Events successfully removed"
    return Response(message, mimetype='text/x-python', status=200)

@app.route('/systems/<system_name>/structure/static', methods=['GET'])
def getStaticSystemStructure(system_name):
    user = authenticate_user()
    if not user:
        return Response("Not logged in", mimetype='text/json', status=403)
    systemDescription = controller.getStaticSystemStructure(user, SystemDAO(name=system_name))
    message = json.dumps(JSONConverter.systemToJSON(systemDescription))
    return Response(message, mimetype='text/json', status=200)


@app.route('/status/<system_name>/tests/last/all', methods=['GET'])
def getLastSystemTestsStatus(system_name):
    user = authenticate_user()
    systemDescription = controller.getLastTestsStatus(user, SystemDAO(name=system_name))

    message = json.dumps(JSONConverter.systemToJSONAfterHosted(systemDescription))
    return Response(message, mimetype='text/json', status=200)


@app.route('/status/<system_name>/tests/session/last', methods=['GET'])
def getLastSystemTestSessionStatus(system_name):
    user = authenticate_user()
    if not user:
        return Response("Not logged in", mimetype='text/json', status=403)

    systemDescription = controller.getLastTestsStatus(user, SystemDAO(name=system_name))
    message = json.dumps(JSONConverter.systemToJSONAfterHosted(systemDescription))
    return Response(message, mimetype='text/json', status=200)


@app.route('/status/<system_name>/tests/analysis/rate', methods=['GET'])
def getSuccessRateAnalysis(system_name):
    user = authenticate_user()
    if not user:
        return Response("Not logged in", mimetype='text/json', status=403)
    systemDescription = controller.getSuccessRateAnalysis(user, SystemDAO(name=system_name))
    message = json.dumps(JSONConverter.testSuccessRateToJSON(systemDescription))
    return Response(message, mimetype='text/json', status=200)


@app.route('/status/<system_name>/tests/analysis/rate/type', methods=['GET'])
def getSuccessRateAnalysisByType(system_name):
    user = authenticate_user()
    if not user:
        return Response("Not logged in", mimetype='text/json', status=403)
    systemDescription = controller.getSuccessRateAnalysisByType(user, SystemDAO(name=system_name))
    message = json.dumps(JSONConverter.testSuccessRateToJSON(systemDescription))
    return Response(message, mimetype='text/json', status=200)


@app.route('/status/<system_name>/tests/analysis/rate/uuid', methods=['GET'])
def getSuccessRateAnalysisByUUID(system_name):
    user = authenticate_user()
    if not user:
        return Response("Not logged in", mimetype='text/json', status=403)
    systemDescription = controller.getSuccessRateAnalysisByUUID(user, SystemDAO(name=system_name))
    message = json.dumps(JSONConverter.testSuccessRateToJSON(systemDescription))
    return Response(message, mimetype='text/json', status=200)


@app.route('/status/<system_name>/tests/analysis/rate/name', methods=['GET'])
def getSuccessRateAnalysisByName(system_name):
    user = authenticate_user()
    if not user:
        return Response("Not logged in", mimetype='text/json', status=403)
    systemDescription = controller.getSuccessRateAnalysisByName(user, SystemDAO(name=system_name))
    message = json.dumps(JSONConverter.testSuccessRateToJSON(systemDescription))
    return Response(message, mimetype='text/json', status=200)


@app.route('/systems/<system_name>/tests/dispatch/all', methods=['POST'])
def dispatchTests(system_name):
    systemDescription = SystemDAO(name=system_name)
    reason = request.data
    user = authenticate_user()
    if not user:
        return Response("Not logged in", mimetype='text/json', status=403)
    controller.dispatchTests(user, systemDescription, reason)
    message = "Tests dispatched"
    return Response(message, mimetype='text/x-python', status=200)
