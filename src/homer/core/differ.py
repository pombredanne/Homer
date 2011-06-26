#!/usr/bin/env python
#
# Copyright 2011 June Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import copy
from homer.util import Schema
"""
DiffError:
Represents any exception that gets thrown during diffing
"""
class DiffError(Exception):
    pass
    
"""
Differ:
Differ contains methods that allow you to find differences
between two container objects.
usecase:

differ = Differ()
names = ['a', 'b', 'c', 'd']
differ.insert(names)
del names[0:2]
result = differ.diff(names)
print result 
=> {'added': None, 'deleted' : ['a', 'b'], 'modified' : None}

"""
class Differ(object):
    """Base class for all views"""
    
    def __init__(self, *arguments):
        '''Inserts all the objects in @args to this differ'''
        self.copies = {}
        map(self.put, arguments)
            
    def put(self, object):
        """introduce an object to the differ"""
        if Schema.isSimple(object): 
            raise DiffError("Differ does not diff simple types")
        replica = copy.deepcopy(object)
        self.copies[id(object)] = replica
    
    def delete(self, object):
        """Removes an object from this Differ"""
        del self.copies[id(object)]
         
    def diff(self, object):
        """Calculate diff for this object."""
        if id(object) not in self.copies:
            raise DiffError("This object was not found in this Differ")
        # I select a diff function based on the Schema of the object.
        old = self.copies[id(object)] # Fetch the old copy first
        if Schema.isMapping(object):
            return diffDict(old, object) 
        elif Schema.isSequence(object):
            return diffList(old, object)   
        elif Schema.isSet(object):
            return diffSet(old, object)
        else:
            raise DiffError("Cannot diff object: %s " % object)
    
    def clear(self):
        """Remove all object from this Differ, clearing its state"""
        self.copies.clear()
          


def diffDict(old, new):
    """Diffs two dict like objects"""
    pass

def diffSet(old, new):
    """Diff two sets"""
    pass

def diffList(old, new):
    """Diff two List like objects"""
    pass
