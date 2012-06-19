from sqlalchemy import create_engine, MetaData, Column, Table, String,\
    Integer, ForeignKey, select, and_, desc, func
from sqlalchemy.exc import IntegrityError
import couchdb
import itertools
import json
from startuppoker_spectator.move import Move

TYPE_BET = 'bet'
TYPE_INFO = 'next_bet_round'
# change 'bet' to 'move' in later versions
MOVE = 'bet'
STAKE = 'stake'

def create_meta():
    engine = create_engine('sqlite:///startuppoker.sqlite')
    meta = MetaData()
    meta.bind = engine
    return meta

def create_db(meta):
    Table('game', meta,
        Column('id', String(64), primary_key = True),
        Column('tournament_id', String(16), nullable = False),
        Column('community_cards', String(19)),
        Column('final_pot', Integer, nullable = False),
    )
    Table('player', meta,
        Column('id', Integer, primary_key = True),
        Column('name', String(32), nullable = False),
    )
    Table('history', meta,
            Column('game_id', ForeignKey('game.id')),
            Column('index', Integer, nullable = False),
            Column('type', String(4), nullable = False),
            Column('player_id', ForeignKey('player.id')),
            Column('action', String(8), nullable = False),
            Column('stake', Integer, nullable = False),
    )
    Table('winner', meta,
            Column('game_id', ForeignKey('game.id')),
            Column('player_id', ForeignKey('player.id')),
            Column('hand', String(19), nullable = False),
    )
    Table('player_at_game', meta,
            Column('game_id', ForeignKey('game.id')),
            Column('player_id', ForeignKey('player.id')),
            Column('pocket_cards', String(19)),
            Column('seat', Integer, nullable = False),
    )

    meta.drop_all()
    meta.create_all()

def migrate_game(meta, tournament_name, document, game_id):
    pot = document['pot_share']
    game_table = Table('game', meta, autoload=True)
    game_table.insert().execute(id=game_id,
            tournament_id=tournament_name,
            community_cards=json.dumps(document['communitycards']),
            final_pot=pot)

def migrate_players(meta, document, game_id):
    players = document['players']
    insert = [{'id': name.__hash__(), 'name': name} for name in players]
    player_table = Table('player', meta, autoload=True)
    try:
        player_table.insert().execute(insert)
    except IntegrityError:
        pass # expected
    player_at_game_table = Table('player_at_game', meta, autoload=True)
    count = itertools.count(0)
    insert = [{
                'game_id': game_id,
                'player_id': player.__hash__(),
                'pocket_cards': json.dumps(document['pocketcards'][player]),
                'seat': count.next(),
            } for player in players]
    player_at_game_table.insert().execute(insert)

def migrate_winners(meta, document, game_id):
    winners  = document['winners']
    winners_hands = document['winners_hands']
    winners_table = Table('winner', meta, autoload=True)
    insert = [
                {
                    'game_id': game_id,
                    'player_id': player.__hash__(),
                    'hand': json.dumps(hand)
                } for player, hand in zip(winners, winners_hands)]
    winners_table.insert().execute(insert)

def migrate_history(meta, document, game_id):
    history_table = Table('history', meta, autoload=True)
    count = itertools.count(0)
    insert = []
    history = document['history']
    for action in history:
        type = action['info']
        if type == 'bet':
            insert.append({
                'game_id': game_id,
                'index': count.next(),
                'type': type,
                'player_id': action['player'].__hash__(),
                'action': action['bet'],
                'stake': action['stake']})
        else:
            insert.append({
                'game_id': game_id,
                'index': count.next(),
                'type': type,
                'player_id': '',
                'action': '',
                'stake': 0})
    history_table.insert().execute(insert)

def migrate_document(meta, tournament_name, document):
    game_id = document['_id']
    migrate_game(meta, tournament_name, document, game_id)
    migrate_players(meta, document, game_id)
    migrate_winners(meta, document, game_id)
    migrate_history(meta, document, game_id)
    document['pocketcards']

