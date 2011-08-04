# -*- coding: utf-8 -*-
"""
    couchdb_repository test

    :copyright: (c) 2011 by it-agile GmbH
    :license: BSD, see LICENSE for more details.
"""

import unittest
from startuppoker_spectator.couchdb_repository import get_stake_for_player, get_pot, get_bet_round, get_last_move

class LastActionTest(unittest.TestCase):

    def test_finds_last_action_when_step_belongs_to_player(self):
        document = {'history': [
                {'info': 'bet', 'player': 'player_1', 'stake': 10, 'bet': 'BET'}
        ]}
        self.assertEqual(('BET', 10), get_last_move('player_1', document, 0))

    def test_finds_nothing_when_first_round_and_no_action(self):
        document = {'history': [
            {'info': 'bet', 'player': 'player_2', 'stake': 10, 'bet': 'BET'}
        ]}
        self.assertEqual(('', ''), get_last_move('player_1', document, 0))

    def test_finds_last_action_when_step_belongs_not_to_player(self):
        document = {'history': [
                {'info': 'bet', 'player': 'player_1', 'stake': 10, 'bet': 'BET'},
                {'info': 'bet', 'player': 'player_2', 'stake': 10, 'bet': 'BET'}
        ]}
        self.assertEqual(('BET', 10), get_last_move('player_1', document, 1))

    def test_last_action_is_nothing_when_action_is_not_fold_and_before_next_betting_round(self):
        document = {'history': [
                {'info': 'bet', 'player': 'player_1', 'stake': 10, 'bet': 'CHECK'},
                {'info': 'next_bet_round'},
                {'info': 'bet', 'player': 'player_2', 'stake': 10, 'bet': 'BET'}
        ]}
        self.assertEqual(('', ''), get_last_move('player_1', document, 2))

    def test_finds_fold_when_no_action_in_current_or_last_betting_round(self):
        document = {'history': [
                {'info': 'bet', 'player': 'player_1', 'stake': 10, 'bet': 'CHECK'},
                {'info': 'next_bet_round'},
                {'info': 'bet', 'player': 'player_2', 'stake': 10, 'bet': 'BET'},
                {'info': 'next_bet_round'},
                {'info': 'bet', 'player': 'player_2', 'stake': 10, 'bet': 'BET'}
        ]}
        self.assertEqual(('FOLD', ''), get_last_move('player_1', document, 4))

class BettingRoundTest(unittest.TestCase):

    def setUp(self):
        self.document = {'history': [
                {'info': 'bet', 'player': 'player_1', 'stake': 10, 'bet': 'CHECK'},
                {'info': 'bet', 'player': 'player_2', 'stake': 10, 'bet': 'CHECK'},
                {'info': 'next_bet_round'},
                {'info': 'bet', 'player': 'player_2', 'stake': 10, 'bet': 'BET'},
                {'info': 'bet', 'player': 'player_2', 'stake': 10, 'bet': 'BET'},
                {'info': 'next_bet_round'},
                {'info': 'bet', 'player': 'player_2', 'stake': 10, 'bet': 'BET'},
                {'info': 'bet', 'player': 'player_2', 'stake': 10, 'bet': 'BET'},
                {'info': 'next_bet_round'},
            ]}

    def test_for_preflop(self):
        self.assertEqual(0, get_bet_round(self.document, 0))
        self.assertEqual(0, get_bet_round(self.document, 1))

    def test_for_flop(self):
        self.assertEqual(1, get_bet_round(self.document, 2))
        self.assertEqual(1, get_bet_round(self.document, 3))
        self.assertEqual(1, get_bet_round(self.document, 4))

    def test_for_turn(self):
        self.assertEqual(2, get_bet_round(self.document, 5))
        self.assertEqual(2, get_bet_round(self.document, 6))
        self.assertEqual(2, get_bet_round(self.document, 7))

    def test_for_river(self):
        self.assertEqual(3, get_bet_round(self.document, 8))

class getPotTest(unittest.TestCase):

    def setUp(self):
        self.document = {'history': [
                {'info': 'bet', 'player': 'stefan', 'stake': 10, 'bet': 'CALL'},
                {'info': 'bet', 'player': 'hugop', 'stake': 20, 'bet': 'CALL'},
                {'info': 'bet', 'player': 'steven', 'stake': 20, 'bet': 'CALL'},
                {'info': 'bet', 'player': 'stefan', 'stake': 30, 'bet': 'RAISE'},
                {'info': 'bet', 'player': 'steven', 'stake': 20, 'bet': 'CALL'},
                {'info': 'next_bet_round'},
                {'info': 'bet', 'player': 'stefan', 'stake': 20, 'bet': 'RAISE'},
                {'info': 'bet', 'player': 'steven', 'stake': 20, 'bet': 'CALL'},
                {'info': 'next_bet_round'},
                {'info': 'bet', 'player': 'stefan', 'stake': 40, 'bet': 'RAISE'},
                {'info': 'bet', 'player': 'steven', 'stake': 40, 'bet': 'CALL'},
                {'info': 'next_bet_round'},
                {'info': 'bet', 'player': 'stefan', 'stake': 40, 'bet': 'RAISE'},
                {'info': 'bet', 'player': 'steven', 'stake': 40, 'bet': 'CALL'},
                ]}

    def test_for_preflop(self):
        self.assertEqual(0, get_pot(self.document, 0))
        self.assertEqual(0, get_pot(self.document, 1))
        self.assertEqual(0, get_pot(self.document, 2))
        self.assertEqual(0, get_pot(self.document, 3))
        self.assertEqual(0, get_pot(self.document, 4))

        self.assertEqual(10, get_stake_for_player(self.document, 'stefan', 0))

        self.assertEqual(0, get_stake_for_player(self.document, 'steven', 0))
        self.assertEqual(0, get_stake_for_player(self.document, 'steven', 1))
        self.assertEqual(20, get_stake_for_player(self.document, 'steven', 2))
        self.assertEqual(20, get_stake_for_player(self.document, 'steven', 3))
        self.assertEqual(40, get_stake_for_player(self.document, 'steven', 4))

    def test_for_flop(self):
        self.assertEqual(100, get_pot(self.document, 5))
        self.assertEqual(100, get_pot(self.document, 6))
        self.assertEqual(100, get_pot(self.document, 7))

        self.assertEqual(0, get_stake_for_player(self.document, 'steven', 5))
        self.assertEqual(0, get_stake_for_player(self.document, 'steven', 6))
        self.assertEqual(20, get_stake_for_player(self.document, 'steven', 7))


    def test_for_turn(self):
        self.assertEqual(140, get_pot(self.document, 8))
        self.assertEqual(140, get_pot(self.document, 9))
        self.assertEqual(140, get_pot(self.document, 10))

        self.assertEqual(0, get_stake_for_player(self.document, 'steven', 8))
        self.assertEqual(0, get_stake_for_player(self.document, 'steven', 9))
        self.assertEqual(40, get_stake_for_player(self.document, 'steven', 10))

    def test_for_river(self):
        self.assertEqual(220, get_pot(self.document, 11))
        self.assertEqual(220, get_pot(self.document, 12))
        self.assertEqual(220, get_pot(self.document, 13))

        self.assertEqual(0, get_stake_for_player(self.document, 'steven', 11))
        self.assertEqual(0, get_stake_for_player(self.document, 'steven', 12))
        self.assertEqual(40, get_stake_for_player(self.document, 'steven', 13))
