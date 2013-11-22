# Copyright (c) The SimpleFIN Team
# See LICENSE for details.
from twisted.trial.unittest import TestCase
from twisted.internet import defer

from banka.test.test_datastore import DataStoreTestMixin
from banka.sql import SQLDataStore, sqlite_patcher

from norm import makePool


class SqliteSQLDataStoreTest(TestCase, DataStoreTestMixin):

    timeout = 2

    @defer.inlineCallbacks
    def getEmptyStore(self):
        pool = yield makePool('sqlite:')
        yield sqlite_patcher.upgrade(pool)
        defer.returnValue(SQLDataStore(pool))
