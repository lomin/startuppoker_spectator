# -*- coding: utf-8 -*-
"""
    Access of a startuppoker history via CouchDB

    :copyright: (c) 2011 by it-agile GmbH
    :license: BSD, see LICENSE for more details.
"""

import couchdb
from startuppoker_spectator.util import create_id

try:
    from local_settings import DATABASE_HOST, DATABASE_PORT
    COUCHDB_URL = '%s:%s/' % (DATABASE_HOST, DATABASE_PORT)
    server = couchdb.Server(COUCHDB_URL)
except ImportError:
    server = couchdb.Server()

def _get_actions(document):
    return document['history']

def get_history(server_name, table, hand):
    db = server[server_name]
    document_id = create_id(server_name, table, hand)
    return db[document_id]

def get_history_by_id(server_name, document_id):
    db = server[server_name]
    return db[document_id]

def get_last_games(tournament_name):
    db = server[tournament_name]
    rows = db.view('_all_docs', None, descending=True, limit=10)
    result = [r.key for r in rows]
    result.reverse()
    return result

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

def get_number_of_actions(document):
    return len(_get_actions(document))

def get_action(document, step):
    return _get_actions(document)[step]
