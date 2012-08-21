import unittest

import startuppoker_spectator.spectator as spectator

class SpectatorRepositoryTest(unittest.TestCase):

    def test_is_for_player(self):
        action = {'player': u'p0', 'info': 'bet', 'stake': 40}
        self.assertTrue(spectator.is_for_player(action, 'p0'))
        self.assertFalse(spectator.is_for_player(action, 'p1'))

    def test_is_bet(self):
        self.assertTrue(spectator.is_bet({'player': u'player_7', 'info': 'bet', 'stake': 40}))
        self.assertFalse(spectator.is_bet({'player': u'player_7', 'info': 'next_bet_round', 'stake': 40}))

