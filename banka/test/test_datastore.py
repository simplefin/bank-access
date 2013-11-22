# Copyright (c) The SimpleFIN Team
# See LICENSE for details.
from twisted.internet import defer


class DataStoreTestMixin(object):

    timeout = 5

    def getEmptyStore(self):
        """
        Get an empty data store to be tested with this mixin.
        """
        raise NotImplementedError("You must implement getEmptyStore "
                                  "in order to use DataStoreTestMixin")

    @defer.inlineCallbacks
    def test_put(self):
        """
        You should be able to put a string key value pair, associated with
        and id, into the store.
        """
        store = yield self.getEmptyStore()
        yield store.put('id', 'key', 'value')

    @defer.inlineCallbacks
    def test_get(self):
        """
        You should be able to get data out that you previously put in.
        """
        store = yield self.getEmptyStore()
        yield store.put('id', 'key', 'value')
        res = yield store.get('id', 'key')
        self.assertEqual(res, 'value')

    @defer.inlineCallbacks
    def test_getAll(self):
        """
        You should be able to get all the data for an id.
        """
        store = yield self.getEmptyStore()
        yield store.put('id', 'a', 'apple')
        yield store.put('id', 'b', 'banana')
        res = yield store.getAll('id')
        self.assertEqual(res, {'a': 'apple', 'b': 'banana'})

    @defer.inlineCallbacks
    def test_put_overwrite(self):
        """
        If you put things in twice, overwrite them.
        """
        store = yield self.getEmptyStore()
        yield store.put('id', 'a', 'apple')
        yield store.put('id', 'a', 'aardvark')
        res = yield store.get('id', 'a')
        self.assertEqual(res, 'aardvark', "Should get most recent change")

    @defer.inlineCallbacks
    def test_groupById(self):
        """
        Different ids should hold different key-value sets.
        """
        store = yield self.getEmptyStore()
        yield store.put('id1', 'a', 'apple')
        yield store.put('id2', 'a', 'aardvark')

        res1 = yield store.get('id1', 'a')
        self.assertEqual(res1, 'apple')

        res2 = yield store.get('id2', 'a')
        self.assertEqual(res2, 'aardvark')

    @defer.inlineCallbacks
    def test_get_missingId(self):
        """
        A KeyError should be raise for missing IDs.
        """
        store = yield self.getEmptyStore()
        self.assertFailure(store.get('id', 'foo'), KeyError)

    @defer.inlineCallbacks
    def test_get_missingKey(self):
        """
        A KeyError should be raised for a missing key.
        """
        store = yield self.getEmptyStore()
        yield store.put('id', 'foo', 'foo')
        self.assertFailure(store.get('id', 'bar'), KeyError)

    @defer.inlineCallbacks
    def test_delete_key(self):
        """
        Deleting an item will make it unavailable using get.
        """
        store = yield self.getEmptyStore()
        yield store.put('id', 'foo', 'foo')
        yield store.delete('id', 'foo')
        self.assertFailure(store.get('id', 'foo'), KeyError)

    @defer.inlineCallbacks
    def test_delete_id(self):
        """
        Deleting an id will delete all associated items.
        """
        store = yield self.getEmptyStore()
        yield store.put('id', 'foo', 'foo')
        yield store.put('id', 'bar', 'bar')
        yield store.delete('id')
        self.assertFailure(store.get('id', 'foo'), KeyError)
        self.assertFailure(store.get('id', 'bar'), KeyError)
