#!/usr/bin/env python
#
# Copyright 2011 June Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import time
from homer.core import *
from homer.options import Settings
from homer.backend import Level
from .testdb import BaseTestCase

class TestBatching(BaseTestCase):
    '''Behavioural contract for Simpson'''    
    def testBatchPut(self):
        '''Tests if puts in batches actually works'''
        import time
        import uuid
        
        @key("id")
        class Profile(Model):
            id = String(required = True, indexed = True)
            fullname = String(indexed = True)
            bookmarks = Map(String, URL)   
        
        profile = Profile(id = str(uuid.uuid4()), fullname = "Iroiso Ikpokonte", bookmarks={})
        profile.save()
        
        l = []
        for i in range(500):
            profile = Profile(id = str(i), fullname = "Iroiso Ikpokonte", bookmarks={})
            profile.bookmarks["google"] = "http://google.com"
            profile.bookmarks["twitter"] = "http://twitter.com"
            l.append(profile)
        
        start = time.time()
        print ''
        print ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
        with Level.All:
            self.db.saveMany(Settings.default(),*l)
        print "Time Taken to put 500 Profiles: %s secs" % (time.time() - start)
        print ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
        
        cursor = self.connection
        cursor.execute("USE %s" % Settings.keyspace())
        cursor.execute("SELECT COUNT(*) FROM Profile;")
        count = cursor.fetchone()[0]
        print "Count: ", count
        self.assertTrue(count == 501)
        
