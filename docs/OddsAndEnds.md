Odds and Ends:
==============
Some things to note if you are using homer.

1. Data Serialization:
   No support for Mixins: Your type must either be a set, sequence, simple or mapping

2. AppEngine does not support serialization of descriptors that are added later e.g.
   
   class Person(db.Models):
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
