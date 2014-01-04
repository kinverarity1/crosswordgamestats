'''
Crossword Game Stats Google App Engine handlers and models.
'''

import datetime
import json
import logging
import os
try:
    import cPickle as pickle
except ImportError:
    import pickle
import string
import sys
import traceback

import jinja2
from google.appengine.api import images
from google.appengine.api import users
from google.appengine.ext import blobstore
from google.appengine.ext import db
from google.appengine.ext.webapp import blobstore_handlers
import webapp2

import gae
import game


path = os.path.join(os.path.dirname(__file__), 'html')
jinja_environment = jinja2.Environment(
        loader=jinja2.FileSystemLoader(path))


class JinjaBunch(dict):
    def __init__(self, **kws):
        dict = self.__dict__
        self.update(kws)

    
class RequestHandler(webapp2.RequestHandler):
    def __init__(self, *args, **kwargs):
        webapp2.RequestHandler.__init__(self, *args, **kwargs)
        self.debug = ''

    def log(self, msg):
        self.debug += '\n' + str(msg)

    def finish_render(self, template_name, **kwargs):
        self.response.headers['Context-Type'] = 'text/html'
        template_values = {'debug': self.debug,
                           'title': ''}
        user = users.get_current_user()
        if user:
            template_values.update({
                    'nickname': user.nickname(),
                    'email': user.email(),
                    'logout_url': users.create_logout_url('/')
                    })
        template_values.update(kwargs)
        template = jinja_environment.get_template(template_name)
        self.response.out.write(template.render(template_values))


