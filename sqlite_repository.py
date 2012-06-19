from sqlalchemy import create_engine, MetaData, Column, Table, String,\
    Integer, ForeignKey, select, and_
from sqlalchemy.exc import IntegrityError
import couchdb
import itertools
import json

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
    game_table = Table('game', history.meta, autoload=True)
    query = game_table.select(). where(game_table.c.id == history.game_id)
    game = query.execute().fetchone()
    return game['final_pot']

def get_last_games(tournament_name):
    pass

def get_number_of_actions(history):
    pass

def get_last_move(player_name, history, step):
    pass

def get_stake_for_player(history, player_name, step):
    pass

def get_pot(history, step):
    pass

def get_bet_round(history, step):
    pass

class Player(object):

    def __init__(self, name, seat):
        self.name = name
        self.seat = seat

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

def _get_player_table(history):
    return Table('player',
            history.meta, autoload=True)

def get_player_names(history):
    player_table = _get_player_table(history)
    player_at_game_table = Table('player_at_game',
            history.meta, autoload=True)
    query = select(
                [player_table.c.name],
                player_at_game_table.c.game_id == history.game_id,
                from_obj=[player_at_game_table.join(player_table)],
                order_by=player_at_game_table.c.seat)
    result = query.execute().fetchall()
    return [row[0] for row in result]

def get_winners(history):
    winner_table = Table('winner',
            history.meta, autoload=True)
    player_table = _get_player_table(history)
    query = select(
                [player_table.c.name],
                winner_table.c.game_id == history.game_id,
                from_obj=[winner_table.join(player_table)],)
    result = query.execute().fetchall()
    return [row[0] for row in result]

def get_community_cards(history):
    game_table = Table('game', history.meta, autoload=True)
    query = game_table.select(). where(game_table.c.id == history.game_id)
    game = query.execute().fetchone()
    return json.loads(game['community_cards'])

def get_pocket_cards(history):
    player_table = _get_player_table(history)
    player_at_game_table = Table('player_at_game',
            history.meta, autoload=True)
    query  = select(
        [player_table.c.name, player_at_game_table.c.pocket_cards],
        player_at_game_table.c.game_id == history.game_id,
        from_obj=[player_at_game_table.join(player_table)],)
    result = query.execute().fetchall()
    return dict((name, json.loads(hand)) for (name, hand) in result)

def get_action(history, step):
    player_table = _get_player_table(history)
    history_table = Table('history', history.meta, autoload=True)
    query  = select(
        [player_table.c.name, history_table.c.type],
        and_(
          history_table.c.game_id == history.game_id,
          history_table.c.index == step),
        from_obj=[history_table.join(player_table)])
    result = query.execute().fetchone()
    return result

def is_for_player(action, player_name):
    return action[0] == player_name

def is_bet(action):
    return action[1] == 'bet'

if __name__ == '__main__':
    migrate_couchdb('test', 100)

