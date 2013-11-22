from twisted.internet import defer, threads
import scrypt


class KeyczarStore(object):
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

    def _expand(self, args, func):
        return func(*args)

    def put(self, id, key, value):
        hashed_id = self._hash(id)
        hashed_key = self._hash(key)
        encrypted_value = self._encrypt(value)

        dlist = defer.gatherResults([hashed_id, hashed_key, encrypted_value])
        return dlist.addCallback(self._expand, self.store.put)

    def get(self, id, key):
        hashed_id = self._hash(id)
        hashed_key = self._hash(key)
        dlist = defer.gatherResults([hashed_id, hashed_key])
        dlist.addCallback(self._expand, self.store.get)
        dlist.addCallback(self._decrypt)
        return dlist

    def delete(self, id, key=None):
        hashed_id = self._hash(id)
        hashed_key = defer.succeed(None)
        if key is not None:
            hashed_key = self._hash(key)
        dlist = defer.gatherResults([hashed_id, hashed_key])
        dlist.addCallback(self._expand, self.store.delete)
        return dlist
