# -*- coding: utf-8 -*-
"""
    Flask-App for displaying Startuppoker sessions.

    :copyright: (c) 2011 by it-agile GmbH
    :license: BSD, see LICENSE for more details.
"""

from flask import Flask, render_template, redirect, url_for
from collections import deque
from move import Move

class Card(object):

    COLORS = {'c': 'clubs', 'd': 'diamonds', 'h': 'hearts', 's': 'spades'}

    def __init__(self, card):
        separator_index = len(card) - 1
        self.rank = card[:separator_index]
        self.color = Card.COLORS[card[separator_index:]]

class Player(object):

    def __init__(self, name):
        self.name = name
        self.move = ''
        self.stake = ''
        self.cards = []
        self.dealer = ''
        self.current_player = ''

class NoPlayer(Player):

    def __init__(self):
       Player.__init__(self, '')

app = Flask(__name__)

def create_players(history):
    players = repository.get_players(history)
    return [Player(name=player) for player in players]

def create_players_list(players):
    def by_name(player):
        return player.name

    def create_sorted_players_list(players):
        sorted_players = [] + players
        sorted_players.sort(key=by_name)
        players_list = deque(players)
        while (sorted_players[0].name != players_list[0].name):
            players_list.rotate(1)
        return players_list

    def append_invisible_players(players_list):
        for i in range(len(players), 8):
            players_list.append(NoPlayer())
        return players_list

    players_list = create_sorted_players_list(players)
    return append_invisible_players(players_list)

def add_actions(players, history, step):
    for player in players:
        action, stake = repository.get_last_move(player.name, history, step)
        player.move = action


def add_stakes(players, history, step):
    for player in players:
        if player.move == Move.FOLD:
            player.stake = ''
        else:
            player.stake = repository.get_stake_for_player(history, player.name, step)

def convert_cards(cards):
    return [Card(card) for card in cards]

def get_community_cards(history, step):
    cards_to_bet_round = {0:0, 1:3, 2:4, 3:5}
    community_cards = convert_cards(repository.get_community_cards(history))
    bet_round = repository.get_bet_round(history, step)
    return community_cards[0:cards_to_bet_round[bet_round]]

def add_pocket_cards(players, history, step):
    pocket_cards = repository.get_pocket_cards(history)
    for player in players:
        player.cards = convert_cards(pocket_cards[player.name])

def add_dealer_button(players, history):
    for player in players:
        if player.name == repository.get_players(history)[2]:
            player.dealer = 'Dealer'

def add_winners(players, history):
    winners = repository.get_winners(history)
    for player in players:
        if player.name in winners:
            player.dealer = 'Winner'

def add_current_player(players, history, step):
    action = repository.get_action(history, step)
    if repository.is_bet(action):
        for player in players:
            if repository.is_for_player(action, player.name):
                player.current_player = ' currentPlayer'

def display_next_hand(server_name, table, hand):
    return redirect(url_for('show', server_name=server_name, table=table, hand=hand+1, step=0))

def display_winners(history, players, step, server_name, table, hand):
    return render_template('startuppoker.html', \
            pot=repository.get_pot_share(history), \
            players=create_players_list(players), \
            community_cards=get_community_cards(history, step - 1), \
            next=url_for('show', server_name=server_name, table=table, hand=hand, step=step+1))

def display_next_step(history, players, step, server_name, table, hand):
    return render_template('startuppoker.html', \
            pot=repository.get_pot(history, step), \
            players=create_players_list(players), \
            community_cards=get_community_cards(history, step), \
            next=url_for('show', server_name=server_name, table=table, hand=hand, step=step+1))


@app.route("/<server_name>/")
@app.route("/<server_name>/<int:table>/<int:hand>/<int:step>")
def show(server_name, table=0, hand=1, step=0):
    history = repository.get_history(server_name, table, hand)
    if step > repository.get_number_of_actions(history):
        return display_next_hand(server_name, table, hand)

    players = create_players(history)
    add_pocket_cards(players, history, step)

    if step == repository.get_number_of_actions(history):
        add_winners(players, history)
        return display_winners(history, players, step, server_name, table, hand)

    add_dealer_button(players, history)
    add_current_player(players, history, step)
    add_actions(players, history, step)
    add_stakes(players, history, step)
    return display_next_step(history, players, step, server_name, table, hand)

def start():
    return app
