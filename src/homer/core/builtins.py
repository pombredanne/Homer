#!/usr/bin/env python
"""
Author : Iroiso . I (iroiso@live.com)
Project: Homer SDK
License: Apache License 2.0
Copyright 2011, June inc.

Description:
builtin functions from the core
"""
from homer.core.options import options

__all__ = ["key", "tag", "deleted", "modified", "added", "view",]
log = options.logger()

"""
added:

"""
def added(object):
    """Yields all the new attributes added to this Record """
    if not isinstance(object, Record):
        raise ValueError("%s : must be a subclass of Record" % object)
        
"""
modified:

"""
def modified(object):
    """Yields all the attributes that have been modified on this Record """
    if not isinstance(object, Record):
        raise ValueError("%s : must be a subclass of Record" % object)
        
"""
deleted:

"""
def deleted(object):
    """Yields all the attributes that have been deleted on this Record """
    if not isinstance(object, Record):
        raise ValueError("%s : must be a subclass of Record" % object)

"""
tag:

"""
def tag(object):
    """Returns a human readable unique id for this object (format :http://taguri.org)"""
    if not isinstance(object, Record):
        raise ValueError("%s : must be a subclass of Record" % object)
    
"""
view:

"""
def view(object):
    """Yields all the attributes that exists on this object; """
    pass

