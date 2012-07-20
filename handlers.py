import string
import webapp2


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

    
class Home(webapp2.RequestHandler):
    """
    Handler for the main page.
    """
    def get(self):
        self.response.headers["Content-Type"] = "text/html"
        self.response.out.write(get_html(
                window_title="Scrabble Stats",
                page_title="Home page"
                ))

                
app = webapp2.WSGIApplication(
        [("/", Home)
        ], debug=True)