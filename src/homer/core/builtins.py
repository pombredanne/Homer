#!/usr/bin/env python
"""
Author : Iroiso . I (iroiso@live.com)
Project: Homer SDK
License: Apache License 2.0
Copyright 2011, June inc.

Description:
Useful builtin functions for everyday use of Homer.
"""
from homer.core.options import options

__all__ = ["tag",]
log = options.logger()

def tag(object):
    """Returns a human readable globally unique id for this object (format :http://taguri.org)"""
    if not isinstance(object, Record):
        raise ValueError("%s : must be a subclass of Record" % object)
    

