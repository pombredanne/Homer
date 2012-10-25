#!/usr/bin/env python
#
# Author Iroiso,
# Copyright 2012 June
#

import os
import sys
import shutil
from datetime import datetime

import time
from fabric.api import local, run, cd

CASSANDRA_HOME = "~/Hub/apache-cassandra-1.0.6"
sys.path.extend(["./src", "./lib"])

def header(message, char= "="):
    '''formats messages within this script in a particular way'''
    width = 70
    padding = (width - len(message))/2
    print(char * padding + message + char * padding)

def clean():
    '''Remove all build related stuff,'''
    header("clean")
    currentDir = os.getcwd()
    print("Current Working Directory: %s" % currentDir)
    print("Deleting build directories")
    build = os.path.join(currentDir, "build")
    dist = os.path.join(currentDir, "dist")

    for path in (dist, build):
        if os.path.exists(path):
            print("Removing build directory: %s" % path)
            shutil.rmtree(path)

    print("Removing all .pyc and temporary files")
    for root, dirs, files in os.walk(currentDir):
        for f in files:
            if f.endswith('.pyc') or f.endswith("~"):
                path = os.path.join(root,f)
                print("Removing: %s" % path)
                os.unlink(path)
        for d in dirs:
            if d.endswith('.egg-info'):
                path = os.path.join(root, d)
                print("Removing Directory: %s" % path)
                shutil.rmtree(path)
    header('')

def test(arguments=""):
    '''Runs unittests for the project'''
    header("Launching Apache Cassandra")
    home = os.path.expanduser("~/.pid")
    command = CASSANDRA_HOME + "/bin/cassandra -p %s" % home
    result = local(command)
    if result.failed:
        print("Couldn't Launch Cassandra, Quitting...")
        sys.exit(1)
    
    time.sleep(5.0) # Wait 5s for the Cassandra Server to fully launch
    header("Launched Cassandra Successfully")
    header("Running Unit tests")
    if not arguments:
        local("./test.py")
    else:
        local("./test.py %s" % arguments)
    pid = open(home).read()
    header("Trying to close Cassandra...")
    result = local("kill %s" % pid)
    if not result.failed:
        header("Successfully closed Cassandra.")
    clean()
    header("Finished testing the project successfully")
    
