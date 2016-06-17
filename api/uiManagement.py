#!/usr/bin/env python
from functools import wraps
import json
import pickle
from lib.Converters import JSONConverter
from lib.Model import NotificationMailInfo, UnitType

from lib.ModelDAO import SystemDAO
from lib.Utils import MailUtil

__author__ = 'TU Wien'
__copyright__ = "Copyright 2015, TU Wien, Distributed Systems Group"
__license__ = "Apache LICENSE"
__version__ = "2.0"
__maintainer__ = "Daniel Moldovan"
__email__ = "d.moldovan@dsg.tuwien.ac.at"
__status__ = "Prototype"
#handles actions required by the User Interface
#has all backing methods, so no REST services, but process and have access to data submitted by FORMS

from flask import request, Response, session, flash, redirect, url_for, render_template
from api import *
from lib import Utils

def authenticate_user():
    user = None
    if session.get('logged_in'):
        user = controller.db.getUserByID(session['userID'])
    else:
        auth = request.authorization
        if auth:
           user = User(username=auth.username, password= auth.password)
           user = controller.db.getUser(user)
           if not user:
               return None
        else:
           return None
    return user


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['action'] == 'Login':
            user = User(username=request.form['username'], password= request.form['password'])
            if controller.db.existsUser(user):
                session['logged_in'] = True
                session['username'] = user.username
                session['userID'] = controller.db.getUser(user).id
                flash('Welcome: ' + user.username)
                return render_template('index.html', error=error)
            else:
                flash('User and password combination not found')
        elif request.form['action'] == 'Register':
            controller.addUser(User(username=request.form['username'], password=request.form['password']))
            flash('You are registered. Please log in')
        elif request.form['action'] == 'MailMeMyPassword':
            controller.emailPassword(username=request.form['username'])
        else:
            return render_template('index.html', error="Unknown error encountered.please try again")

    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('userID', None)
    flash('You were logged out')
    return render_template('login.html')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/documentation')
def showHelp():
    return render_template('help.html')


@app.route('/system_management', methods=['POST'])
def addSystemFromJSONDescription():

    user = authenticate_user()
    if not user :
        return render_template('login.html')

    template = ""

    if request.form['action'] == 'Add':
        systemJSON = request.form['systemDescription']
        system = JSONConverter.convertJSONToSystem(systemJSON.strip())
        if not controller.db.existsSystem(system):
            controller.addSystem(user,system)
        else:
           flash('System name allready exists. Choose another')
    elif request.form['action'] == 'LoadTemplate':
           template = controller.loadSystemDescriptionTemplate(user)
    elif request.form['action'] == 'Clear':
           template = ""

    systems = []
    user = controller.db.getUser(user)
    for system in user.managedSystems:
       systems.append(system)

    return render_template('systemmanagement.html', systems=systems, template=template)


#manage systems
@app.route('/system_management#delete', methods=['POST'])
def deleteSystemFromUI():

    user = authenticate_user()
    if not user :
        return render_template('login.html')

    system = controller.db.getSystem(SystemDAO(name=request.form['system_id']))
    controller.removeSystem(user, system)
    systems = []
    user = controller.db.getUser(user)
    for system in user.managedSystems:
        systems.append(system)
    return render_template('systemmanagement.html', systems=systems)

@app.route('/system_management')
def manageSystem():
    user = authenticate_user()
    if not user :
        return render_template('login.html')
    systems = []
    user = controller.db.getUser(user)
    for system in user.managedSystems:
        systems.append(system)
    return render_template('systemmanagement.html', systems=systems)


