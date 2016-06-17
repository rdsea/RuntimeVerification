#!/bin/sh

echo "deb http://www.rabbitmq.com/debian/ testing main" | sudo -S tee -a /etc/apt/sources.list

sudo -S wget https://www.rabbitmq.com/rabbitmq-signing-key-public.asc
sudo -S apt-key add rabbitmq-signing-key-public.asc
sudo -S apt-get update
sudo -S apt-get install rabbitmq-server -y

if [ ! -z $(sudo rabbitmqctl status | grep running_applications) ]; 
 then
    echo "RabbitMQ running"| sudo -S tee -a /tmp/rabbitmqinstall.log;
 else
    echo "Problems installing rabbitmq $(sudo rabbitmqctl status | grep running_applications)" | sudo -S tee -a /tmp/rabbitmqinstall.log;
fi
sudo -S rabbitmq-plugins enable rabbitmq_management

sudo -S rabbitmqctl add_user mela mela
sudo -S rabbitmqctl set_user_tags mela administrator
sudo -S rabbitmqctl set_permissions mela  ".*" ".*" ".*"
 
sudo -S rabbitmqctl delete_user guest