Odds and Ends:
==============
Some things to note if you are using homer.

1. Data Serialization:
   No support for Mixins: Your type must either be a set, sequence, simple or mapping

2. AppEngine does not support serialization of descriptors that are added later e.g.
   
   class Person(db.Model):
       birthday = Date()
   
   if I'd do something like
       Person.age = Integer()
       p = Person()
       p.birthday = #Some date here
       p.age = 45 #May not work
       p.put() # Will only store the birthday attribute to the datastore.
   
   Well Homer wisely avoided this :)

3. By default all the common properties coerce types set on them. BUT containers
   type do not try to coerce thier elements. I think devs should know. coercion
   should be a convenience not a habit:::: Fixed Yeah, Now Homer will try to coerce all the elements in a container.

4. Do normal type coercion, third party devs should make sure their Descriptors are callable

5. Homer does not currently suppor ttl CF's in cassandra. how do I do this elegantly? --- Done; YEAH..
6. Why didn't you implement automatic key Generation ?

Odds:
What about classes from different modules clashing; The @key decorator can prevent this
by throwing an exception when the same kind is defined twice in the same namespace.

Ten things I love about Homer-Simpson:
1.  Autofailover
2.  Loadbalancing
3.  Typesafe object mapping with data validation
4.  Low latency, through nifty optimizations under the hood; Everything occurs in batches.
5.  Very high level, Cluelessness? SWEET.
6.  Builtin Model SerDe (Serialization, Deserialization) ; JSON, XML
7.  Lightning Speed, Yup - Using the store and cache pattern automatically
8.  The @key decorator; Simplicity...
9.  Rich data modeling (String, Map, List, ...)
10. Model.rollback(); Incase I screw up ?
11. Context Managers for controlling Consistency.
12. CqlQuery support with automatic object mapping...!. Cutting edge.
13. It runs on Apache Cassandra and Memcache...
14. Out of the box multiple keyspace/namespaces support.
15. Indexing support out of the box.
16. Automatic and smart coercion and constructors; very pythonic I guess.
17. Dynamically expandable models.... No need for db.Expando I guess.
18. Homer minds its own bussiness. You can't poke around with the internals of Model and shouldn't be able to
19. Homer is ThreadSafe
17. .... Oops I've gone past 10; Its time to stop I guess...


