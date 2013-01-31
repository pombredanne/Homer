#!/usr/bin/env python

"""
Author : Iroiso,
Project: Homer SDK
License: Apache License 2.0
Copyright 2012, June inc.

Description:
Common data types for the homer project, these classes
are designed to 'look like' builtin classes, e.g.

mobile = phone('+1', '(248) 123-7654')
assert mobile.country == "+1"
assert mobile.number == '2481237654'
"""
import sys
import json
import re
import codecs
import hashlib

__all__ = ["phone", "blob", "TypedMap", "TypedSet", "TypedList",]


class phone(object):
    '''An immutable Phone number in international format'''
    pattern = re.compile("^\+(?:[0-9] ?){6,14}[0-9]$")

    def __init__(self, number):
        '''Simply pass in the number as one block. '''
        assert isinstance(number, str), "Type Error, Please use strings instead"
        number = number.strip()
        if not re.search(self.pattern, number):
            raise ValueError("Invalid international phone number")
        self.__number = number
    
    @property
    def number(self):
        '''A readonly property that returns the number part of this phone number'''
        return self.__number
    
    def __eq__(self, other):
        '''Equality tests'''
        assert isinstance(other, phone),"%s must be a phone type" % other
        return self.number == other.number
         
    def __str__(self):
        '''String representation of an international phone number'''
        return self.number
    
    def __repr__(self):
        '''Returns a phone object as a tuple'''
        return "phone('%s')" % (self.number)


class blob(object):
    '''A opaque binary object with a content-type and description'''
    def __init__(self, content="", mimetype="application/text", description="", **keywords):
        '''Basic constructor for a blob'''
        self.metadata = {}
        encode = codecs.getencoder("utf-8")
        self.content = encode(content)[0]
        self.mimetype = mimetype
        self.description = description
        self.metadata.update(keywords)
        self.checksum = self.__md5(content)
    
    def __md5(self, content):
        '''Calculates the md5 hash of the content and returns it as a string'''
        m = hashlib.md5()
        m.update(content)
        return m.hexdigest()
            
    def __eq__(self, other):
        '''Compares the checksums if @other is a blob, else it compares content directly''' 
        if isinstance(other, blob):
            return self.checksum == other.checksum
        else: 
            return self.content == other
    
    def __sizeof__(self):
        '''Returns the size of this blob, this returns the size of the content string'''
        return sys.getsizeof(self.content)
        
    def __repr__(self):
        '''Returns a JSON representation of the contents of this blob'''
        dump = dict()
        dump['metadata'] = self.metadata
        dump['content'] = self.content
        dump['mimetype'] = self.mimetype
        dump['description'] = self.description
        dump['checksum'] = self.checksum
        return json.dumps(dump)
        
    def __str__(self): 
        '''Returns a human readable string representation of the blob'''
        return "Blob: [mimetype:%s, checksum:%s, description:%s]" % \
            (self.mimetype, self.checksum, self.description)


"""
Description:
Typed Collections that are useful for the collection descriptors. Typed
Collections can be used to store collections of Simple Types or Models
in Cassandra; Typed Collections have one special feature however, if they
are used to store Models; they store the Model keys instead of pickling the
Models themselves.
"""
from homer.backend import store
from homer.core.models import Converter, Reference, Model, KeyHolder
from collections import MutableMapping, MutableSet, MutableSequence, Counter

blank = Converter #An alias

