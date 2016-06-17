#!/bin/sh
mkdir ./runtime
sudo -S apt-get update
sudo -S apt-get install python-pip git-core -y
sudo -S pip install pika==0.9.14
sudo -S apt-get install python-virtualenv -y
sudo -S pip install Flask
sudo -S pip install pyyaml
#sudo -S apt-get install libevent-dev -y
#sudo apt-get install python-all-dev -y 
#sudo -S pip install greenlet
#sudo -S pip install gevent
#sudo -S apt-get install python-gevent -y
#sudo -S apt-get install python-socketio
sudo -S pip install flask-login

#for serving flask
#http://www.tornadoweb.org/en/stable/
sudo -S pip install tornado

#only for profiling
#https://github.com/fengsp/flask-profile
sudo -S pip install Flask-Profile

#ORM mapper for python
#http://www.pythoncentral.io/sqlalchemy-expression-language-advanced/
sudo -S pip install SQLAlchemy


#for backing up in memory DB to file and reverse
#https://pypi.python.org/pypi/sqlitebck
#maybe I need here also python-dev
#sudo apt-get install libsqlite3-dev #needed to compile sqlitebck
#sudo -S pip install sqlitebck

#for openStack tests
#sudo -S pip install python-novaclient

#used for test grammar parsing
sudo -S pip install grako

#for performance metric (mem/cpu) from system
sudo -S pip install psutil