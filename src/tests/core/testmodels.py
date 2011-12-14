#!/usr/bin/env python
"""
Author : Iroiso . I (iroiso@live.com)
Project: Homer SDK
License: Apache License 2.0
Copyright 2011, June inc.

Description:
Unittests for the Models module...
"""
from unittest import TestCase,expectedFailure,skip
from datetime import datetime, date
from homer.core.models import key, Model, Property, Type, READONLY, READWRITE
from homer.core.models import BadValueError, BadKeyError, UnDeclaredPropertyError,\
    NamespaceCollisionError, StorageSchema
  
class TestKeyAndModel(TestCase):
    """Keys and Model where built to work together; they should be tested together"""
    
    def testkeySanity(self):
        """Makes sure that basic usage for @key works"""
        @key("name")
        class Person(Model):
            name = Property("JohnBull")
            
        assert isinstance(Person, type)
        person = Person()
        assert person.key() is not None, "Key Must not be None when its attribute is non null"
        self.assertTrue(person.name == "JohnBull")
        print "'" + str(person.key()) + "'"
        person.name = None
        self.assertRaises(BadKeyError, lambda : person.key())
        
    def testkeyAcceptsOnlyModels(self):
        """Asserts that @key only works on subclasses of Model"""
        with self.assertRaises(TypeError):
            @key("name")
            class House(object):
                name = Property("House M.D")

    def testkeyAcceptsCallables(self):
        """Asserts that @key can accept a callable function"""
        @key("name")
        class House(Model):
            '''A key whose name is function'''
            number = Property()
            def name(self):
                '''Useful for building composite keys'''
                return "House: %s" % self.number
                
        house = House(number = 50)
        self.assertEquals(house.key().key, "House: 50")
    
    def testkeyDetectsNamespaceCollision(self):
        """Asserts that the attribute passed in to @key must exist in the class"""
        @key("name", namespace="April")
        class House(Model):
            pass
        
        with self.assertRaises(NamespaceCollisionError):
            @key("name", namespace="April")
            class House(Model):
                pass
    
    def testModelAcceptsKeywords(self):
        """Tests If accepts keyword arguments and sets them"""
        diction = { "name": "iroiso", "position" : "CEO", "nickname" : "I.I"}
        class Person(Model):
            name = Property()
            position = Property()
            nickname = Property()
        
        person = Person(**diction)
        for name in diction:
            self.assertEqual(getattr(person,name), diction[name])
        print "..........................................."
        for name, value in person.fields().items():
            print name, str(value)

class TestModelDictability(TestCase):
    '''Proves that a Model behaves like a dictionary'''
    def setUp(self):
        '''Common setup code'''
        class Bug(Model):
            name = Property(default = "house", required = True)
            reporter = Property(type = str) 
        self.bug = Bug(name = "Gilly")
    
    def testModelSupportsInOperator(self):
        '''Shows that you can iterate through attributes of a Model like a dictionary'''
        self.bug["house"] = "Blue house"
        self.assertTrue('name' in self.bug)
        self.assertTrue('house' in self.bug)
        
    def testSet(self):
        '''Shows that you can add properties to a Model like a dict, allowing you create wide rows'''
        self.bug["issue_number"] = 1245
        self.assertEquals(self.bug.issue_number, 1245)
        self.assertTrue("issue_number" in self.bug)
        self.assertTrue("name" in self.bug)
        
    def testRemove(self):
        '''Shows that dict-like subtraction of properties work'''
        self.bug["house"] = "blue"
        self.assertEquals(self.bug.house, "blue")
        del self.bug["house"]
        del self.bug["name"]
        self.assertFalse("house" in self.bug)
        self.assertFalse("name" in self.bug)
   
    def testKeys(self):
        '''Shows that keys() work properly'''
        class Person(Model):
            name = Property(default = "house", required = True)
            reporter = Property(type = str) 
        person = Person(name="iroiso", reporter="Zainab")
        self.assertTrue("name" in person.keys())
        self.assertTrue("reporter" in person.keys())

    def testValues(self):
        '''Shows that values() work properly'''
        class Values(Model):
            name = Property(default = "house", required = True)
            reporter = Property(type = str) 
        person = Values(name="iroiso", reporter="zainab")
        self.assertTrue("iroiso", "zainab" in person.values())
        
    def testItems(self):
        '''Shows that items() works properly on a Model'''
        item = Model()
        for i in range(50):
            item[str(i)] = i
        print item.items()
        comparison = []
        for i in range(50):
            tup = (str(i), i)
            comparison.append(tup)
        bag = item.items()
        for tup in comparison:
            self.assertTrue(tup in bag)

    def testIterItems(self):
        '''Test iteritems() to show that it works'''
        item = Model()
        for i in range(50):
            item[str(i)] = i
        print item.items()
        comparison = []
        for i in range(50):
            tup = (str(i), i)
            comparison.append(tup)
        for tup in item.iteritems():
            self.assertTrue(tup in comparison)

    def testIterKeys(self):
        '''Tests that Iteration of over keys work'''
        item = Model()
        comparison = set()
        for i in range(50):
            item[str(i)] = i
            comparison.add(str(i))
        for i in item.iterkeys():
            self.assertTrue(i in comparison)
            
            
        
          
