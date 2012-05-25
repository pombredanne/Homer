Author : Iroiso . I (iroiso at live dot com)
License: Apache License 2.0
Copyright 2011, June inc.


Description:
============
Homer is the pragmatic python based object non-relational 
mapper for Apache Cassandra that doesn't get in your way.

Installation:
=============
To install you can use pip or download the latest build from 
[github](http://github.com/junery/homer)

pip:
====
$ sudo pip install homer (Not Done Yet)

from source:
============
Download the latest build by cloning master repository

$ git clone git://github.com/junery/homer.git
$ cd homer
$ sudo python setup.py install

Example Usage:
==============
This example walks you through creating a simple model and persisting it to cassandra. 
We assume you've used cassandra before; If you haven't there are plenty of helpful 
resources on the [Project Site](http://cassandra.apache.org) that'll get you started.

So here we go:

```python
# Relevant imports.
from homer.options import *
from homer.core import Model, key, Key
from homer.core.commons import *

# Point Homer to Cassandra and create a default keyspace;
# Do this before you declare your models.
instances = ["localhost:9160", "localhost:9161",]
c = DatastoreOptions(servers=instances, username="test", password="test")
namespace = Namespace(name= "June", cassandra= c)
namespaces.add(namespace)
namespaces.default = "June" # or you could use namespaces.default = namespace

'''
The snippet above points homer to your datastores and tells
Homer to map all models to the 'June' keyspace by default. You
can always map a Model to a different keyspace with the idiom 
below.

@key("name", namespace="Logging")
class Stat(object): ....

Ok, thats a bit too early; but read on!
'''

# Declare your model. 
@key("name")
class Profile(Model): 
    name = String("", indexed = True)
    link = URL("http://june.com", indexed = True)
    
'''
The `@key("name")` idiom makes the 'name' field the primary key
of all Profile models. The String and URL properties are just common
descriptors for data validation; adding `indexed=true` tells 
Casssandra to index all 'names' and 'links' which is useful for CQL
queries as we'll see later on.
'''

# Specify your consistency level and save your instance.
with Level.Quorum:
    person = Profile(name = 'Yoda', link = 'http://faceboook.com/yoda')
    person.save()

'''
Homer will automatically create a Column Family named 'Profile' 
in a keyspace named 'June' when you save an instance of your model
for the first time.
'''

# Reading from Cassandra is Simple.
found = Profile.read('Yoda') 
assert person == found

# Want stronger consistency? you can use the 'with Level' clause too!
with Level.All:
    found = Profile.read('Yoda')
    assert person == found


# You can also use CQL to search the secondary index, 
results = Profile.query("WHERE link=:link", link="http://facebook.com/iroiso")

'''
The *results* object above is an iterable object that yields
Profile instances when you iterate over it. 
''''
```
This is by no means a complete guide. There is still alot of documenting
and explaining to do, need more samples? please dive into the [Tests Directory](src/tests) 
to quench your thirst. Any suggestions or improvements? Fork away!

Does any of these seem interesting? then, you'd like to join us! or contribute, 
either ways we'd love to hear from you. Reach out to us iroiso at live dot com.
