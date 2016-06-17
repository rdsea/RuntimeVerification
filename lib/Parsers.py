#!/usr/bin/env python
from TestDescriptionParser import TestDescriptionGrammarParser
from Model import *

#parser used to process tests specified according to the test grammar

class TestDescriptionSemantics(object):

    def __init__(self):
        self.test = TestDescription()
        self.name  = "DDD'"

    def PropertiesDescriptionExpression(self, ast):
        # 'verify' ':' {id}+
        # return params
        #print("Detected PropertiesDescriptionExpression expression ")
        #print(ast)
        return ast# name, value

    def TriggeredByExpression(self, ast):
        # 'verify' ':' {id}+
        # return params
        #print("Detected TriggeredByExpression expression ")
        #print(ast)
        return ast# name, value


    def EventExpression(self, ast):
        # 'verify' ':' {id}+
        # return params
        #print("Detected EventExpression expression ")
        events = ast[0]
        eventTargets = ast[1]

        eventTrigger = EventTrigger()
        eventTrigger.addTests(self.test)
        for e in events:
            event = Event(id=e)
            for t in eventTargets:
                #currently I add just the identifier, not the whole unit
                event.addTarget(t)

            eventTrigger.addEvents(event)
        self.test.addEventTrigger(eventTrigger)
        return ast


    def PeriodExpression(self, ast):
        # 'verify' ':' {id}+
        # return params
        #print("Detected PeriodExpression expression ")
        period = ast[0]
        timeUnit = ast[1]

        periodTrigger = PeriodicTrigger(period=period, timeUnit=timeUnit)
        self.test.addPeriodTrigger(periodTrigger)
        return ast

    def ExecutionInfoExpression(self, ast):
        # 'verify' ':' {id}+
        # return params
        #print("Detected ExecutionInfoExpression expression ")
        #print(ast)
        return ast# name, value


    def name(self, ast):
        # 'verify' ':' {id}+
        # return params
        #print("Detected name expression ")
        #print("name = " + str(ast[1]))
        self.test.name = str(ast[1])
        self.name  = str(ast[1])
        return ast[1]


    def description(self, ast):
        # 'verify' ':' {id}+
        # return params
        #print("Detected description expression ")
        #print("description = " + str(ast[0]))
        self.test.description = str(ast[0])
        return ast

    def distinct(self, ast):
        print ast
        return ast


    def timeout(self, ast):
        #print("Detected timeout expression ")
        #print("timeout = " + str(ast[0]))
        self.test.timeout = int(ast[1])

    def executorExpression(self, ast):
        # 'verify' ':' {id}+
        # return params
        #print("Detected executor expression ")
        #print("executor = " + str(ast[0]))
        if ast[0]:
           executor  = 'distinct ' + str(ast[1][0]) + "." + str(ast[1][1])
        #add 'distinct ' if starts with
        else:
            executor  = str(ast[1][0]) + "." + str(ast[1][1])
        for target in ast[2]:
            self.test.addExecutor(executor, str(target[0]) + "." + str(target[1]))
        return ast# name, value

    def object(self, ast):
        # object = '{' { record }+ '}' ;
        return dict(ast[1])


class TestDescriptionParser(object):

    def parseTestDescriptionFromFile(self, filePath):
        with open(filePath) as file:
           text = file.read()
        parser = TestDescriptionGrammarParser(comments_re="#.*")
        s = TestDescriptionSemantics()
        parser.parse(text, rule_name='grammar', semantics=s)
        #print s.test.periodTriggers
        return s.test

    def parseTestDescriptionFromText(self, text):
        parser = TestDescriptionGrammarParser(comments_re="#.*")
        s = TestDescriptionSemantics()
        parser.parse(text, rule_name='grammar', semantics=s)
        return s.test


