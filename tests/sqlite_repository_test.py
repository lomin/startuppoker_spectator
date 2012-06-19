import unittest
import sqlite3
import startuppoker_spectator.sqlite_repository as repository
from startuppoker_spectator.sqlite_repository import create_db,\
    migrate_couchdb, create_meta, get_pot_share

class SqliteRepositoryTest(unittest.TestCase):

    def query_game(self):
        conn = sqlite3.connect('startuppoker.sqlite')
        c = conn.cursor()
        c.execute('select * from game')
        return c

    def _test_create_db(self):
        create_db(create_meta())

        self.assertEquals(0, len(self.query_game().fetchall()))

    def _test_game_migration(self):
        migrate_couchdb('test', 10)

        self.assertEquals(10, len(self.query_game().fetchall()))

    def get_history(self):
        return repository.get_history('test', 2, 120600)

    def test_get_pot_share(self):
        self.assertEquals(1160, get_pot_share(self.get_history()))

    def test_get_player_names(self):
        self.assertEquals(
                [
                    "player_6",
                    "player_1",
                    "player_2",
                    "player_3",
                    "player_5",
                    "player_7",
                    "player_4",
                    "player_0",],
                repository.get_player_names(self.get_history()))

    def test_winners(self):
        self.assertEquals(['player_7'], repository.get_winners(self.get_history()))

    def test_community_cards(self):
        self.assertEquals([u'8c', u'6h', u'10s', u'10d', u'3d'], repository.get_community_cards(self.get_history()))

    def test_pocket_cards(self):
        self.assertEquals([u'Ad', u'7h'], repository.get_pocket_cards(self.get_history())['player_6'])

    def test_get_action(self):
        self.assertEquals({'player': u'player_7', 'info': 'bet', 'stake': 40, 'bet': 'RAISE'},
          repository.get_action(self.get_history(), 5))

    def test_is_for_player(self):
        action = {'player': u'p0', 'info': 'bet', 'stake': 40}
        self.assertTrue(repository.is_for_player(action, 'p0'))
        self.assertFalse(repository.is_for_player(action, 'p1'))

    def test_is_bet(self):
        self.assertTrue(repository.is_bet({'player': u'player_7', 'info': 'bet', 'stake': 40}))
        self.assertFalse(repository.is_bet({'player': u'player_7', 'info': 'next_bet_round', 'stake': 40}))

    def test_get_last_games(self):
        self.assertEquals([
            u'test-2:0000120591',
            u'test-2:0000120592',
            u'test-2:0000120593',
            u'test-2:0000120594',
            u'test-2:0000120595',
            u'test-2:0000120596',
            u'test-2:0000120597',
            u'test-2:0000120598',
            u'test-2:0000120599',
            u'test-2:0000120600'], repository.get_last_games('test'))

    def test_get_number_of_actions(self):
        self.assertEquals(30, repository.get_number_of_actions(self.get_history()))


