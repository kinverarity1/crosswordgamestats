import datetime

from google.appengine.ext import db, blobstore

import game


class GAEGame(db.Model):
    date_played = db.DateTimeProperty()
    date_modified = db.DateTimeProperty()
    players = db.StringListProperty()
    scores = db.ListProperty(int)
    total_score = db.IntegerProperty()
    margin = db.IntegerProperty()
    winning_player = db.StringProperty()
    board_pic = blobstore.BlobReferenceProperty()
    game_finished = db.BooleanProperty()
    json_serialisation = db.TextProperty()
    uploader_id = db.StringProperty()
    import_batch = db.StringProperty()
    player_ids = db.StringListProperty()
    move_children = db.StringListProperty()
    duplicate_game_keys = db.StringListProperty()
    tags = db.StringListProperty()
    trashed = db.BooleanProperty()
    
    @property
    def _t_scores(self):
        return ', '.join([str(s) for s in self.scores])

    @property
    def _t_players(self): 
        return ', '.join([p for p in self.players])
    
    @property
    def _t_score_summary(self):
        return ', '.join(['%s %d' % (player, score) for
                          player, score in zip(self.players, self.scores)])
                          
    @property
    def _t_date_played(self):
        return self.date_played.strftime('%Y-%m-%d %H:%M')
        
    @property
    def _t_date_modified(self):
        return self.date_modified.strftime('%Y-%m-%d %H:%M:%S')

    @property
    def _t_margin(self):
        if self.margin:
            return self.margin
        else:
            return ''

    @property
    def _t_key(self):
        return self.key()
    
    def set_game(self, g):
        '''Set up GAE object.'''
        self.date_played = g._metadata.get('date_played', None)
        self.date_modified = datetime.datetime.now()
        self.players = list(g._players)
        self.scores = [0 for player in self.players]
        for move in g._moves:
            player_index = self.players.index(move['player'])
            self.scores[player_index] += move['score']
        self.total_score = sum(self.scores)
        sorted_scores, sorted_players = zip(
                *sorted(zip(self.scores, self.players), key=lambda x: x[0]))
        self.margin = None
        if len(sorted_scores) > 1:
            self.margin = sorted_scores[-1] - sorted_scores[-2]
        self.winning_player = sorted_players[-1]
        self.trashed = False
        
        self.json_serialisation = str(g.json)
    
    def get_game(self):
        return game.Game(single_game_JSON_txt=self.json_serialisation)


class Photograph(db.Model):
    date_uploaded = db.DateTimeProperty()
    date_modified = db.DateTimeProperty()
    game_key = db.StringProperty()
    blob_key = blobstore.BlobReferenceProperty()
    uploader_id = db.StringProperty()