@app.route('/system_config_management', methods=['POST'])
def manageSystemsConfigurations():
    user = authenticate_user()
    if not user :
        return render_template('login.html')
    if request.method == 'POST':
        if request.form['action'] == 'Delete':
            system = controller.db.getSystem(SystemDAO(name=request.form['system_id']))
            controller.removeSystem(user, system)
            systems = []
            user = controller.db.getUser(user)
            for system in user.managedSystems:
                systems.append(system)
            return render_template('systemmanagement.html', systems=systems)
        elif request.form['action'] == 'DispatchTests':
            system = controller.db.getSystem(SystemDAO(name=request.form['system_id']))
            controller.dispatchTests(user, system, request.form['reason'])
            systems = []
            user = controller.db.getUser(user)
            for system in user.managedSystems:
                systems.append(system)
            return render_template('systemmanagement.html', systems=systems)
        elif request.form['action'] == 'ManageTests':
            system = controller.db.getSystem(SystemDAO(name=request.form['system_id']))
            # system.complexTestConfig= controller.getComplexTestsConfiguration(user,system)
            # system.simpleTestConfig= controller.getSimpleTestsConfiguration(user,system)
            system.genericTests = controller.getGenericTests(user)
            system.customTests = controller.getUserTests(user)
            return render_template('testsmanagement.html', system=system)

        elif request.form['action'] == 'ViewEvents':
            systemID =request.form['system_id']
            system = controller.db.getSystem(SystemDAO( name=systemID))
            events = controller.getAllEventsForSystem(user, system)
            system.events = events
            return render_template('eventsManagement.html', system=system)

        elif request.form['action'] == 'DownloadInstaller':
            systemID =request.form['system_id']
            system = controller.db.getSystem(SystemDAO( name=systemID))
            units = controller.getStaticSystemStructure(user, SystemDAO( name=systemID)).toList()
            units.pop(0) #to unit list and remove self, as self is complex system

            urls = {}

            #traverse shit of system

            for unit in units:
                if unit.type == UnitType.Composite:
                    continue
                command = "wget -q --user=" + user.username + " --password=" + user.password+ " --auth-no-challenge http://"+ centralPublicIP\
                  +":5001/artifacts/ubuntu12-14-python2/remote-executor/installer/"+systemID+"/" + unit.type + "/" + unit.id +" -O ./install.sh"
                # url = "http://"+ centralIP\
                #   +":5001/artifacts/ubuntu12-14-python2/remote-executor/installer/"+systemID+"/" + unit.type + "/" + unit.id
                urls[unit.id] = command

            system.installers = urls

            return render_template('installerManagement.html', system=system)


#manage tests and testing strategies

@app.route('/tests_management', methods=['POST'])
def manageTestsConfigurations():
    user = authenticate_user()
    if not user :
        return render_template('login.html')
    if request.form['action'] == 'ManageTests':
        system = controller.db.getSystem(SystemDAO(name=request.form['system_id']))
        # system.complexTestConfig= controller.getComplexTestsConfiguration(user,system)
        # system.simpleTestConfig= controller.getSimpleTestsConfiguration(user,system)
        system.genericTests = controller.getGenericTests(user)
        system.customTests = controller.getUserTests(user)
        return render_template('testsmanagement.html', system=system)

@app.route('/systems', methods=['POST'])
def updateTestDescription():
    user =  authenticate_user()
    if not user:
        return render_template('login.html')

    system = controller.db.getSystem(SystemDAO(name=request.form['system_id']))
    system.genericTests = controller.getGenericTests(user)
    system.customTests = controller.getUserTests(user)

    if request.method == 'POST':
        testName = request.form['testName']

        if request.form['action'] == 'Add/Update':
           testDescriptionContent = request.form['testDescriptionContent']
           #check and remove for SUDO
           try:
             controller.addTestDescription(user,system
                                            , controller.db.getTest(TestDAO(name=testName))
                                           , testDescriptionContent)
           except Exception as e:
                   return render_template('testsmanagement.html', system=system, error=e)
        elif request.form['action'] == 'Reset':
           controller.deleteTestDescription(user,system
                                            , controller.db.getTest(TestDAO(name=testName)))

    return render_template('testsmanagement.html', system=system)


