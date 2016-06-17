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

case "$UNIT_TYPE" in
    # Docker or similar should get parent IP from a static IP defined on the VM hosting the container
    "Container")
	     parentUUID=$(curl -X GET http://192.0.0.1:5000/uuid)
	     UNIT_UUID=$parentUUID-$(ifconfig eth0 | grep -o 'inet addr:[0-9.]*' | grep -o [0-9.]*)
         eval "sed -i 's#parentUUID=.*#parentUUID=$parentUUID#' $CURRENT_DIR/sendUUID.py"
#        removed screen as I start it from executor service
#         screen -S uuidSender_$UNIT_UUID -d -m python ./sendUUID.py $UNIT_UUID
        ;;
    #for VM/OR types, parent IP is nobody, and ID is IP
    "VirtualMachine")
        #create fixed IP interface for docker(Container) types to use to get the parent ID
        sudo -S ifconfig lo:0 192.0.0.1
        UNIT_UUID=$(ifconfig eth0 | grep -o 'inet addr:[0-9.]*' | grep -o [0-9.]*)
#        removed screen as I start it from executor service
#        screen -S uuidSender_$UNIT_UUID -d -m python ./sendUUID.py $UNIT_UUID
        ;;
    "Gateway")
        #create fixed IP interface for docker(Container) types to use to get the parent ID
        sudo -S ifconfig lo:0 192.0.0.1
        UNIT_UUID=$(ifconfig eth0 | grep -o 'inet addr:[0-9.]*' | grep -o [0-9.]*)
#        removed screen as I start it from executor service
#        screen -S uuidSender_$UNIT_UUID -d -m python ./sendUUID.py $UNIT_UUID
        ;;
    #for else, such as processes, parent ID is the IP of the localhost, retrieved from the localhost sendUUID
    *)
         #give the possibility for someone to manually inject parent UUID here
         if [[ -z $parentUUID ]] #if not defined, get IP
            then
                parentUUID=$(curl -X GET http://localhost:5000/uuid)
            fi
         UNIT_UUID=$parentUUID-$UNIT_UUID
        ;; 
esac

#eval "sed -i 's#UNIT_UUID=.*#UNIT_UUID=$parentUUID-$UNIT_INSTANCE_ID#' $CURRENT_DIR/remoteExecutor.py"

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
