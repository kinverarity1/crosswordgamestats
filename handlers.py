"""
Crossword Game Stats Google App Engine handlers and models.
"""

import os
try:
    import cPickle as pickle
except ImportError:
    import pickle
import string

import jinja2
from google.appengine.api import users
from google.appengine.ext import db, blobstore
import webapp2

import game


jinja_environment = jinja2.Environment(
        loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


class GAEGame(db.Model):
    date_played = db.DateTimeProperty()
    date_entered = db.DateTimeProperty()
    total_score = db.IntegerProperty()
    margin = db.IntegerProperty()
    players = db.StringListProperty()
    winning_player = db.StringProperty()
    board_pic = blobstore.BlobReferenceProperty()
    game_finished = db.BooleanProperty()
    json_serialisation = db.TextProperty()
    
    def set_game(self, g):
        """
        Set up GAE object.
        """
        self.json_serialisation = g.json
    
    def get_game(self):
        return game.Game(jsontxt=self.json_serialisation)
    
    
def get_html(*args, **kwargs):
    """
    Fill HTML by keywords.
    
    Args: 
        - dictionaries updated in ordered of passing, so the last have
          precedence.
    
    Kwargs:
        - keyword arguments which are the last thing used in updating the
          template.
    
    Returns:
        - string of HTML
    
    """
    fields = {"javascript_headers": "",
              "content": ""}
    for d in args:
        fields.update(d)
    fields.update(kwargs)
    html = string.Template(open("html.template", mode="r").read())
    return html.safe_substitute(**fields)
    
class RequestHandler(webapp2.RequestHandler):
    def finish_render(self, template_name, **kwargs):
        self.response.headers["Context-Type"] = "text/html"
        template_values = {"title": ""}
        user = users.get_current_user()
        if user:
            template_values.update({
                    "nickname": user.nickname(),
                    "email": user.email(),
                    "logout_url": users.create_logout_url("/")
                    })
        template_values.update(kwargs)
        template = jinja_environment.get_template(template_name)
        self.response.out.write(template.render(template_values))
    
    
class Home(RequestHandler):
    """
    Handler for the main page.
    """
    def get(self):
        self.finish_render("index.html", title="Home")

        
class Login(RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            self.redirect("/app")
        else:
            self.finish_render(
                    "login.html", title="Login to Crossword Game Stats",
                    login_url=users.create_login_url("/app"))
        
class ShowGame(RequestHandler):
    """
    Handler to show progress of a game.
    """
    def get(self):
        key = self.request.get("key")
        g = GAEGame(key).get_game()
        self.finish_render("index.html", title="Show game")


class ImportGame(RequestHandler):
    def get(self):
        self.finish_render("import.html", title="Import game")
                
    def post(self):
        # Check the user has credentials to add a game:
        user = users.get_current_user()
        
        format = self.request.get("format")
        text = self.request.get("text")
        
        # Parse the game
        if format == "json":
            g = game.Game(jsontxt=text)
        elif format == "gcg":
            g = game.Game(gcgtxt=text)
            
        # Add to datastore
        gae_game = GAEGame()
        gae_game.set_game(g)
        gae_game.put()
        
        self.redirect("/app")

        
        
app = webapp2.WSGIApplication(
        [("/", Login),
         ("/app", Home),
         ("/app/game", ShowGame),
         ("/app/import", ImportGame)
         ], debug=True)
        
        