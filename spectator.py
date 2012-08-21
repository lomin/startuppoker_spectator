# -*- coding: utf-8 -*-
"""
    Flask-app for displaying startuppoker sessions.

    :copyright: (c) 2011 by it-agile GmbH
    :license: BSD, see LICENSE for more details.
"""

from flask import Flask, render_template, redirect, url_for, jsonify
from collections import deque
from startuppoker_spectator.move import Move
from startuppoker_spectator.util import TYPE_INFO, TYPE_BET
import random

repository = None

# change 'bet' to 'move' in later versions
MOVE = 'bet'
STAKE = 'stake'

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
    players = repository.get_player_names(history)
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
        action, stake = get_last_move(player.name, history, step)
        player.move = action


def add_stakes(players, history, step):
    for player in players:
        if player.move == Move.FOLD:
            player.stake = ''
        else:
            player.stake = get_stake_for_player(history,\
                   player.name, step)


def convert_cards(cards):
    return [Card(card) for card in cards]


def get_community_cards(history, step):
    cards_to_bet_round = {0: 0, 1: 3, 2: 4, 3: 5}
    community_cards = convert_cards(repository.get_community_cards(history))
    bet_round = get_bet_round(history, step)
    return community_cards[0:cards_to_bet_round[bet_round]]


def add_pocket_cards(players, history, step):
    pocket_cards = repository.get_pocket_cards(history)
    for player in players:
        player.cards = convert_cards(pocket_cards[player.name])


def is_heads_up(players):
    return len(players) == 2


def get_dealer_name(players):
    if (is_heads_up(players)):
        return players[0]
    return players[-1]


def add_dealer_button(players, history):
    player_names = repository.get_player_names(history)
    for player in players:
        if player.name == get_dealer_name(player_names):
            player.dealer = 'Dealer'


def add_winners(players, history):
    winners = repository.get_winners(history)
    for player in players:
        if player.name in winners:
            player.dealer = 'Winner'


def is_for_player(action, player_name):
    return action['player'] == player_name

def _get_type(action):
    return action['info']

def _is_type(action, action_type):
    return _get_type(action) == action_type

def is_bet(action):
    return _is_type(action, TYPE_BET)

def get_stake(action):
    return action[STAKE]

def add_current_player(players, history, step):
    action = repository.get_action(history, step)
    if is_bet(action):
        for player in players:
            if is_for_player(action, player.name):
                player.current_player = 'currentPlayer'

def _is_info(action):
    return _is_type(action, TYPE_INFO)

def get_bet_round(document, step):
    bet_round = 0
    for i in range(0, step + 1):
        if _is_info(repository.get_action(document, i)):
            bet_round += 1
    return bet_round

def get_pot(history, step):
    pot = 0
    pot_for_current_bet_round = 0
    for i in range(0, step + 1):
        action = repository.get_action(history, i)
        if is_bet(action):
            pot_for_current_bet_round += get_stake(action)
        else:
            pot += pot_for_current_bet_round
            pot_for_current_bet_round = 0
    return pot

def get_stake_for_player(document, player_name, index):
    pot = 0
    while index >= 0:
        action = repository.get_action(document, index)
        if is_bet(action):
            if is_for_player(action, player_name):
                pot += get_stake(action)
        else:
            return pot
        index -= 1
    return pot

def _get_move(action):
    return action[MOVE]

def get_last_move(player_name, document, index):
    def get_next_move_for_player(player_name, document, index):
        while index >= 0:
            action = repository.get_action(document, index)
            if is_bet(action):
                if is_for_player(action, player_name):
                    return _get_move(action), index
            else:
                return Move.NONE, index
            index -= 1
        return '', index

    def regular_bet_or_fold(player_name, document, index):
        move, index = get_next_move_for_player(player_name, document, index)
        if move == Move.NONE or move == Move.FOLD or index < 0:
            return Move.FOLD, ''
        else:
            return '', ''

    move, index = get_next_move_for_player(player_name, document, index)
    if index < 0:
        return '', ''
    if move == Move.FOLD:
        return Move.FOLD, ''
    if move == Move.NONE:
        return regular_bet_or_fold(player_name, document, index - 1)
    return move, get_stake(repository.get_action(document, index))

def display_winners(history, players, step,
        tournament_name, create_next_link):
    return render_template('startuppoker.html',
            pot=repository.get_pot_share(history),
            players=create_players_list(players),
            community_cards=get_community_cards(history, step - 1),
            next=create_next_link())

def display_next_step(history, players, step,
        tournament_name, create_next_link):
    return render_template('startuppoker.html',
            pot=get_pot(history, step),
            players=create_players_list(players),
            community_cards=get_community_cards(history, step),
            next=create_next_link())

def show_hand(tournament_name, history, step, display_next_hand,
        create_next_link):
    if step > repository.get_number_of_actions(history):
        return display_next_hand()

    players = create_players(history)
    add_pocket_cards(players, history, step)

    if step == repository.get_number_of_actions(history):
        add_winners(players, history)
        return display_winners(history, players, step,
                tournament_name, create_next_link)

    add_dealer_button(players, history)
    add_current_player(players, history, step)
    add_actions(players, history, step)
    add_stakes(players, history, step)
    return display_next_step(history, players, step,
            tournament_name, create_next_link)


@app.route("/latest/<tournament_name>/<history_id>/<int:step>")
def show_latest(tournament_name='spiel', history_id='1', step=1):
    history = repository.get_history_by_id(tournament_name, history_id)
    return show_hand(tournament_name, history, step,
            lambda: redirect(url_for('find_and_show_latest',
                tournament_name=tournament_name, history_id=history_id)),
            lambda: url_for('show_latest', tournament_name=tournament_name,
                history_id=history_id, step=step + 1))


@app.route("/latest/<tournament_name>/")
@app.route("/latest/<tournament_name>/<history_id>")
def find_and_show_latest(tournament_name, history_id = ''):
    last_10_ids = repository.get_last_games(tournament_name)
    if history_id in last_10_ids and history_id != last_10_ids[-1]:
        index = last_10_ids.index(history_id)
        next_id = last_10_ids[index + 1]
    else:
        next_id = last_10_ids[0]
    return show_latest(tournament_name, next_id, 0)


@app.route("/<tournament_name>/")
@app.route("/<tournament_name>/<int:table>/<int:hand>/<int:step>")
def show(tournament_name, table=0, hand=1, step=0):
    history = repository.get_history(tournament_name, table, hand)
    return show_hand(tournament_name, history, step,
            lambda: redirect(url_for('show', tournament_name=tournament_name,\
            table=table, hand=hand + 1, step=0)),
            lambda: url_for('show', tournament_name=tournament_name,
                table=table, hand=hand, step=step + 1))

player_num = 10
def create_fake_standings():
    return [{'name': 'player_%s' % player, 'history':  [{'credits': 0, 'hands': 0}]} for player in range(player_num)]


all_standings = create_fake_standings()
hands = 0

@app.route("/standings/<tournament_name>.json/")
def get_standings(tournament_name):
    global hands

    hands += 1000
    standings = create_fake_standings()
    pot_sum = 0
    for index in range(player_num):
        last_credits = all_standings[index]['history'][-1]['credits']
        history = {'credits': last_credits, 'hands': hands}
        pot = 0
        if index < player_num -1:
            for i in xrange(1000):
                pot += int(random.uniform(0, 100)) - 50
            pot_sum += pot
        else:
            pot = -pot_sum
        history['credits'] = pot
        all_standings[index]['history'].append(history)
    return jsonify(standings=all_standings)
