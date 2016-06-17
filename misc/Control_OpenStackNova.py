#!/usr/bin/env python
import httplib, urllib, json, base64, time, os, random

__author__ = 'TU Wien'
__copyright__ = "Copyright 2015, TU Wien, Distributed Systems Group"
__license__ = "Apache LICENSE"
__version__ = "2.0"
__maintainer__ = "Daniel Moldovan"
__email__ = "d.moldovan@dsg.tuwien.ac.at"
__status__ = "Prototype"

# {"flavors": [{"id": "000000512", "name": "m1.tiny"},
#  {"id": "000000960",  "name": "m1.micro"},
#  {"id": "000001920",  "name": "m1.small"},
#  {"id": "000003750", name:  "m1.medium"},
# {"id": "000005760", "name": "m2.medium"},
#  {"id": "000007680", "name": "m1.large"},
#  {"id": "000015360", "name": "m1.xlarge"},
#  {"id": "000030720",  "name": "m1.2xlarge"},
# {"flavors": [{"id": "000000512", "links": [{"href": "http://openstack.infosys.tuwien.ac.at:8774/v2/9fee130e30784e33a7d3c9bd4f5a60ce/flavors/000000512", "rel": "self"}, {"href": "http://openstack.infosys.tuwien.ac.at:8774/9fee130e30784e33a7d3c9bd4f5a60ce/flavors/000000512", "rel": "bookmark"}], "name": "m1.tiny"}, {"id": "000000960", "links": [{"href": "http://openstack.infosys.tuwien.ac.at:8774/v2/9fee130e30784e33a7d3c9bd4f5a60ce/flavors/000000960", "rel": "self"}, {"href": "http://openstack.infosys.tuwien.ac.at:8774/9fee130e30784e33a7d3c9bd4f5a60ce/flavors/000000960", "rel": "bookmark"}], "name": "m1.micro"}, {"id": "000001920", "links": [{"href": "http://openstack.infosys.tuwien.ac.at:8774/v2/9fee130e30784e33a7d3c9bd4f5a60ce/flavors/000001920", "rel": "self"}, {"href": "http://openstack.infosys.tuwien.ac.at:8774/9fee130e30784e33a7d3c9bd4f5a60ce/flavors/000001920", "rel": "bookmark"}], "name": "m1.small"}, {"id": "000003750", "links": [{"href": "http://openstack.infosys.tuwien.ac.at:8774/v2/9fee130e30784e33a7d3c9bd4f5a60ce/flavors/000003750", "rel": "self"}, {"href": "http://openstack.infosys.tuwien.ac.at:8774/9fee130e30784e33a7d3c9bd4f5a60ce/flavors/000003750", "rel": "bookmark"}], "name": "m1.medium"}, {"id": "000005760", "links": [{"href": "http://openstack.infosys.tuwien.ac.at:8774/v2/9fee130e30784e33a7d3c9bd4f5a60ce/flavors/000005760", "rel": "self"}, {"href": "http://openstack.infosys.tuwien.ac.at:8774/9fee130e30784e33a7d3c9bd4f5a60ce/flavors/000005760", "rel": "bookmark"}], "name": "m2.medium"}, {"id": "000007680", "links": [{"href": "http://openstack.infosys.tuwien.ac.at:8774/v2/9fee130e30784e33a7d3c9bd4f5a60ce/flavors/000007680", "rel": "self"}, {"href": "http://openstack.infosys.tuwien.ac.at:8774/9fee130e30784e33a7d3c9bd4f5a60ce/flavors/000007680", "rel": "bookmark"}], "name": "m1.large"}, {"id": "000015360", "links": [{"href": "http://openstack.infosys.tuwien.ac.at:8774/v2/9fee130e30784e33a7d3c9bd4f5a60ce/flavors/000015360", "rel": "self"}, {"href": "http://openstack.infosys.tuwien.ac.at:8774/9fee130e30784e33a7d3c9bd4f5a60ce/flavors/000015360", "rel": "bookmark"}], "name": "m1.xlarge"}, {"id": "000030720", "links": [{"href": "http://openstack.infosys.tuwien.ac.at:8774/v2/9fee130e30784e33a7d3c9bd4f5a60ce/flavors/000030720", "rel": "self"}, {"href": "http://openstack.infosys.tuwien.ac.at:8774/9fee130e30784e33a7d3c9bd4f5a60ce/flavors/000030720", "rel": "bookmark"}], "name": "m1.2xlarge"}, {"id": "900000960", "links": [{"href": "http://openstack.infosys.tuwien.ac.at:8774/v2/9fee130e30784e33a7d3c9bd4f5a60ce/flavors/900000960", "rel": "self"}, {"href": "http://openstack.infosys.tuwien.ac.at:8774/9fee130e30784e33a7d3c9bd4f5a60ce/flavors/900000960", "rel": "bookmark"}], "name": "w1.tiny"}, {"id": "900001920", "links": [{"href": "http://openstack.infosys.tuwien.ac.at:8774/v2/9fee130e30784e33a7d3c9bd4f5a60ce/flavors/900001920", "rel": "self"}, {"href": "http://openstack.infosys.tuwien.ac.at:8774/9fee130e30784e33a7d3c9bd4f5a60ce/flavors/900001920", "rel": "bookmark"}], "name": "w1.small"}, {"id": "900003750", "links": [{"href": "http://openstack.infosys.tuwien.ac.at:8774/v2/9fee130e30784e33a7d3c9bd4f5a60ce/flavors/900003750", "rel": "self"}, {"href": "http://openstack.infosys.tuwien.ac.at:8774/9fee130e30784e33a7d3c9bd4f5a60ce/flavors/900003750", "rel": "bookmark"}], "name": "w1.medium"}, {"id": "900007680", "links": [{"href": "http://openstack.infosys.tuwien.ac.at:8774/v2/9fee130e30784e33a7d3c9bd4f5a60ce/flavors/900007680", "rel": "self"}, {"href": "http://openstack.infosys.tuwien.ac.at:8774/9fee130e30784e33a7d3c9bd4f5a60ce/flavors/900007680", "rel": "bookmark"}], "name": "w1.large"}, {"id": "900015360", "links": [{"href": "http://openstack.infosys.tuwien.ac.at:8774/v2/9fee130e30784e33a7d3c9bd4f5a60ce/flavors/900015360", "rel": "self"}, {"href": "http://openstack.infosys.tuwien.ac.at:8774/9fee130e30784e33a7d3c9bd4f5a60ce/flavors/900015360", "rel": "bookmark"}], "name": "w1.xlarge"}, {"id": "900015362", "links": [{"href": "http://openstack.infosys.tuwien.ac.at:8774/v2/9fee130e30784e33a7d3c9bd4f5a60ce/flavors/900015362", "rel": "self"}, {"href": "http://openstack.infosys.tuwien.ac.at:8774/9fee130e30784e33a7d3c9bd4f5a60ce/flavors/900015362", "rel": "bookmark"}], "name": "m2.large"}]}

