#!/usr/bin/env python
"""
Author : Iroiso . I (iroiso@live.com)
Project: Homer SDK
License: Apache License 2.0
Copyright 2011, June inc.

Description:
The absolute minimum you need to know to use Cassandra
and Redis 

#...

@key("name")
class Shinobi(Model):
    name = String(indexed = True)
    rank = String(choices = ["Genin","Chounin","Jonin",])
    
"""
from .core import *
from .backend import *

version = "1.1.0"
