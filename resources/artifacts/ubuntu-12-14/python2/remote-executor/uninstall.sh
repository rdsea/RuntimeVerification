#!/bin/bash

export $(cat /etc/init.d/executor-service | grep -o "DAEMONDIR=[.*]")

sudo -S service executor-service stop
sudo -S rm /etc/init.d/executor-service
sudo -S update-rc.d executor-service remove  
rm $DAEMONDIR/executor-service
rm $DAEMONDIR/remoteExecutor.py
rm $DAEMONDIR/install.sh
rm $DAEMONDIR/uninstall.sh
rm -rf $DAEMONDIR/lib


