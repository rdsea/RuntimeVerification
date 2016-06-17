#!/usr/bin/env python
__author__ = 'TU Wien'
__copyright__ = "Copyright 2015, TU Wien, Distributed Systems Group"
__license__ = "Apache LICENSE"
__version__ = "2.0"
__maintainer__ = "Daniel Moldovan"
__email__ = "d.moldovan@dsg.tuwien.ac.at"
__status__ = "Prototype"

from flask import Response, Flask
import commands, sys

parentUUID=""

app = Flask("UUIDSender")
 
@app.route('/uuid', methods = ['GET'])
def getUUID():
    global unitID
    return Response(parentUUID + unitID, mimetype='text/plain')
 
if __name__ == '__main__':

    args = sys.argv
    ip = commands.getoutput("ifconfig eth0 | grep -o 'inet addr:[0-9.]*' | grep -o [0-9.]*")

    if len(args) > 1:
        unitID = args[1]
    else:
        unitID = ip

    app.debug = True
    app.run('0.0.0.0', 5000)
 