web_server_user_data = '#!/bin/bash\n\
ARTIFACT_TAR_URL=http://10.99.0.13/iCOMOTTutorial/files/ElasticIoTCloudPlatform/artifacts/DaaS-1.0.tar.gz\n\
SERVICE_NAME=SportsAnalytics\n\
RUNTIME_VERIFICATION_SERVER_IP=128.130.172.230\n\
RUNTIME_VERIFICATION_SERVER_USER=daniel\n\
RUNTIME_VERIFICATION_SERVER_PASSWORD=daniel\n\
LOAD_BALANCER_IP=10.99.0.16\n\
sudo -S /bin/bash /home/ubuntu/prepare.sh'
#sudo -S /bin/bash /home/ubuntu/P.sh install 61 90

key = "dmoldovan"

lbIP = "10.99.0.34"

from novaclient import client

def deleteServer(nova,serverID):
 #reboot to gracefully shutdown health and then delete
 nova.servers.reboot(serverID)
 time.sleep(5)
 nova.servers.delete(serverID)
 os.system("curl -X DELETE http://" + lbIP + ":5001/service/" + str(nova.servers.get(serverID).networks['private'][0]) + "/8080")

def createServer(nova, name,image, flavor="000000512", user_data=""):
  global key
  server = nova.servers.create(nova=nova, name=name, image=image, flavor=flavor, meta=None, files=None, reservation_id=None,
                        min_count=None, max_count=None, security_groups=["default"], userdata=user_data, key_name=key)
  serverID= server.id

  #wait till server starts
  status = nova.servers.get(serverID).status
  while not status == 'ACTIVE':
    time.sleep(10)
    status = nova.servers.get(serverID).status
  return serverID

