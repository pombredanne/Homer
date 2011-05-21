#!/usr/bin/env python
"""
Author : Iroiso . I (iroiso@live.com)
Project: Homer SDK
License: Apache License 2.0
Copyright 2011, June inc.

Description:
The absolute minimum you need to know to create a model; 

#...

@key("name")
class Shinobi(Record):
    name = String()
    rank = String(choices = ["Genin","Chounin","Jonin", "Sanin", "Kage"])
    
"""
from core import key, Record, Type
from core import commons 

version = "0.5.0"
