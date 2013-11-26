# Copyright (c) The SimpleFIN Team
# See LICENSE for details.

from twisted.internet import defer, threads
import scrypt
from keyczar.keys import AesKey, HmacKey
from keyczar import util


class _HashingCryptingStore(object):

    _sem = None

    def _hash(self, data):
        raise NotImplementedError

    def _encrypt(self, plaintext):
        raise NotImplementedError

    def _decrypt(self, ciphertext):
        raise NotImplementedError

    def _semaphore(self):
        if not self._sem:
            self._sem = defer.DeferredSemaphore(1)
        return self._sem

    def _lockRunDeferredArgs(self, func, *argd):
        dlist = defer.gatherResults(argd)
        sem = self._semaphore()
        return sem.run(self._reallyRun, func, dlist)

    def _reallyRun(self, func, arg_dlist):
        return arg_dlist.addCallback(self._reallyRunForReal, func)

    def _reallyRunForReal(self, args, func):
        return func(*args)

    def put(self, id, key, value):
        hashed_id = self._hash(id)
        hashed_key = self._hash(key)
        encrypted_value = self._encrypt(value)

        d = self._lockRunDeferredArgs(
            self.store.put,
            hashed_id,
            hashed_key,
            encrypted_value)
        d.addCallback(lambda x: None)
        return d

    def get(self, id, key):
        hashed_id = self._hash(id)
        hashed_key = self._hash(key)

        d = self._lockRunDeferredArgs(self.store.get, hashed_id, hashed_key)
        d.addCallback(self._decrypt)
        return d

    def delete(self, id, key=None):
        hashed_id = self._hash(id)
        hashed_key = defer.succeed(None)
        if key is not None:
            hashed_key = self._hash(key)

        d = self._lockRunDeferredArgs(
            self.store.delete,
            hashed_id,
            hashed_key
        )
        d.addCallback(lambda x: None)
        return d


class KeyczarStore(_HashingCryptingStore):
    """
    I wrap another data store such that everything is encrypted when
    stored in the wrapped store.
    """

    salt = 'non-random salt'

    def __init__(self, store, crypter):
        """
        @param store: Another data store (such as an SQL store).
        @param crypter: A L{keyczar.keyczar.Crypter} instance.
        """
        self.store = store
        self.crypter = crypter

    def _hash(self, data):
        return threads.deferToThread(scrypt.hash, data, self.salt)

    def _encrypt(self, plaintext):
        return threads.deferToThread(self.crypter.Encrypt, plaintext)

    def _decrypt(self, ciphertext):
        return threads.deferToThread(self.crypter.Decrypt, ciphertext)


class PasswordStore(_HashingCryptingStore):
    """
    I wrap another data store such that everything is encrypted with a
    password when stored in the store.
    """

    _key = None
    key_size = 32
    salt = 'non-random salt for PasswordStore'
    password_salt = 'some password salt'

    def __init__(self, store, password):
        """
        @param store: Another data store (such as an SQL store).
        @param password: A string password
        """
        self.store = store
        self.password = password

    def _hash(self, data):
        return threads.deferToThread(scrypt.hash, data, self.salt)

    def _getKey(self):
        if self._key:
            return self._key
        key_bytes = scrypt.hash(self.password, self.password_salt,
                                buflen=self.key_size)
        key_string = util.Base64WSEncode(key_bytes)
        hmac_key = HmacKey(key_string)
        self._key = AesKey(key_string, hmac_key)
        return self._key

    def _encrypt(self, plaintext):
        key = self._getKey()
        return threads.deferToThread(key.Encrypt, plaintext)

    def _decrypt(self, ciphertext):
        key = self._getKey()
        return threads.deferToThread(key.Decrypt, ciphertext)