def testScaleUpDownWrongCFG(nova, scaleNr, repetitions):
   global lbIP
   goodImage = "ccd73ce9-64bb-439f-a950-17c5ed79007f"
   badCFGImage = "7e260462-5370-4fdd-9ee7-9f44b607da27"
   badProcessImage = "1e07e9ee-8b4c-4998-b271-7cccb10121fe"
   #10 minute time to boot up and install

   wrong = 0 # 0 means goodCnt, 1 means wrongCFGCnt, 2 means wrongProcessCnt
   wrongCFGCnt = 0
   wrongProcessCnt = 0
   goodCnt = 0

   for r in range(repetitions):
       list = []
       print "Repetition " + str(r)
       for s in range(scaleNr):
          if wrong == 0:
             serverID = createServer(nova = nova, image = goodImage, name="StreamAnalytics_WS", flavor="000000512", user_data=web_server_user_data)
             print "Created good ! " + str(nova.servers.get(serverID).networks['private'][0])
             list.append(serverID)
             wrong += 1
             goodCnt += 1
          elif wrong == 1:
             serverID = createServer(nova = nova,image = badCFGImage, name="StreamAnalytics_WS", flavor="000000512", user_data=web_server_user_data)
             list.append(serverID)
             print "Created bad cfg ! " + str(nova.servers.get(serverID).networks['private'][0])
             wrong += 1
             wrongCFGCnt += 1
          elif wrong == 2:
             serverID = createServer(nova = nova,image = badProcessImage, name="StreamAnalytics_WS", flavor="000000512", user_data=web_server_user_data)
             list.append(serverID)
             print "Created bad process ! " + str(nova.servers.get(serverID).networks['private'][0])
             wrong = 0
             wrongProcessCnt += 1
          time.sleep(60)

       time.sleep(600)
       for i in range(0,2):
           nova.servers.suspend(list[i])
       #wait 5 minutes and then recover
       time.sleep(120)
       for i in range(0,2):
           nova.servers.resume(list[i])
       time.sleep(120)

       for server in list:
           #ensure we remove from load balancer
           os.system("curl -X DELETE http://" + lbIP + ":5001/service/" + str(nova.servers.get(server).networks['private'][0]) + "/8080")
           deleteServer(nova=nova, serverID=server)

   print "Summary:"
   print "Wrong cfg: " + str(wrongCFGCnt)
   print "Wrong process: " + str(wrongProcessCnt)
   print "Good: " + str(goodCnt)


#one VM added every minute, and after specified limit, vms start to be destroyed
def testSuspend(nova, nodes, repetitions):
   global lbIP
   goodImage = "ccd73ce9-64bb-439f-a950-17c5ed79007f"
   badCFGImage = "7e260462-5370-4fdd-9ee7-9f44b607da27"
   badProcessImage = "1e07e9ee-8b4c-4998-b271-7cccb10121fe"
   #10 minute time to boot up and install

   list = []

   for r in range(nodes):
      serverID = createServer(nova = nova, image = goodImage, name="StreamAnalytics_WS", flavor="000000512", user_data=web_server_user_data)
      list.append(serverID)

   for r in range(repetitions):
       server = list[random.randint(0,len(list)-1)]
       print "Suspending " + str(server)
       nova.servers.suspend(server)
       time.sleep(120)
       nova.servers.resume(server)
       time.sleep(120)

   #deallocate
   for server in list:
      #ensure we remove from load balancer
      os.system("curl -X DELETE http://" + lbIP + ":5001/service/" + str(nova.servers.get(server).networks['private'][0]) + "/8080")
      deleteServer(nova=nova, serverID=server)

   print "Summary:"
   print "Suspended: " + str(repetitions)

