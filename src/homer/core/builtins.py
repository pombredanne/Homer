#!/usr/bin/env python
"""
Author : Iroiso . I (iroiso@live.com)
Project: Homer SDK
License: Apache License 2.0
Copyright 2011, June inc.

Description:
builtin functions from the core
"""
from homer.core.records import Record
from homer.core.events import Observer
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

"""
DiffObserver:
DiffObserver tracks attributes on Records that have been added, modified, or 
deleted and you can look up this attributes with the added(), modified(), deleted() 
builtins; An instance of this class (RecordObserver) is added to R

Implementation Notes:
DiffObserver uses a dictionary internally (table) to store the modified, 
deleted and added attributes of objects: They are stored internally as

{id : {'added': set(), 'modified' : set(), 'deleted' : set() }}

where id is the unique id of the record.
"""
class DiffObserver(Observer):
    '''Tracks records monitoring attributes that have be modified, added or deleted'''
    table = {}
    
    def modified(self, id):
        """Returns the 'key:'modified' on  @id"""
        if id in self.table:
            return self.table[id]['modified']
        raise KeyError("Invalid key:{id}" % id)
        
    def deleted(self, id):
        """Returns the key:'deleted' on  @id"""
        if id in self.table:
            return self.table[id]['deleted']
        raise KeyError("Invalid key:{id}" % id)
   
    def added(self, id):
        """Returns the key:'originals' on @id"""
        if id in self.table:
            return self.table[id]['added']
        raise KeyError("Invalid key:{id}" % id)
    
    def clear(self, id):
        """Clears information that has been stored up for @id"""
        log.warning("Removing id: %s from tracking table; This is undoable")
        del self.table[id]
        
    def observe(self, event):
        """Checks the Event and It source and log it into the table"""
        source = event.source
        key = id(source)
        
        if key not in self.table:
            log.info("Putting a new Record with id: %s in table" % key)
            self.table[key] = {'added': set(), 'modified' : set(), 'deleted': set() }
        
        log.info("About to start processing events") 
        if event.id == "ADD":
            log.info("Processing ADD Event")
            addSet = self.table[key]['added']
            addSet.add(event.name)
            delSet = self.table[key]['deleted']
            if event.name in delSet:
                delSet.remove(event.name) 
        elif event.id == "SET":
            log.info("Processing SET Event")
            addSet = self.table[key]['added'] 
            if event.name in addSet:  
                log.info('This attribute has just recently been added skipping it')
                return
            log.info('Adding this attribute to the modification table')
            modSet = self.table[key]['modified']
            modSet.add(event.name)
            log.info('Removing attribute from deletion table')
            delSet = self.table[key]['deleted']
            if event.name in delSet:
                delSet.remove(event.name)
        elif event.id == "DEL":
            log.info("Processing DEL Event")
            log.info("Adding attribute from deletion table")
            delSet = self.table[key]['deleted']
            delSet.add(event.name)
            log.info('Removing this attribute from the addition and modification table')
            modSet = self.table[key]['modified']
            addSet = self.table[key]['added']
            if event.name in modSet:
                modSet.remove(event.name)
            if event.name in addSet:
                addSet.remove(event.name)      
        else:
            log.info("Ignoring Event: %s" % event.id)
          


""" #Singletons """
RecordObserver = DiffObserver()


