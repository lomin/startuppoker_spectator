# -*- coding: utf-8 -*-
"""
    Access of a startuppoker history via CouchDB

    :copyright: (c) 2011 by it-agile GmbH
    :license: BSD, see LICENSE for more details.
"""

import couchdb
from startuppoker_spectator.move import Move

TYPE_BET = 'bet'
TYPE_INFO = 'next_bet_round'
# change 'bet' to 'move' in later versions
MOVE = 'bet'
STAKE = 'stake'

try:
    from local_settings import DATABASE_HOST, DATABASE_PORT
    COUCHDB_URL = '%s:%s/' % (DATABASE_HOST, DATABASE_PORT)
    server = couchdb.Server(COUCHDB_URL)
except ImportError:
    server = couchdb.Server()


def create_id(server_name, table, hand):
    def fill_with_zeros(string, index, zero_count):
        return ':'.join([string, index.zfill(zero_count)])

    table_name = '-'.join([server_name, str(table)])
    return fill_with_zeros(table_name, str(hand), 10)


def get_history(server_name, table, hand):
    db = server[server_name]
    document_id = create_id(server_name, table, hand)
    return db[document_id]


def get_pot_share(document):
    return document['pot_share']


def get_player_names(document):
    return document['players']


def get_winners(document):
    return document['winners']


def get_pocket_cards(document):
    return document['pocketcards']


def get_community_cards(document):
    return document['communitycards']


def get_move(action):
    return action[MOVE]


def get_stake(action):
    return action[STAKE]


def get_type(action):
    return action['info']


def is_type(action, action_type):
    return get_type(action) == action_type


def is_for_player(action, player_name):
    return action['player'] == player_name


def is_bet(action):
    return is_type(action, TYPE_BET)


def is_info(action):
    return is_type(action, TYPE_INFO)


def get_actions(document):
    return document['history']


def get_number_of_actions(document):
    return len(get_actions(document))


def get_action(document, step):
    return get_actions(document)[step]


def get_stake_for_player(document, player_name, index):
    pot = 0
    while index >= 0:
        action = get_action(document, index)
        if is_bet(action):
            if is_for_player(action, player_name):
                pot += get_stake(action)
        else:
            return pot
        index -= 1
    return pot


def get_pot(document, step):
    pot = 0
    pot_for_current_bet_round = 0
    for i in range(0, step + 1):
        action = get_action(document, i)
        if is_bet(action):
            pot_for_current_bet_round += get_stake(action)
        else:
            pot += pot_for_current_bet_round
            pot_for_current_bet_round = 0
    return pot


def get_bet_round(document, step):
    bet_round = 0
    for i in range(0, step + 1):
        if is_info(get_action(document, i)):
            bet_round += 1
    return bet_round


def get_last_move(player_name, document, index):
    def get_next_move_for_player(player_name, document, index):
        while index >= 0:
            action = get_action(document, index)
            if is_bet(action):
                if is_for_player(action, player_name):
                    return get_move(action), index
            else:
                return Move.NONE, index
            index -= 1
        return '', index

    def regular_bet_or_fold(player_name, document, index):
        move, index = get_next_move_for_player(player_name, document, index)
        if move == Move.NONE or index < 0:
            return Move.FOLD, ''
        else:
            return '', ''

    move, index = get_next_move_for_player(player_name, document, index)
    if index < 0:
        return '', ''
    if move == Move.NONE:
        return regular_bet_or_fold(player_name, document, index - 1)
    if move == Move.FOLD:
        return Move.FOLD, ''
    return move, get_stake(get_action(document, index))
