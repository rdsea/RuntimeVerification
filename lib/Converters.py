#!/usr/bin/env python
import ast
from lib.Model import Unit, UnitType

__author__ = 'TU Wien'
__copyright__ = "Copyright 2015, TU Wien, Distributed Systems Group"
__license__ = "Apache LICENSE"
__version__ = "2.0"
__maintainer__ = "Daniel Moldovan"
__email__ = "d.moldovan@dsg.tuwien.ac.at"
__status__ = "Prototype"

#used for converting internal model representation and reports to JSON so it can be displayed
#and vice-versa, converting the JSON specifications of system structure to internal model

import json
#
class JSONConverter(object):

    #this creates a new Node for each unit hosting another unit. so it adds one node for each VM
    #used for run-time structure
    @staticmethod
    def systemToJSONAfterHosted(currentUnit):

        jsonObject = {}

        toProcess = []
        toProcessJSONs = []

        toProcess.append(currentUnit)
        toProcessJSONs.append(jsonObject)
        while toProcess:
            currentChild = toProcess.pop()
            currentChildJSON = toProcessJSONs.pop()
            childContainedUnits = []

            currentChildJSON['name'] = currentChild.name
            currentChildJSON['type'] = currentChild.type
            if currentChild.uuid:
                currentChildJSON['uuid'] = currentChild.uuid

            tests = []
            if hasattr(currentChild,'testsStatus'):
                for key, value in currentChild.testsStatus.iteritems():
                    testInfo = {}
                    testInfo['name'] = key
                    testInfo['type'] = "Test"
                    testInfo['successful'] = value.successful
                    testInfo['details'] = value.details + "; Executed by: " + value.executorUnit.uuid + ' for Target Unit: ' +  value.targetUnit.uuid
                    testInfo['timestamp'] = value.timestamp.strftime("%H:%M:%S   %d-%m-%Y")
                    childContainedUnits.append(testInfo)

            if tests:
              currentChildJSON['tests'] = tests



            for child in currentChild.containedUnits:
                #if hosted on something, create separate subtree for that host
                if not child.hostedOnUnit:
                    childJSON = JSONConverter.systemToJSON(child)
                    toProcess.append(child)
                    toProcessJSONs.append(childJSON)
                    childContainedUnits.append(childJSON)

            for child in currentChild.hostedUnits:
                childJSON = JSONConverter.systemToJSON(child)
                toProcess.append(child)
                toProcessJSONs.append(childJSON)
                childContainedUnits.append(childJSON)

            currentChildJSON['containedUnits'] = childContainedUnits

        if hasattr(currentUnit,'testSession'):
            for key, value in currentUnit.testSession.iteritems():
                testInfo = {}
                testInfo[key] = value
                jsonObject['testSession'] = testInfo

        return jsonObject


    #this creates one node per CompositeComponent. Suitable for Static Description
    @staticmethod
    def systemToJSON(currentUnit):

        jsonObject = {}

        jsonObject['name'] = currentUnit.name
        jsonObject['type'] = currentUnit.type

        if currentUnit.uuid:
            jsonObject['uuid'] = currentUnit.uuid
        if currentUnit.hostedOnUnit:
            jsonObject['hostedOn'] = currentUnit.hostedOnUnit.id

        tests = []
        if hasattr(currentUnit,'testsStatus'):
            for key, value in currentUnit.testsStatus.iteritems():
                testInfo = {}
                testInfo['name'] = key
                testInfo['type'] = "Test"
                testInfo['successful'] = value.successful
                testInfo['details'] = value.details
                testInfo['timestamp'] = value.timestamp.strftime("%H:%M:%S   %d-%m-%Y")
                tests.append(testInfo)

        if tests:
            jsonObject['tests'] = tests

        containedUnitsTSTs = []
        for child in currentUnit.containedUnits:
            containedUnitsTSTs.append(JSONConverter.systemToJSON(child))

        if containedUnitsTSTs:
            jsonObject['containedUnits'] = containedUnitsTSTs

        if hasattr(currentUnit,'testSession'):
            for key, value in currentUnit.testSession.iteritems():
                testInfo = {}
                testInfo[key] = value
                jsonObject['testSession'] = testInfo

        return jsonObject

    @staticmethod
    def testSuccessRateToJSON(currentUnit):

        jsonObject = {}

        jsonObject['name'] = currentUnit.name
        jsonObject['type'] = currentUnit.type
        jsonObject['uuid'] = currentUnit.uuid

        successRate = {}
        if hasattr(currentUnit,'testResultsAnalysis'):
            for typeOfTest, results in currentUnit.testResultsAnalysis.iteritems():
                successRate[typeOfTest] = {}
                for key, unit in results.iteritems():
                     successRate[typeOfTest][key] = {}
                     if hasattr(unit,'testResultsAnalysis'):
                         for testName, testResult in  unit.testResultsAnalysis.iteritems():
                              successRate[typeOfTest][key][testName] = testResult


        if successRate:
            jsonObject['successRate'] = successRate

        # containedUnitsTSTs = []
        # for child in currentUnit.containedUnits:
        #     containedUnitsTSTs.append(JSONConverter.testSuccessRateToJSON(child))
        #
        # if containedUnitsTSTs:
        #     jsonObject['containedUnits'] = containedUnitsTSTs

        return jsonObject


    # example of JSON
    #         {
    #   'system_name': 'name',
    #   'containedUnits': [
    #     {
    #       'name': 'ComplexUnitID',
    #       'type': 'Composite|VirtualMachine|Container|SoftwareContainer|SoftwareArtifact|Process',
    #       'containedUnits': [
    #         {
    #           'name': 'VM.Unit',
    #           'type': 'VirtualMachine'
    #         },
    #         {
    #           'name': 'Docker.Unit',
    #           'type': 'Container',
    #           'hostedOn': 'VM.Unit'
    #         },
    #         {
    #           'name': 'Process.Unit',
    #           'type': 'Process',
    #           'hostedOn': 'Docker.Unit'
    #         }
    #       ]
    #     }
    #   ]
    # }
    @staticmethod
    def convertJSONToSystem(jsonText):
        systemUnits = {} #units structured by

        json_acceptable_string = jsonText.replace("'", "\"").replace("\t", "").replace("\r", "").replace("\n", "")
        dict = json.loads(json_acceptable_string)

        system = Unit(name=dict['name'])
        JSONConverter.__convertJSONToSystem(system,dict, systemUnits)
        return system


    @staticmethod
    def __convertJSONToSystem(parent, parent_info, systemUnits):

        if 'containedUnits' in parent_info:
            for unitInfo in parent_info['containedUnits']:
                if not UnitType.isValid(unitInfo['type']):
                    raise ValueError("Invalid unit type " + unitInfo['type'])
                unit = Unit(name=unitInfo['name'], type=unitInfo['type'])
                if 'hostedOn' in unitInfo:
                    hostedOnName = unitInfo['hostedOn']
                    if hostedOnName in systemUnits.keys():
                        systemUnits[hostedOnName].hosts(unit)
                        unit.hostedOn = systemUnits[hostedOnName]
                    else:
                        raise ValueError(hostedOnName + " not found in declared system units so far")

                systemUnits[unit.name] = unit
                parent.consistsOf(unit) #adding only parent complex units in the system directly. rest are sub units of the complex units
                JSONConverter.__convertJSONToSystem(unit,unitInfo, systemUnits)
        return parent