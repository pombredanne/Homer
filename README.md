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
from homer.options import CONFIG
from homer.core import Model, key, Key
from homer.core.commons import String, URL


'''
The snippet above points homer to your datastores and tells
Homer to map all models to the 'June' keyspace by default. You
can always map a Model to a different keyspace with the idiom 
below.

@key("name", namespace="Logging")
class Stat(object): ....

But you have to create a different configuration for the namespace 'Logging';
Ok, thats a bit too early; but read on!
'''

# Declare your model. 
@key("name")
class Profile(Model): 
    name = String("", indexed=True)
    link = URL("http://june.com", indexed=True)
    
'''
The `@key("name")` idiom makes the 'name' field the primary key
of all Profile models. The String and URL properties are just common
descriptors for data validation; adding `indexed=true` tells 
Casssandra to index all 'names' and 'links' which is useful for CQL
queries as we'll see later on.
'''

# Specify your consistency level and save your instance.
with Level.Quorum:
    person = Profile(name='Yoda', link='http://faceboook.com/yoda')
    person.save()

# You can also save with the default consistency level which is Consistency Level One.  
another = Profile(name='Iroiso', link='http://facebook.com/iroiso')
another.save()


'''
Homer will automatically create a Column Family named 'Profile' 
in a keyspace named 'June' when you save an instance of your model
for the first time.
'''

# Reading from Cassandra is Simple.
found = Profile.read('Yoda') 
assert person == found

# Want stronger consistency? you can use the 'with Level.All' clause too!
with Level.All:
    found = Profile.read('Yoda')
    assert person == found
    
'''
Other Consistency Levels are (One, Two, Three, EachQuorum, LocalQuorum and Any), 
You can also use CQL to search the secondary index, with the idiom below.
'''
found = Profile.query(link="http://facebook.com/iroiso").fetchone()
assert found == another

'''
The Profile.query() returns a generator that yields Profile instances when you
iterate over it. 
''''
```
This is by no means a complete guide. There is still alot of documenting
and explaining to do, need more samples? please dive into the [Tests Directory](http://github.com/junery/homer/src/tests) 
to quench your thirst. Any suggestions or improvements? Fork away!

Does any of these seem interesting? then, you'd like to join us! or contribute, 
either ways we'd love to hear from you. Reach out to us iroiso at live dot com.

Notes:
------
Another opensource project made with love in the Junery; pragmatic, simple,  
beautiful and pleasurable to use.
