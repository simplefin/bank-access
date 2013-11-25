# Copyright (c) The SimpleFIN Team
# See LICENSE for details.

from twisted.internet import defer, threads
import scrypt
from hashlib import sha256
from Crypto import Random
from Crypto.Cipher import AES


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

    iv_size = 16
    salt = 'non-random salt for PasswordStore'

    def __init__(self, store, password):
        """
        @param store: Another data store (such as an SQL store).
        @param password: A string password
        """
        self.store = store
        self.pw_hash = sha256(password).digest()

    def _hash(self, data):
        return threads.deferToThread(scrypt.hash, data, self.salt)

    def _mkIV(self):
        """
        Make a random initialization vector.
        """
        rnd = Random.new()
        return rnd.read(self.iv_size)

    def _encrypt(self, plaintext):
        # XXX that I'm making my own IV and padding makes me think I'm doing
        # it wrong.
        iv = self._mkIV()
        crypter = AES.new(self.pw_hash, AES.MODE_CBC, iv)

        padding_length = 16 - (len(plaintext) % 16)
        rnd = Random.new()
        padded_plaintext = plaintext + rnd.read(padding_length)

        def prefixWithDetails(cipher, iv, padding_length):
            return '%d %s%s' % (padding_length, iv, cipher)
        d = threads.deferToThread(crypter.encrypt, padded_plaintext)
        d.addCallback(prefixWithDetails, iv, padding_length)
        return d

    def _decrypt(self, ciphertext):
        # XXX see comment in _encrypt
        padding, ciphertext = ciphertext.split(' ', 1)
        padding_length = int(padding)

        iv = ciphertext[:self.iv_size]
        ciphertext = ciphertext[self.iv_size:]

        crypter = AES.new(self.pw_hash, AES.MODE_CBC, iv)

        def stripPadding(plaintext, padding_length):
            return plaintext[:-padding_length]
        d = threads.deferToThread(crypter.decrypt, ciphertext)
        d.addCallback(stripPadding, padding_length)
        return d
