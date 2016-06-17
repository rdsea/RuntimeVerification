#!/usr/bin/env python
__author__ = 'TU Wien'
__copyright__ = "Copyright 2015, TU Wien, Distributed Systems Group"
__license__ = "Apache LICENSE"
__version__ = "2.0"
__maintainer__ = "Daniel Moldovan"
__email__ = "d.moldovan@dsg.tuwien.ac.at"
__status__ = "Prototype"

import sys
from lib.Utils import QueueUtil
import threading
import time


if __name__ == '__main__':
    args = sys.argv
    threads = []
    util = QueueUtil()
    for i in range (1,10):
      time.sleep(1)
      t = threading.Thread(target=util.removeQueue, args=["128.130.172.191", "SportsAnalytics", "10.99.0."  +str(i)+ "-Results", "daniel","daniel"])
      t.start()
      threads.append(t)

      t = threading.Thread(target=util.removeQueue, args=["128.130.172.191", "SportsAnalytics", "10.99.0."  +str(i)+ "-Tests", "daniel","daniel"])
      t.start()
      threads.append(t)

      t = threading.Thread(target=util.removeQueue, args=["128.130.172.191", "SportsAnalytics", "10.99.0."  +str(i)+ "-Tomcat-Results", "daniel","daniel"])
      t.start()
      threads.append(t)

      t = threading.Thread(target=util.removeQueue, args=["128.130.172.191", "SportsAnalytics", "10.99.0."  +str(i)+ "-Tomcat-Tests", "daniel","daniel"])
      t.start()
      threads.append(t)

      t = threading.Thread(target=util.removeQueue, args=["128.130.172.191", "SportsAnalytics", "10.99.0."  +str(i)+ "-Tomcat-StreamingAnalytics-Results", "daniel","daniel"])
      t.start()
      threads.append(t)

      t = threading.Thread(target=util.removeQueue, args=["128.130.172.191", "SportsAnalytics", "10.99.0."  +str(i)+ "-Tomcat-StreamingAnalytics-Tests", "daniel","daniel"])
      t.start()
      threads.append(t)

    for t in threads:
        t.join()