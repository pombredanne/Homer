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
import hashlib

__all__ = ["phone", "blob", "TypedMap", "TypedSet", "TypedList", "TypedCounter",]


class phone(object):
    '''A Phone number in international format'''
    def __init__(self, country, number):
        '''country == 'country code' number == 'local number' '''
        assert isinstance(country, str) and isinstance(number, str), "Type Error, Please use strings instead"
        country, number = country.strip(), number.strip()
        if country[0] != '+':
            raise ValueError("Country code must begin with a '+'")
        # Strip out all non numbers, and remove the first zeros
        value = [c for c in number if c.isdigit()]
        if value[0] == '0':
            value = value[1:]    
        self.__number = ''.join(value)
        self.__country = country
    
    @property
    def country(self):
        '''A readonly property that returns the country of this phone number'''
        return self.__country
    
    @property
    def number(self):
        '''A readonly property that returns the number part of this phone number'''
        return self.__number
    
    def __eq__(self, other):
        '''Equality tests'''
        assert isinstance(other, phone),"%s must be a phone type" % other
        return self.__number == other.__number and self.__country == other.__country
         
    def __str__(self):
        '''String representation of an international phone number'''
        return self.country + self.number
    
    def __repr__(self):
        '''Returns a phone object as a tuple'''
        return "phone('%s', '%s')" % (self.country, self.number)


class blob(object):
    '''A opaque binary object with a content-type and description'''
    def __init__(self, content="", mimetype="application/text", description="", **keywords):
        '''Basic constructor for a blob'''
        self.metadata = {}
        self.content = content
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
        dump = {"metadata": self.metadata, "content": self.content,\
           "mimetype": self.mimetype, "description": self.description, 
                        "checksum": self.checksum}
        return json.dumps(dump)
        
    def __str__(self): 
        '''Returns a human readable string representation of the blob'''
        return "Blob: [mimetype:%s, checksum:%s, description:%s]" % \
            (self.mimetype, self.checksum, self.description)

"""
Description:
Typed Collections that are useful for the collection descriptors.
"""
from .models import Converter, Reference, Model
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
        assert isinstance(T, type) and isinstance(V, type), "T and V must be classes"
        assert issubclass(T, (Converter, Model)), "T must be a Converter or a Model"
        assert issubclass(V, (Converter, Model)), "V must be a Converter or a Model"
        # Convert Models to a References underneath.
        if issubclass(T, Model):
            self.T = Reference(T)
        else: 
            self.T = T()     
        if issubclass(V, Model):
            self.V = Reference(V)
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
        return self.__data__[key]

    def __delitem__(self, key):
        '''Validate and possibly transform key before deletion'''
        key = self.T(key)
        del self.__data__[key]

    def __iter__(self):
        '''Returns a iterable over the data set'''
        return self.__data__.__iter__()
    
    def __eq__(self, other):
        return self.__data__ == other

    def __len__(self):
        '''Returns the number of the keys in this map'''
        return len(self.__data__)


"""
TypedList:
A mutable sequence type that does data validation before storing
data. by default it behave like an ordinary list..

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
        assert isinstance(T, type), "T must be a class"
        assert issubclass(T, (Converter, Model)), "T must be a Converter or a Model"
        # Converter Model classes to References
        if issubclass(T, Model):
            self.T = Reference(T)
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
        return self.__data__(index) 

    def __contains__(self, item):
        value = self.T(item)
        return value in self.__data__

    def __delitem__(self, index):
        del self.__data__[index]

    def __len__(self):
        return len(self.__data__)

    def __iter__(self):
        '''Returns a iterable over the data set'''
        return self.__data__.__iter__()

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
        # Converter Models to References
        if issubclass(T, Model):
            self.T = Reference(T)
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

    def __iter__(self):
        '''Returns a iterable over the data set'''
        return self.__data__.__iter__()

    def __eq__(self, other):
        return self.__data__ == other

    def __len__(self):
        return len(self.__data__)

"""
TypedCounter:
A mixin of a Counter and a TypedMap. There is catch
though; a TypedCounter does not support any of the different
construction configurations of the default Counter type.
But it works as expected.
"""
class TypedCounter(Counter, TypedMap):
    '''A Counter that does validation of data'''

    def __init__(self, T=blank, V=blank):
        '''Basic initialisation of the TypedMap'''
        TypedMap.__init__(self, T, V)
        super(Counter, self).__init__()          