def migrate_couchdb(tournament_name, limit):
    meta = create_meta()
    create_db(meta)
    server = couchdb.Server('http://localhost:8778')
    couch_db = server[tournament_name]
    rows = couch_db.view('_all_docs', None, descending=True, limit=limit)
    for row in rows:
        document = couch_db[row.key]
        migrate_document(meta, tournament_name, document)
    meta.bind.dispose()

class History(object):

    def __init__(self, meta, game_id):
        self.meta = meta
        self.game_id = game_id
        self.game_table = Table('game', self.meta, autoload=True)
        self.player_table = Table('player', self.meta, autoload=True)
        self.winner_table = Table('winner', self.meta, autoload=True)
        self.history_table = Table('history', self.meta, autoload=True)
        self.history = select([self.history_table],
                self.history_table.c.game_id == self.game_id).\
                        execute().fetchall()
        self.player_at_game_table = Table('player_at_game', self.meta, autoload=True)
        self.player_at_game = select(
                    [self.player_table.c.name,
                     self.player_at_game_table.c.pocket_cards],
                    self.player_at_game_table.c.game_id == self.game_id,
                    from_obj=[self.player_at_game_table.join(self.player_table)],
                    order_by=self.player_at_game_table.c.seat).\
                            execute().fetchall()
        self.game = self.game_table.select().\
                where(self.game_table.c.id == self.game_id).\
                execute().fetchone()

def _create_id(tournament_name, table, hand):
    def fill_with_zeros(string, index, zero_count):
        return ':'.join([string, index.zfill(zero_count)])

    table_name = '-'.join([tournament_name, str(table)])
    return fill_with_zeros(table_name, str(hand), 10)

def get_history_by_id(tournament_name, game_id):
    return History(create_meta(), game_id)

def get_history(tournament_name, table, hand):
    game_id = _create_id(tournament_name, table, hand)
    return get_history_by_id(tournament_name, game_id)

def get_pot_share(history):
    return history.game['final_pot']

def get_last_games(tournament_name):
    meta = create_meta()
    game_table = Table('game', meta, autoload=True)
    query = select(
            [game_table.c.id], limit=10).\
                    order_by(desc(game_table.c.id))
    result = query.execute().fetchall()
    result = [id[0] for id in result]
    result.reverse()
    return result

def get_number_of_actions(history):
    return len(history.history)

def get_player_names(history):
    return [row[0] for row in history.player_at_game]

def get_winners(history):
    winner_table = Table('winner',
            history.meta, autoload=True)
    query = select(
                [history.player_table.c.name],
                winner_table.c.game_id == history.game_id,
                from_obj=[winner_table.join(history.player_table)],)
    result = query.execute().fetchall()
    return [row[0] for row in result]

def get_community_cards(history):
    return json.loads(history.game['community_cards'])

def get_pocket_cards(history):
    return dict((name, json.loads(hand)) for (name, hand) in history.player_at_game)

def get_action(history, step):
    query  = select(
        [history.player_table.c.name,
            history.history_table.c.type,
            history.history_table.c.stake,
            history.history_table.c.action,],
        and_(
          history.history_table.c.game_id == history.game_id,
          history.history_table.c.index == step),
        from_obj=[history.history_table.join(history.player_table)])
    result = query.execute().fetchone()
    if result:
        return {'player': result[0], 'info': result[1], 'stake': result[2], 'bet': result[3]}
    else:
        return {'player': '', 'info': TYPE_INFO, 'stake': 0, 'bet': ''}


def is_for_player(action, player_name):
    return action['player'] == player_name

def is_bet(action):
    return action['info'] == 'bet'

def _get_move(action):
    return action[MOVE]

def get_stake(action):
    return action[STAKE]

def _get_type(action):
    return action['info']


def _is_type(action, action_type):
    return _get_type(action) == action_type


def is_bet(action):
    return _is_type(action, TYPE_BET)


def _is_info(action):
    return _is_type(action, TYPE_INFO)

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
        if _is_info(get_action(document, i)):
            bet_round += 1
    return bet_round


def get_last_move(player_name, document, index):
    def get_next_move_for_player(player_name, document, index):
        while index >= 0:
            action = get_action(document, index)
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
    return move, get_stake(get_action(document, index))
if __name__ == '__main__':
    migrate_couchdb('test', 100)

