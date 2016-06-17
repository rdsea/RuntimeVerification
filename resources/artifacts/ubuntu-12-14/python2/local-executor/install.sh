#!/bin/bash
HEALTH_CENTRAL_IP='localhost'
HEALTH_CENTRAL_IP_PORT=5001
SYSTEM_NAME=''

UNIT_ID=''

#  Unit type any of the folllwing:
#    VirtualMachine = "OperatingSystem"
#    AppContainer = "ApplicationContainer"
#    SoftwareContainer = "SoftwareContainer"
#    SoftwarePlatform = "SoftwarePlatform"
#    SoftwareArtifact = "SoftwareArtifact"
#    Process = "Process"
#    Composite = "Composite"
UNIT_TYPE=''

parentUUID=''
UNIT_ID=''
UNIT_UUID=''
USERNAME=''
PASSWORD=''

SYSTEM_NAME=''

sudo apt-get update -y
sudo apt-get install curl -y
sudo apt-get install screen -y
sudo -S apt-get install python-pip git-core -y
sudo -S apt-get install python-virtualenv -y
sudo -S pip install Flask
sudo -S pip install pika
#for monitoring memory/cpu usage
sudo -S apt-get install python-dev -y
sudo -S pip install psutil

#to add functionality for allowing custom properties injection
#CUSTOM_PROPERTIES_FILE=/etc/tests.simple.specification

CURRENT_DIR=$(pwd)

wget -q GET http://$HEALTH_CENTRAL_IP:$HEALTH_CENTRAL_IP_PORT/artifacts/ubuntu12-14-python2/remote-executor/uuidsender -O ./sendUUID.py
wget -q --user=$USERNAME --password=$PASSWORD --auth-no-challenge http://$HEALTH_CENTRAL_IP:$HEALTH_CENTRAL_IP_PORT/artifacts/ubuntu12-14-python2/remote-executor/executor/$SYSTEM_NAME/$UNIT_TYPE/$UNIT_ID/$UNIT_UUID -O ./testsExecutor.py
wget http://$HEALTH_CENTRAL_IP:$HEALTH_CENTRAL_IP_PORT/artifacts/ubuntu12-14-python2/remote-executor/service -O ./executor-service_$UNIT_UUID

mkdir ./lib

touch ./lib/__init__.py

wget -q --user=$USERNAME --password=$PASSWORD --auth-no-challenge http://$HEALTH_CENTRAL_IP:$HEALTH_CENTRAL_IP_PORT/artifacts/ubuntu12-14-python2/remote-executor/common/common -O ./lib/Common.py
wget -q --user=$USERNAME --password=$PASSWORD --auth-no-challenge http://$HEALTH_CENTRAL_IP:$HEALTH_CENTRAL_IP_PORT/artifacts/ubuntu12-14-python2/remote-executor/common/model -O ./lib/Model.py

#screen -S testsExecutor_$UNIT_UUID -d -m python ./testsExecutor.py

eval "sed -i 's#DAEMONDIR=.*#DAEMONDIR=$CURRENT_DIR#' $CURRENT_DIR/executor-service_$UNIT_UUID"
eval "sed -i 's#NAME=.*#NAME=$UNIT_UUID-remote-executor-pid#' $CURRENT_DIR/executor-service_$UNIT_UUID"
eval "sed -i 's#daas-pid.pid.*#$UNIT_UUID-remote-executor.pid#' $CURRENT_DIR/executor-service_$UNIT_UUID"

sudo -S cp ./executor-service_$UNIT_UUID /etc/init.d/executor-service_$UNIT_UUID
sudo -S chmod +x /etc/init.d/executor-service_$UNIT_UUID
sudo -S update-rc.d executor-service_$UNIT_UUID defaults

sudo service executor-service_$UNIT_UUID start
