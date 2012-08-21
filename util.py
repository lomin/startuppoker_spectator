# -*- coding: utf-8 -*-
"""
    Access of a startuppoker history via CouchDB

    :copyright: (c) 2011 by it-agile GmbH
    :license: BSD, see LICENSE for more details.
"""

TYPE_BET = 'bet'
TYPE_INFO = 'next_bet_round'

def create_id(server_name, table, hand):
    def fill_with_zeros(string, index, zero_count):
        return ':'.join([string, index.zfill(zero_count)])

    table_name = '-'.join([server_name, str(table)])
    return fill_with_zeros(table_name, str(hand), 10)

