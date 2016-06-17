#!/bin/bash
PID=$(cat /tmp/health-management.pid)
for p in $PID
  do
    sudo kill -9 $p
  done

rm /tmp/health-management.pid
