import unittest
import sqlite3
from startuppoker_spectator.sqlite_repository import create_db,\
    migrate_couchdb, create_meta

class SqliteRepositoryTest(unittest.TestCase):

    def query_game(self):
        conn = sqlite3.connect('startuppoker.sqlite')
        c = conn.cursor()
        c.execute('select * from game')
        return c

    def test_create_db(self):
        create_db(create_meta())

        self.assertEquals(0, len(self.query_game().fetchall()))

    def test_game_migration(self):
        migrate_couchdb('test')

        self.assertEquals(10, len(self.query_game().fetchall()))