def testScaleUpDownWrongCFGIterative(nova, repetitions, maxScaleNr):
   global lbIP
   goodImage = "ccd73ce9-64bb-439f-a950-17c5ed79007f"
   badCFGImage = "7e260462-5370-4fdd-9ee7-9f44b607da27"
   badProcessImage = "1e07e9ee-8b4c-4998-b271-7cccb10121fe"
   #10 minute time to boot up and install

   wrong = 0 # 0 means goodCnt, 1 means wrongCFGCnt, 2 means wrongProcessCnt
   wrongCFGCnt = 0
   wrongProcessCnt = 0
   goodCnt = 0
   list = []

   for r in range(maxScaleNr):
      if wrong == 0:
         serverID = createServer(nova = nova, image = goodImage, name="StreamAnalytics_WS", flavor="000000512", user_data=web_server_user_data)
         print "Created good! " + str(nova.servers.get(serverID).networks['private'][0])
         list.append(serverID)
         wrong = 1
         goodCnt += 1
      elif wrong == 1:
         serverID = createServer(nova = nova,image = badCFGImage, name="StreamAnalytics_WS", flavor="000000512", user_data=web_server_user_data)
         list.append(serverID)
         print "Created bad cfg!  " + str(nova.servers.get(serverID).networks['private'][0])
         wrong = 2
         wrongCFGCnt += 1
      elif wrong == 2:
         serverID = createServer(nova = nova,image = badProcessImage, name="StreamAnalytics_WS", flavor="000000512", user_data=web_server_user_data)
         list.append(serverID)
         print "Created bad process!  " + str(nova.servers.get(serverID).networks['private'][0])
         wrong = 0
         wrongProcessCnt += 1
      time.sleep(120) #wait to ensure we do not have overlapping test results

   #give them time to register in runtime verification platform
   time.sleep(600)
   for r in range(repetitions):
      #delete 1 (always first added to ensure it has registered in the thing)
      server = list.pop(0)
      print "Removed!  " + str(nova.servers.get(server).networks['private'][0])
      os.system("curl -X DELETE http://" + lbIP + ":5001/service/" + str(nova.servers.get(server).networks['private'][0]) + "/8080")
      deleteServer(nova=nova, serverID=server)

      #create 1
      if wrong == 0:
         serverID = createServer(nova = nova, image = goodImage, name="StreamAnalytics_WS", flavor="000000512", user_data=web_server_user_data)
         print "Created good! " + str(nova.servers.get(serverID).networks['private'][0])
         list.append(serverID)
         wrong = 1
         goodCnt += 1
      elif wrong == 1:
         serverID = createServer(nova = nova,image = badCFGImage, name="StreamAnalytics_WS", flavor="000000512", user_data=web_server_user_data)
         list.append(serverID)
         print "Created bad cfg!  " + str(nova.servers.get(serverID).networks['private'][0])
         wrong = 2
         wrongCFGCnt += 1
      elif wrong == 2:
         serverID = createServer(nova = nova,image = badProcessImage, name="StreamAnalytics_WS", flavor="000000512", user_data=web_server_user_data)
         list.append(serverID)
         print "Created bad process!  " + str(nova.servers.get(serverID).networks['private'][0])
         wrong = 0
         wrongProcessCnt += 1
      time.sleep(120) #wait to ensure we do not have overlapping test results

   for server in list:
      #ensure we remove from load balancer
      os.system("curl -X DELETE http://" + lbIP + ":5001/service/" + str(nova.servers.get(server).networks['private'][0]) + "/8080")
      print "Removed!  " + str(nova.servers.get(server).networks['private'][0])
      deleteServer(nova=nova, serverID=server)

   print "Summary:"
   print "Wrong cfg: " + str(wrongCFGCnt)
   print "Wrong process: " + str(wrongProcessCnt)
   print "Good: " + str(goodCnt)


def testScaleUpDownCFGIterative(nova, repetitions, maxScaleNr):
   global lbIP
   # goodImage = "ccd73ce9-64bb-439f-a950-17c5ed79007f"
   #this one is with NO CURL so VMs start faster
   goodImage = "06cee2d2-9a6f-4d9f-97d6-b3a80accf2c3"
   #10 minute time to boot up and install

   goodCnt = 0
   list = []

   for r in range(maxScaleNr):
     serverID = createServer(nova = nova, image = goodImage, name="StreamAnalytics_WS", flavor="000000512", user_data=web_server_user_data)
     print "Created good! " + str(nova.servers.get(serverID).networks['private'][0])
     list.append(serverID)
     goodCnt += 1
     time.sleep(120) #wait to ensure we do not have overlapping test results

   time.sleep(600)
   for r in range(repetitions):
      #delete 1 (always first added to ensure it has registered in the thing)
      server = list.pop(0)
      print "Removed!  " + str(nova.servers.get(server).networks['private'][0])
      os.system("curl -X DELETE http://" + lbIP + ":5001/service/" + str(nova.servers.get(server).networks['private'][0]) + "/8080")
      deleteServer(nova=nova, serverID=server)
      #create new server
      serverID = createServer(nova = nova, image = goodImage, name="StreamAnalytics_WS", flavor="000000512", user_data=web_server_user_data)
      print "Created good! " + str(nova.servers.get(serverID).networks['private'][0])
      list.append(serverID)
      goodCnt += 1
      time.sleep(600)

   for server in list:
      #ensure we remove from load balancer
      os.system("curl -X DELETE http://" + lbIP + ":5001/service/" + str(nova.servers.get(server).networks['private'][0]) + "/8080")
      print "Removed!  " + str(nova.servers.get(server).networks['private'][0])
      deleteServer(nova=nova, serverID=server)

   print "Summary:"
   print "Good: " + str(goodCnt)

