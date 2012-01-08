#!/usr/bin/env python
#
# A simple benchmark tornado's HTTP stack along with Homer to see if they fit.

import cql

from homer.core import *
from homer.core.models import Schema
from homer.backend import *
from homer.options import *

from tornado.ioloop import IOLoop
from tornado.options import define, options, parse_command_line
from tornado.web import RequestHandler, Application

import uuid
import random
import signal
import subprocess

# choose a random port to avoid colliding with TIME_WAIT sockets left over
# from previous runs.
define("min_port", type=int, default=8000)
define("max_port", type=int, default=9000)

# Increasing --n without --keepalive will eventually run into problems
# due to TIME_WAIT sockets
define("n", type=int, default=5000)
define("c", type=int, default=100)
define("keepalive", type=bool, default=True)
define("quiet", type=bool, default=False)

# Repeat the entire benchmark this many times (on different ports)
# This gives JITs time to warm up, etc.  Pypy needs 3-5 runs at
# --n=15000 for its JIT to reach full effectiveness
define("num_runs", type=int, default=5)

# Homer Simpson's data classes here.
@key("name")
class Profile(Model):
    name = String(indexed = True)
    message = String('')
    
class RootHandler(RequestHandler):
    '''Root handler for the ab test'''
    def get(self):
        '''Do a write everytime a GET is received'''
        p = Profile(name=str(uuid.uuid4()), message="Hello world")
        p.save()
        # print "Writing :%s to cassandra" % p.name
        self.write("Hello, world")

    def _log(self):
        pass

def handle_sigchld(sig, frame):
    IOLoop.instance().add_callback(IOLoop.instance().stop)

def main():
    parse_command_line()
    for i in xrange(options.num_runs):
        run()

def run():
    # Homer Simpson's configuration here
    db = Simpson
    # Do Datastore configuration, setup stuff like namespaces and etcetera
    print "Bringing in Homer Simpson's Baggage..."
    c = DataStoreOptions(servers=["localhost:9160",], username="", password="")
    c.size = 1000 #Just for now.
    namespace = Namespace(name= "Test", cassandra= c)
    namespaces.add(namespace)
    namespaces.default = "Test"
    
    app = Application([("/", RootHandler)])
    port = random.randrange(options.min_port, options.max_port)
    app.listen(port, address='127.0.0.1')
    signal.signal(signal.SIGCHLD, handle_sigchld)
    args = ["ab"]
    args.extend(["-n", str(options.n)])
    args.extend(["-c", str(options.c)])
    if options.keepalive:
        args.append("-k")
    if options.quiet:
        # just stops the progress messages printed to stderr
        args.append("-q")
    args.append("http://127.0.0.1:%d/" % port)
    subprocess.Popen(args)
    IOLoop.instance().start()
    IOLoop.instance().close()
    del IOLoop._instance
    assert not IOLoop.initialized()
   
    print "Clearing Homer Simpson's Baggage..."
    print "Finally Stored: %s Profiles in the Datastore" % (Profile.count(),)
    
if __name__ == '__main__':
    main()
