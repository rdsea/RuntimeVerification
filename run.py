from flask import render_template


__author__ = 'TU Wien'
__copyright__ = "Copyright 2015, TU Wien, Distributed Systems Group"
__license__ = "Apache LICENSE"
__version__ = "2.0"
__maintainer__ = "Daniel Moldovan"
__email__ = "d.moldovan@dsg.tuwien.ac.at"
__status__ = "Prototype"

from api import app, config, centralIP, centralPort, profilingEnabled, databasePath
from lib.Parsers import TestDescriptionParser
from lib.Common import SimplePerformanceLogger
import os

#used for profiling in debug mode
import sys
from werkzeug.contrib.profiler import ProfilerMiddleware, MergeStream

#must test further. currently it actually hangs with tornado if one task is long running, so must be some config issue
# from tornado.wsgi import WSGIContainer
# from tornado.httpserver import HTTPServer
# from tornado.ioloop import IOLoop

@app.route('/', methods = ['GET'])
def showGeneric():
   return render_template('index.html')


if __name__=='__main__':

   default_test_description =  os.path.join(os.path.dirname(__file__), 'lib/grammars/defaultTestExecutionDescription')
   TestDescriptionParser().parseTestDescriptionFromFile(default_test_description)

   if profilingEnabled:
      #for profiling
      f = open('runtime/profiler.log', 'w')
      stream = MergeStream(sys.stdout, f)
      app.config['PROFILE'] = True
      app.wsgi_app = ProfilerMiddleware(app.wsgi_app, stream=f)
      app.debug = True

   p = SimplePerformanceLogger("./runtime/performance.csv", 'a')
   p.logPerformance(5)

   app.run(centralIP, centralPort, use_reloader=False, threaded=True)

