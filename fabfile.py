#!/usr/bin/env python
#
# Author Iroiso,
# Copyright 2012 June
#

import os
import sys
import shutil
from datetime import datetime
from gates.core import Application, run

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