class SignIn(RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            self.redirect('/app')
        else:
            self.finish_render(
                    'signin.html', title='Crossword Game Stats',
                    signin_url=users.create_login_url('/app'))
        
    
class Home(RequestHandler):
    '''Handler for the main page.'''
    def get(self):
        user = users.get_current_user()
        q = gae.GAEGame.all()
        q.filter('uploader_id =', user.user_id())
        q.filter('trashed = ', False)
        games = q.run(batch_size=1000)
        games2 = []
        for game in games:
            if 'pip' in game.players:
                games2.append(game)
        #self.log(str(type(games)).replace('>', '&gt;').replace('<', '&lt;'))
        self.finish_render('index.html', title='List of games', games=games2,
                           trash_or_delete='Move to Trash')


class ExportJSON(RequestHandler):
    '''Export games as JSON'''
    def get(self):
        user = users.get_current_user()
        q = gae.GAEGame.all()
        q.filter('uploader_id =', user.user_id())
        q.filter('trashed =', False)
        games = q.run(batch_size=1000)
        data = []

        def escape(string, chars='[]{}'):
            for char in chars:
                string = string.replace(char, chr(92) + char)
            return string

        for game in games:
            gdata = {'type': 'single_game_JSON',
                     'data': game.json_serialisation}
            data.append(gdata)
        self.response.headers['Context-Type'] = 'text/html'
        self.response.out.write(json.dumps(data, indent=2))


class Move(JinjaBunch):
    @property
    def _t_bonuses(self):
        return ''

    @property
    def _t_total_score(self):
        return ''
        

class ShowGame(RequestHandler):
    '''
    Handler to show progress of a game.
    '''
    def get(self):
        key = self.request.get('key')
        gae_game = db.get(key)
        if gae_game is None:
            self.redirect('/app')
        else:
            g = gae_game.get_game()
            if 'date_played' in g._metadata:
                try: 
                    dts = g._metadata['date_played'].strftime('%Y-%m-%d %H:%M')
                except:
                    dts = g._metadata['date_played']
                title = 'Game played on %s' % dts
            else:
                title = 'Game'

            moves = []
            for i, move in enumerate(g._moves):
                m = Move(move_number=i, **move)
                m.total_score = sum([mi['score'] for mi in g._moves[:i + 1] if mi['player'] == move['player']])
                moves.append(m)

            self.finish_render('game.html', title=title, moves=moves)


class Import(RequestHandler):
    def get(self):
        user = users.get_current_user()
        if 'import_batch' in self.request.arguments():
            import_batch = self.request.get('import_batch')
            q = gae.GAEGame.all()
            q.filter('uploader_id = ', user.user_id())
            q.filter('import_batch = ', import_batch)
            games = q.run(batch_size=1000)
            self.finish_render('index.html', title='Imported at %s' % import_batch,
                               games=games)
        else:
            import_batches = {}
            q = gae.GAEGame.all()
            q.filter('uploader_id = ', user.user_id())
            games = q.run(batch_size=1000)
            for gae_game in games:
                ib = gae_game.import_batch
                if ib not in import_batches:
                    import_batches[ib] = 1
                else:
                    import_batches[ib] += 1

            ib_jinja = []
            for dt, count in import_batches.items():
                ib_jinja.append(JinjaBunch(dt=dt, count=count))
            self.finish_render('import.html', title='Import game', import_batches=ib_jinja)
                
    def post(self):
        # Check the user has credentials to add a game:
        user = users.get_current_user()

        import_batch = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        format = self.request.get('format')
        text = self.request.get('text')

        if format != 'export_JSON':
            text = json.dumps([{'type': format, 'data': text}])

        try:
            data_object = json.loads(text)
            for i, game_object in enumerate(data_object):
                try:
                    g = game.Game(**{game_object['type'] + '_txt': game_object['data']})
                    gae_game = gae.GAEGame(uploader_id=user.user_id(), import_batch=import_batch)
                    gae_game.set_game(g)
                except:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    # self.log('Error importing game: \n%s' % ''.join(traceback.format_tb(exc_traceback)))
                    self.log('Error importing game #%d' % i)
                else:
                    gae_game.put()
            q = gae.GAEGame.all()
            q.filter('uploader_id =', user.user_id())
            q.filter('import_batch = ', import_batch)
            games = q.run(batch_size=1000)
            self.finish_render('index.html', title='Finished importing games', games=games)
        except:
            self.finish_render('index.html', title='Error importing games', debug=''.join(traceback.format_tb(exc_traceback)))


class Trash(RequestHandler):
    def get(self):
        user = users.get_current_user()
        q = gae.GAEGame.all()
        q.filter('uploader_id =', user.user_id())
        q.filter('trashed =', True)
        games = q.run(batch_size=1000)
        self.finish_render('trash.html', title='Trash', games=games)

        
class MoveToTrash(RequestHandler):
    def get(self):
        user = users.get_current_user()
        key = self.request.get('key')
        gae_game = db.get(key)
        gae_game.trashed = True
        gae_game.put()
        self.redirect('/app')
 
 
class Delete(RequestHandler):
    def get(self):
        user = users.get_current_user()
        key = self.request.get('key')
        gae_game = db.get(key)
        db.delete(key)
        self.redirect('/app')


class Restore(RequestHandler):
    def get(self):
        user = users.get_current_user()
        key = self.request.get('key')
        gae_game = db.get(key)
        gae_game.trashed = False
        gae_game.put()
        self.redirect('/app/trash')


class RefreshAllGames(RequestHandler):
    def get(self):
        user = users.get_current_user()
        q = gae.GAEGame.all()
        q.filter('uploader_id =', user.user_id())
        games = q.run(batch_size=1000)
        for gae_game in games:
            g = gae_game.get_game()
            gae_game.delete()
            
            gae_game_new = gae.GAEGame(uploader_id=user.user_id())
            gae_game_new.set_game(g)
            gae_game_new.put()
            
        self.redirect('/')


class Settings(RequestHandler):
    def get(self):
        user_id = users.get_current_user()
        self.finish_render('settings.html', title='Settings')

    def post(self):
        # Check the user has credentials to add a game:
        user = users.get_current_user()
        
        self.redirect('/app')


class Photos(RequestHandler):
    def get(self):
        user = users.get_current_user()
        q = gae.Photograph.all()
        q.filter('uploader_id =', user.user_id())
        photos = q.run(batch_size=1000)
        
        photos_jinja = []
        for photo in photos:
            pj = JinjaBunch()
            pj.thumb_url = images.get_serving_url(photo.blob_key, size=250)
            pj.date_uploaded = photo.date_uploaded
            photos_jinja.append(pj)
        self.finish_render('photos.html', title='Photographs', photos=photos_jinja)


class AddPhoto(RequestHandler):
    def get(self):
        user_id = users.get_current_user()
        upload_url = blobstore.create_upload_url('/app/photos/upload')
        self.finish_render('photos-add.html', title='Upload photograph of board', upload_url=upload_url)


class PhotoUploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        user = users.get_current_user()
        photo = gae.Photograph()
        photo.blob_key = self.get_uploads('file')[0]
        photo.game_key = None
        photo.date_modified = datetime.datetime.now()
        photo.date_uploaded = datetime.datetime.now()
        photo.uploader_id = user.user_id()
        db.put(photo)
        self.redirect('/app/photos')
        

app = webapp2.WSGIApplication(
        [('/', SignIn),
         ('/app', Home),
         ('/app/game', ShowGame),
         ('/app/import', Import),
         ('/app/export/json', ExportJSON),
         ('/app/trash', Trash),
         ('/app/movetotrash', MoveToTrash),
         ('/app/delete', Delete),
         ('/app/restore', Restore),
         ('/app/refresh', RefreshAllGames),
         ('/app/settings', Settings),
         ('/app/photos', Photos),
         ('/app/photos/add', AddPhoto),
         ('/app/photos/upload', PhotoUploadHandler)
         ], debug=True)
        
        