Odds and Ends:
==============
Some things to note if you are using homer.

1. Write simple SerDe
2. Fix the Type Quirk, to make sure that Type(Blog) works, I don't want to keep doing Type(type = str, default = "Hello")


Ten things I love about Homer-Simpson:
1.  Autofailover => Done
2.  Loadbalancing => Done
3.  Typesafe object mapping with data validation => Done
4.  Low latency, through nifty optimizations under the hood; Everything occurs in batches. => ToDo
5.  Very high level, Cluelessness? SWEET. => Done
6.  Builtin Model SerDe (Serialization, Deserialization) ; JSON, XML, YAML => ToDo
7.  Lightning Speed, Yup - Using the store and cache pattern automatically => ToDo
8.  The @key decorator; Simplicity... => Done
9.  Rich data modeling (String, Map, List, ...) => Done
10. Model.rollback(); Incase I screw up ? => Done
11. Context Managers for controlling Consistency. => Done
12. CqlQuery support with automatic object mapping...!. Cutting edge. => ToDo
13. It runs on Apache Cassandra and Memcache... => Half Done
14. Out of the box multiple keyspace/namespaces support. => Done
15. Indexing support out of the box. => Done
16. Automatic and smart coercion and constructors; very pythonic I guess. => Done
17. Dynamically expandable models.... No need for db.Expando I guess; ??? => WIP
18. Homer minds its own bussiness. You can't poke around with the internals of Model and shouldn't be able to => NA
19. Homer is ThreadSafe => Done
20. Wide and Skinny Rows...; Using properties and the dict protocol.
17. .... Oops I've gone past 10; Its time to stop I guess...