def testScaleUpDown(nova, scaleNr, repetitions):
   global lbIP
   goodImage = "ccd73ce9-64bb-439f-a950-17c5ed79007f"
   badCFGImage = "7e260462-5370-4fdd-9ee7-9f44b607da27"
   badProcessImage = "1e07e9ee-8b4c-4998-b271-7cccb10121fe"
   #10 minute time to boot up and install

   for r in range(repetitions):
       list = []
       print "Iteration " + str(r)
       for s in range(scaleNr):
          list.append(createServer(nova = nova, name="StreamAnalytics_WS", image = goodImage, flavor="000000512", user_data=web_server_user_data))
       time.sleep(900)
       for server in list:
           os.system("curl -X DELETE http://" + lbIP + ":5001/service/" + str(nova.servers.get(server).networks['private'][0]) + "/8080")
           deleteServer(nova=nova, serverID=server)

def testScaleUp(nova, scaleNr):
   global lbIP
   goodImage = "ccd73ce9-64bb-439f-a950-17c5ed79007f"
   badCFGImage = "7e260462-5370-4fdd-9ee7-9f44b607da27"
   badProcessImage = "1e07e9ee-8b4c-4998-b271-7cccb10121fe"
   #10 minute time to boot up and install

   list = []
   for s in range(scaleNr):
      sID = createServer(nova = nova, name="StreamAnalytics_WS", image = goodImage, flavor="000000512", user_data=web_server_user_data)
      list.append(sID)
      print "Added ID " + str(sID)
      time.sleep(600)

if __name__ == '__main__':

 nova = client.Client("2.0", "dmoldovan", "Bee8sah1", "CELAR",
                     "http://openstack.infosys.tuwien.ac.at/identity/v2.0", connection_pool=True)

 # testSuspend(nova,10,30)
 # testScaleUpDownCFGIterative(nova, 10, 10)

 # testScaleUp(nova,2)
 #
 # deleteServer(nova,"705896a9-30f2-437b-8513-2c006cc9f12d")
 # deleteServer(nova,"18ab628c-93dd-441e-80be-7244c7479cb2")
 # deleteServer(nova,"6cde7295-3dc0-4475-816e-2bb2fcc45638")
 #

 # badCFGImage = "7e260462-5370-4fdd-9ee7-9f44b607da27"
 # badProcessImage = "1e07e9ee-8b4c-4998-b271-7cccb10121fe"

 #badCFGImage = "7e260462-5370-4fdd-9ee7-9f44b607da27"
 # createServer(nova= nova, name="StreamAnalytics_WS", image = goodImage,flavor="000000512", user_data=web_server_user_data)
 #
 # nova.servers.resume("de5f082f-fb7b-41c1-ba65-0dde60c1b9d7")

 goodImage = "ccd73ce9-64bb-439f-a950-17c5ed79007f"
 tstsImage = "52f91e0c-4123-42df-a1be-ee6b8ad7b257"

# web_server_user_data = '#!/bin/bash\n\
#ARTIFACT_TAR_URL=http://10.99.0.13/iCOMOTTutorial/files/ElasticIoTCloudPlatform/artifacts/DaaS-1.0.tar.gz\n\
#SERVICE_NAME=SportsAnalytics\n\
#RUNTIME_VERIFICATION_SERVER_IP=128.130.172.230\n\
#RUNTIME_VERIFICATION_SERVER_USER=daniel\n\
#RUNTIME_VERIFICATION_SERVER_PASSWORD=daniel\n\
#LOAD_BALANCER_IP=10.99.0.16\n\
#sudo -S /bin/bash /home/ubuntu/P.sh install 1 30 > /tmp/prepare.log'   #PPrepare is the one which deploys only executors

createServer(nova= nova, name="StreamAnalytics_WS",image = goodImage, flavor="000000512", user_data=web_server_user_data)
