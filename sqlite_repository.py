from sqlalchemy import create_engine, MetaData, Column, Table, String, Integer, ForeignKey
from sqlalchemy.exc import IntegrityError
import couchdb
import itertools

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
    )

    meta.drop_all()
    meta.create_all()

def migrate_game(meta, tournament_name, document, game_id):
    pot = document['pot_share']
    game_table = Table('game', meta, autoload=True)
    game_table.insert().execute(id=game_id,
            tournament_id=tournament_name,
            community_cards=document['communitycards'].__str__(),
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
    insert = [{
                'game_id': game_id,
                'player_id': player.__hash__(),
                'pocket_cards': str(document['pocketcards'][player])
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
                    'hand': hand.__str__()
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
                'player_id': action['player'],
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

def migrate_couchdb(tournament_name):
    meta = create_meta()
    create_db(meta)
    server = couchdb.Server('http://localhost:8778')
    couch_db = server[tournament_name]
    rows = couch_db.view('_all_docs', None, descending=True, limit=100000)
    for row in rows:
        document = couch_db[row.key]
        migrate_document(meta, tournament_name, document)
    meta.bind.dispose()

if __name__ == '__main__':
    migrate_couchdb('test')

