#
# Author : Iroiso . I 
# Copyright 2011
# License: Apache License 2.0
# Module: Utility functions and classes.
# File Description: Utility functions for the SDK.

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
from numbers import Number
from datetime import datetime, date, time
from collections import Sequence, Set, Mapping

"""
Schema:
The Homer SDK classifies objects into three classes which are 
similar to the W3C XMLSchema (http://www.w3.org/2001/XMLSchema)
with a few minor differences. 

Simple = DateTime, Date, Time, String, and Numbers

"""
class Schema(object):
    """Provides static methods for XMLSchema type checking"""
    simples = (Number, basestring, datetime, date, time, bool)
    sets, sequences, mappings = (Set , ), (Sequence, ), (Mapping, )
    
    @classmethod
    def isSimple(cls, object):
        """Is @object a simple type"""
        return isinstance(object, cls.simples)
        
    @classmethod
    def isComplex(cls, object):
        """Is @object a complex type ?"""
        if cls.isSimple(object) or cls.isSequence(object):
            return False
        elif cls.isMapping(object) or cls.isSet(object):
            return False
        else:
            return True
    
    @classmethod
    def isSequence(cls, object):
        """Is @object a sequence type ?"""
        if cls.isSimple(object):
            return False
        return isinstance(object, cls.sequences)
    
    @classmethod
    def isMapping(cls, object):
        """Is @object a mapping ? e.g. dict """
        return isinstance(object, cls.mappings)
    
    @classmethod
    def isSet(cls, object):
        """Is @object a set of any kind ? """
        return isinstance(object, cls.sets)
    
"""
Size:
Size provide utilities for checking size of objects in Kb, Mb and Gb.
"""    
class Size(object):
    """Provides utility functions to convert to and from bytes,kilobytes, etc."""
    
    @staticmethod
    def inBytes(object):
        """Returns the size of this python object in bytes"""
        view = memoryview(object)
        return len(view) * view.itemsize


"""
Validation:
Provides utility methods for common type validation
"""
class Validation(object):
    '''Provides utility methods for validation of common types'''
    
    @staticmethod
    def validateString(value, exception = ValueError, length = 500, emptyOk = True):
        """ Utility method for validating strings """
        if value is None and emptyOk:
            return value
        if isinstance(value, basestring):
            if not len(value) <= length:
                raise exception("Your String must not be longer than: %s" % length)
            return value   
        else:
            raise exception("Expected String, Got: %s" % value)