"""#.. Tests for homer.core.models.Type"""  
class TestType(TestCase):
    """Sanity Checks for Type"""
    def setUp(self):
        """Creates a Type"""
        class Bug(object):
            name = Type(type = str )
            filed = Type(type = date ) 
            
        self.bug = Bug()
           
    def testTypeSanity(self):
        """Makes sure that Type doe type checking"""
        self.assertRaises(Exception, lambda: 
            setattr(self.bug, "filed", "Today"))
        now = datetime.now().date()
        self.bug.filed = now
   
    def testTypeCoercion(self):
        """Does Type do coercion? """
        self.bug.name = 23
        self.assertEqual(self.bug.name, "23")
    
    def testTypeAcceptsPositionalArgs(self):
        """Does type accept positional args"""
        class Blog(object):
            def __init__(self, name, post):
                self.name = name
                self.post = post
                
        class News(object):
            blog = Type(type = Blog)
            
        news = News()
        news.blog = ["iroiso", "a little something"]
        self.assertEqual(news.blog.name, "iroiso")
        self.assertEqual(news.blog.post, "a little something")
        
    def testTypeKeywordArgs(self):
        """Does Type accept keyword arguments"""
        class Blog(object):
            def __init__(self, name, post):
                self.name = name
                self.post = post
                
        class News(object):
            blog = Type(type = Blog)
            
        another = News()
        another.blog = {"name": "iroiso", "post": "a little something"}
        self.assertEqual(another.blog.name, "iroiso")
        self.assertEqual(another.blog.post, "a little something")  
        

"""#.. Tests for homer.core.Model.Property"""
class TestProperty(TestCase):
    def setUp(self):
        """Creates a new Bug class everytime"""
        class Bug(object):
            """No bugs..."""
            name = Property()
            email = Property("iroiso@live.com", mode = READONLY)
            girlfriend = Property("gwen", choices = ["amy","stacy","gwen"],required = True) 
        self.bug = Bug()
      
    def testReadWriteProperty(self):
        """Makes sure that ReadWrites can be read,written and deleted"""
        setattr(self.bug,"name","Emeka")
        self.assertEqual(self.bug.name , "Emeka")
        delattr(self.bug, "name")
        with self.assertRaises(AttributeError):
            print self.bug.name
    
    def testIndexed(self):
        """Tests if Indexed Properties work"""
        class Bug(object):
            name = Property("A bugs life", indexed = True)
        self.assertTrue(Bug.name.indexed)
        
    def testSetDeleteSetGetWorks(self):
        """Tests this sequence, Delete,Set,Get does it work; Yup I know its crap"""
        setattr(self.bug,"name","First name")
        delattr(self.bug,"name")
        self.assertRaises(AttributeError, lambda: getattr(self.bug,"name"))
        setattr(self.bug,"name","NameAgain")
        self.assertEquals(self.bug.name,"NameAgain")
        delattr(self.bug,"name")
        self.assertRaises(AttributeError, lambda: getattr(self.bug, "name"))
        setattr(self.bug,"name","AnotherNameAgain")
        self.assertEquals(self.bug.name,"AnotherNameAgain")
    
    def testDelete(self):
        """Tests if the del keyword works on READWRITE attributes"""
        self.bug.name = "Emeka"
        del self.bug.name
        self.assertRaises(Exception,lambda:getattr(self.bug,"name"))
         
    def testChoices(self):
        """Tries to set a value that is not a amongst the properties choices"""
        with self.assertRaises(BadValueError):
            self.bug.girlfriend = "steph"
            
    def testRequired(self):
        """Asserts that a required Property cannot be set to an empty value"""
        with self.assertRaises(BadValueError):
            self.bug.girlfriend = None
    
    def testReadOnlyProperty(self):
        """Makes sure that ReadOnlies are immutable """
        with self.assertRaises(ValueError):
            self.readOnly = Property(mode = READONLY)
        with self.assertRaises(AttributeError):
            print("You cannot write to a read only Property")
            setattr(self.bug,"email",100)
        with self.assertRaises(AttributeError):
            print("You cannot delete a read only Property")
            delattr(self.bug,"email")
    
