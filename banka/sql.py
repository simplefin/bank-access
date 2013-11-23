# Copyright (c) The SimpleFIN Team
# See LICENSE for details.


from norm.patch import Patcher


class SQLDataStore(object):
    """
    I store data in an SQL database.
    """

    def __init__(self, pool):
        """
        @param pool: A norm pool.
        """
        self.pool = pool

    def put(self, id, key, value):
        """
        Store a data value.

        @param id: ID of key set.
        @type id: str

        @param key: value key
        @type key: str

        @param value: value
        @type value: str
        """
        return self.pool.runOperation('replace into data (id, key, value) '
                                      'values (?,?,?)',
                                      (buffer(id), buffer(key), buffer(value)))

    def get(self, id, key):
        """
        Get a stored value.

        @raise KeyError: (Deferred) if no such id or key is in the database.
        """
        d = self.pool.runQuery('select value from data where id=? and key=?',
                               (buffer(id), buffer(key)))

        def one(rows):
            try:
                return str(rows[0][0])
            except:
                raise KeyError((id, key))
        d.addCallback(one)
        return d

    def delete(self, id, key=None):
        """
        Delete a single key-value pair or and entire set of key-value pairs.
        """
        if key is None:
            return self.pool.runOperation('delete from data where id=?',
                                          (buffer(id),))
        else:
            return self.pool.runOperation(
                'delete from data where id=? and key=?',
                (buffer(id), buffer(key)))


sqlite_patcher = Patcher()
sqlite_patcher.add('init', [
    '''CREATE TABLE data (
        id blob,
        key blob,
        value blob,
        primary key (id,key)
    )''',
])