"""
TypedMap:
A mutable hash table that does type validation before
storing items, It behaves like a dict normally.

e.g.
from homer.core.commons import String, Integer

var = TypedMap(String, Integer)
var['Hello'] = 1

or

var = TypedMap() #This does not do any data validation at all.
var[0] = "hello"

alternate configuration for construction.
var = TypedList(String, Integer, data={"Hello", 1})
assert var["Hello"] == 1
"""
class TypedMap(MutableMapping):
    '''A map that does validation of keys and values'''

    def __init__(self, T=blank, V=blank, data={}):
        '''Initialization routine for TypeMap'''
        assert issubclass(T, (Converter, Model)), "T must be a Converter"
        assert issubclass(V, (Converter, Model)), "V must be a Converter"
        # Convert Models to KeyHolders Beneath.
        if issubclass(T, Model):
            self.T = KeyHolder(T)
        else:
            self.T = T()
        if issubclass(V, Model):
            self.V = KeyHolder(V)
        else:
            self.V = V()
        
        # Create the underlying data for the Map.
        self.__data__ = {}
        for k, v in data.iteritems():
            self[k] = v
    
    def __setitem__(self, key, value):
        '''Validate and possibly transform key, value before storage'''
        key, value = self.T(key), self.V(value)
        self.__data__[key] = value
        
    def __getitem__(self, key):
        '''Validate and possibly transform key before retreival'''
        key = self.T(key)
        value = self.__data__[key]
        if isinstance(self.V, KeyHolder) and self.V.cls is not None:
            return store.read(value)
        return value

    def __delitem__(self, key):
        '''Validate and possibly transform key before deletion'''
        key = self.T(key)
        del self.__data__[key]

    def __iter__(self):
        '''Returns a iterable over the data set'''
        # If we have KeyHolders with Models in them, read the Models and return them.
        for k in self.__data__:
            if isinstance(self.T, KeyHolder) and self.T.cls is not None:
                yield store.read(k)
            else:
                yield k
    
    def __str__(self):
        '''String representation of an object'''
        return str(self.__data__)

    def __eq__(self, other):
        return self.__data__ == other

    def __len__(self):
        '''Returns the number of the keys in this map'''
        return len(self.__data__)


"""
TypedList:
A mutable sequence type that does data validation before storing
data. By default it behaves like an ordinary list.
If the data type (the `cls` attribute) of a TypedList is a Model, 
the TypedList stores the key of the Model instead of pickling the Model itself.

e.g.
from homer.core.commons import String

var = TypedList(String)
var.append("Hello")

or

var = TypedList() #This does not do any data validation at all.
var[0] = "hello"

alternate configuration for constructors.
var = TypedList(String, data="Hello")
assert var[0] == 'H'
"""
class TypedList(MutableSequence):
    '''A List that validates content before addition or removal'''
    def __init__(self, T=blank, data=[]):
        '''Initializes a TypedList'''
        assert issubclass(T, (Converter, Model)), "T must be a Converter"

        if issubclass(T, Model):
            self.T = KeyHolder(T)
        else:
            self.T = T()
        self.__data__ = []
        for k in data:
            self.append(k)

    def insert(self, index, value):
        '''Validate and possibly transform value before insertion'''
        value = self.T(value)
        self.__data__.insert(index, value)

    def __setitem__(self, index, value):
        '''Validate and possibly transform value before adding it to @self'''
        value = self.T(value)
        self.__data__[index] = value

    def __getitem__(self, index):
        '''Read the item stored at @index, possibly transforming it before returning it'''
        value = self.__data__[index]
        if isinstance(self.T, KeyHolder) and self.T.cls is not None:
            return store.read(value)
        else:
            return value

    def __contains__(self, item):
        value = self.T(item)
        return value in self.__data__

    def __delitem__(self, index):
        del self.__data__[index]

    def __len__(self):
        return len(self.__data__)

    def __iter__(self):
        '''Returns a iterable over the data set'''
        for k in self.__data__:
            if isinstance(self.T, KeyHolder) and self.T.cls is not None:
                yield store.read(k)
            else:
                yield k

    def __eq__(self, other):
        return self.__data__ == other

"""
TypedSet:
A mutable set that does type validation before adding items
to the set. By default it behaves like an ordinary set.
"""
class TypedSet(MutableSet):
    '''A Set that validates content before addition'''
    def __init__(self, T=blank, data=set()):
        assert isinstance(T, type), "T must be a class"
        assert issubclass(T, (Converter, Model)), "T must be a Converter or a Model"
        # Converter Models to KeyHolders
        if issubclass(T, Model):
            self.T = KeyHolder(T)
        else:
            self.T = T()
        self.__data__ = set()
        for k in data:
            self.add(k)

    def add(self, value):
        '''Validate and possibly transform value before appending it to @self'''
        value = self.T(value)
        self.__data__.add(value)

    def discard(self, value):
        '''Validate and possibly transform value before appending it to @self'''
        value = self.T(value)
        self.__data__.discard(value)

    def __contains__(self, item):
        value = self.T(item)
        return value in self.__data__

    def _from_iterable(self, iterable):
        '''Overridden to make this behave more like a Set'''
        return TypedSet(self.T, iterable)

    def __iter__(self):
        '''Returns a iterable over the data set'''
        for k in self.__data__:
            if isinstance(self.T, KeyHolder) and self.T.cls is not None:
                yield store.read(k)
            else:
                yield k

    def __eq__(self, other):
        return self.__data__ == other

    def __len__(self):
        return len(self.__data__)

