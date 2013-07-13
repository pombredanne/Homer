Author: I (iroiso at live dot com)  
License: Apache License 2.0  
&copy; 2011, June inc.

Description:
------------
Homer is an intuitive and pragmatic python based object non-relational 
mapper for Apache Cassandra with a beautiful API.

Installation:
-------------
To install you can use pip or download the latest build from 
[Github](http://github.com/junery/homer)

##pip:
$ sudo pip install homer (Not Done Yet)

##from source:
Download the latest build by cloning master repository

$ git clone git://github.com/junery/homer.git  
$ cd homer  
$ sudo python setup.py install  

Example Usage:
--------------
This example walks you through creating a simple model and persisting it to cassandra. 
We assume you've used cassandra before; If you haven't there are plenty of helpful 
resources on the [Apache Cassandra Project Page](http://cassandra.apache.org) that'll get you started.

So here we go:

```python
# Relevant imports.
from homer import String, URL
from homer import key, Model, Level

'''
Homer models are python classes that extend the homer 'Model' super class.
Let's create a model for storing profile information in cassandra.
'''

@key("name")
class Profile(Model): 
    name = String()
    fullname = String(indexed=True)
    link = URL("http://rafiki.me/user/new", indexed=True)
    
'''
The `@key("name")` idiom makes the 'name' field the primary key
of all Profile models. The String and URL properties are just common
descriptors for data conversion and validation; adding `indexed=true` tells 
Homer to index the name and link property of the Profile class which would allow 
us to query against them later.
You can create new models like ordinary python classes, like this:
'''
person = Profile(name='Yoda', link='http://faceboook.com/yoda', fullname="Master Yoda")

'''
Then you can save the person to cassandra by calling person.save(), 
this stores the profile you created with the default consistency level which is
ConsistencyLevel.ONE
'''
person.save()

'''
Notice all the things you aren't doing:
1. You aren't creating any keyspaces
2. You aren't creating any column families.
3. Serialization and Deserialization
4. You aren't creating any thrift connections or doing any connection pooling or 
   any other low level stuff.

Nice huh :), Send me some coffee :D

Homer will automatically create a Column Family named 'Profile' 
in a keyspace named 'Homer' when you save an instance of your model
for the first time; It handles connection pooling, batch updates, and does a lot of cool
things under the hood for you. Homer's behavior is very configurable, and simple to configure.
I'll show you how to configure this in later documentation.
'''

# You can also save stuff with a different consistency level.  
another = Profile(name='Iroiso', link='http://facebook.com/iroiso')
with Level.Quorum:        #You can also use Level.One, Level.Two, or Level.All
    another.save()


# Reading from Cassandra with Homer is Simple.
found = Profile.read('Yoda') 
assert person == found

# Want stronger consistency when you read or write? you can use the 'with Level.All' clause too!
with Level.All:
    found = Profile.read('Yoda')
    assert person == found
    
'''
You can also query the indexes on cassandra with homer using the idiom: 
'''
iter = Profile.query(fullname="Master Yoda") # Returns a iterable generator that yields Profile instances 
found = Profile.query(fullname="Master Yoda").fetchone() # Retreive the first result.
assert found == person

'''
and you can count all your models using Profile.count (which also takes parameters and filters); 
'''
count = Profile.count() # To count all the Profile models, or
count = Profile.count(fullname="Master Yoda")

'''   
Finally you can retrieve all your models using Profile.all() which returns an generator 
object you can iterate over, like so:
'''
for person in Profile.all():
    print person.name

```
This is by no means a complete guide. There is still alot of documenting
and explaining to do, need more samples? please dive into the [Tests Directory](http://github.com/junery/homer/src/tests) 
to quench your thirst. Any suggestions or improvements? Fork away!

Wanna know about all the other cool things homer does for you behind the scenes?
Read: [All the Reasons why should use Homer](http://github.com/junery/homer/docs/OddsAndEnds.md)

Does any of these seem interesting? then maybe you'd like to join us our startup or contribute to Homer. 
Either ways we'd love to hear from you. Reach out to me here: iroiso at live dot com.

Notes:
------
Another pragmatic, beautiful and simple opensource project: "Made with Love in June." 
