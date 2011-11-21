Odds and Ends:
==============
Some things to note if you are using homer.

1. Write simple SerDe
2. Fix the Type Quirk, to make sure that Type(Blog) works, I don't want to keep doing Type(type = str, default = "Hello")


Ten things I love about Homer-Simpson:
1.  Autofailover
2.  Loadbalancing
3.  Typesafe object mapping with data validation
4.  Low latency, through nifty optimizations under the hood; Everything occurs in batches.
5.  Very high level, Cluelessness? SWEET.
6.  Builtin Model SerDe (Serialization, Deserialization) ; JSON, XML, YAML
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


