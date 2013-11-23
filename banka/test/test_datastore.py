# Copyright (c) The SimpleFIN Team
# See LICENSE for details.
from twisted.trial.unittest import TestCase
from twisted.internet import defer
from twisted.python.filepath import FilePath

from keyczar import keyczart, keyinfo, keyczar

from banka.datastore import KeyczarStore, PasswordStore


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
        val = yield store.put('id', 'key', 'value')
        self.assertEqual(val, None, "put must return None")

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
        res = yield store.delete('id', 'foo')
        self.assertFailure(store.get('id', 'foo'), KeyError)
        self.assertEqual(res, None, 'delete must return None')

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

    @defer.inlineCallbacks
    def test_race(self):
        """
        A get immediately after a put should wait until the put is done.
        """
        store = yield self.getEmptyStore()

        # lack of yield is intentional
        put_d = store.put('id', 'foo', 'bar')
        get_d = store.get('id', 'foo')
        del_d = store.delete('id')

        yield put_d
        result = yield get_d
        yield del_d
        self.assertEqual(result, 'bar')


class KeyczarStoreFunctionalTest(TestCase, DataStoreTestMixin):

    timeout = 20

    @defer.inlineCallbacks
    def getEmptyStore(self):
        from norm import makePool
        from banka.sql import SQLDataStore, sqlite_patcher
        pool = yield makePool('sqlite:')
        yield sqlite_patcher.upgrade(pool)

        # make keyczar key set
        key_dir = self.mktemp()
        FilePath(key_dir).makedirs()
        keyczart.Create(key_dir, 'test key', keyinfo.DECRYPT_AND_ENCRYPT)
        keyczart.AddKey(key_dir, keyinfo.PRIMARY)
        crypter = keyczar.Crypter.Read(key_dir)

        defer.returnValue(KeyczarStore(SQLDataStore(pool), crypter))


class KeyczarStoreTest(TestCase):

    timeout = 10

    @defer.inlineCallbacks
    def getEmptyStore(self):
        from norm import makePool
        from banka.sql import SQLDataStore, sqlite_patcher
        pool = yield makePool('sqlite:')
        yield sqlite_patcher.upgrade(pool)

        defer.returnValue(SQLDataStore(pool))

    @defer.inlineCallbacks
    def test_encrypted(self):
        """
        The data should not be accessible from the base store.
        """
        # make keyczar key set
        key_dir = self.mktemp()
        FilePath(key_dir).makedirs()
        keyczart.Create(key_dir, 'test key', keyinfo.DECRYPT_AND_ENCRYPT)
        keyczart.AddKey(key_dir, keyinfo.PRIMARY)
        crypter = keyczar.Crypter.Read(key_dir)

        base_store = yield self.getEmptyStore()
        enc_store = KeyczarStore(base_store, crypter)
        yield enc_store.put('id', 'key', 'value')
        self.assertFailure(base_store.get('id', 'key'), KeyError)


class PasswordStoreFunctionalTest(TestCase, DataStoreTestMixin):

    timeout = 20

    @defer.inlineCallbacks
    def getEmptyStore(self):
        from norm import makePool
        from banka.sql import SQLDataStore, sqlite_patcher
        pool = yield makePool('sqlite:')
        yield sqlite_patcher.upgrade(pool)
        defer.returnValue(PasswordStore(SQLDataStore(pool), 'password'))