@app.route('/system_config_management#tests', methods=['POST'])
def updateTest():
    user =  authenticate_user()
    if not user :
        return render_template('login.html')
    system = controller.db.getSystem(SystemDAO(name=request.form['system_id']))

    if request.method == 'POST':
        if request.form['action'] == 'Add/Update':
           testName = request.form['testName']
           testContentNoPadded  = request.form['testContent']

           testContent = ""

           #add for each line in content one space on left, to ensure compatibility with
           #test dispatch mechanism which embeds tests in local python method
           lines = testContentNoPadded.splitlines()

           #if first line is padded do not pad (was allready padded), else pad
           if not lines[0].startswith(" "):
             for line in testContentNoPadded.splitlines():
                 testContent = testContent + " " + line + "\n"
           else:
             testContent = testContentNoPadded

           test = TestDAO(name = testName, content = testContent)
           if controller.db.existsTest(test):
               test = controller.db.getTest(test)
               test.content = testContent
               if test in user.managedTests:
                  controller.db.update(test)
           else:
               controller.db.add(test)
               user.managedTests.append(test)
               controller.db.update(user)
        if request.form['action'] == 'Delete':
           testName = request.form['testName']
           test = TestDAO(name = testName)
           if controller.db.existsTest(test):
               test = controller.db.getTest(test)
               #remove test description
               controller.deleteTestDescription(user,system, test)
               user.managedTests.remove(test)
               controller.db.update(user)
               controller.db.remove(test)

    system.genericTests = controller.getGenericTests(user)
    system.customTests = controller.getUserTests(user)

    return render_template('testsmanagement.html', system=system)



#manage account settings

@app.route('/account_settings')
def manageAccount():
    user = authenticate_user()
    if not user :
        return render_template('login.html')
    dao = controller.db.getUser(user)
    userDetails = {}
    userDetails['mailUsername'] =  dao.mailUsername
    userDetails['mailPassword'] =  dao.mailPassword
    userDetails['mailAddress'] =  dao.mailAddress
    userDetails['smtpServerName'] =  dao.smtpServerName
    userDetails['smtpServerPort'] =  dao.smtpServerPort

    return render_template('accountManagement.html', userDetails = userDetails)

@app.route('/update_settings', methods=['POST'])
def updateAccountSettings():

    user = authenticate_user()
    if not user:
        return render_template('login.html')

    if request.method == 'POST':
        if request.form['action'] == 'Save':
            dao = controller.db.getUser(user)
            # TODO: add change password / delete account feature
            # if request.form['password']:
            #     dao.password =  request.form['password']
            if 'mailNotifications' in request.form and request.form['mailNotifications']:
                dao.mailUsername = request.form['mailUsername']
                dao.mailPassword = request.form['mailPassword']
                dao.mailAddress = request.form['mailAddress']
                dao.smtpServerName = request.form['smtpServerName']
                dao.smtpServerPort = int(request.form['smtpServerPort'])
                subject = "[Run-Time Verification Platform] Mail address confirmation"
                content = "Updated mail address details. " + "\n Health management platform started on http://" + centralPublicIP + ":" + str(centralPort)
                MailUtil.sendMail(dao.mailAddress, dao.mailUsername, dao.mailPassword,dao.smtpServerName, dao.smtpServerPort, subject, content)
            else:
                #reset everything
                dao.mailUsername = ""
                dao.mailPassword = ""
                dao.mailAddress = ""
                dao.smtpServerName = ""
                dao.smtpServerPort = 0
            controller.db.update(dao)

            return render_template('index.html')
        if request.form['action'] == 'Cancel':
            return render_template('index.html')
        else:
            flash("Unknown error encountered.please try again")


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] == 'cfg'

@app.route('/tests/config/upload', methods=['POST'])
def uploadTestsConfig():
    if request.method == 'POST':
        file = request.files['tests_config_file']
        if file and allowed_file(file.filename):
            testDescriptions = pickle.load(file.stream)
            for testDescription in testDescriptions:
                if controller.db.getTestDescriptionByID(testDescription.id):
                    controller.db.update(testDescription)
                else:
                    controller.db.add(testDescription)
            print testDescriptions
            flash("Not implemented")
            return redirect(url_for('manageTestsConfigurations'))