"""Script executed by Apache via mod_wsgi to create the application.
Environment variables aren't passed via Apache so we fake them here. This gives
us the advantage, however, of being able to make changes to the application
simply by editing this file in place (Apache will automatically re-load the code
if it sees the wsgi file has been edited)."""

import sys
import os

sys.path.insert(0, '/usr/local/adnxs/data-governor/current')

from config.settings import NEW_RELIC_ON, GOVERNOR_ENV
if NEW_RELIC_ON:
    import newrelic.agent
    newrelic.agent.initialize('/usr/local/adnxs/data-governor/current/newrelic.ini',GOVERNOR_ENV)

def application(environ, start_response):
    """Return the WSGI application object"""
    from runserver import get_application
    app = get_application()
    return app(environ, start_response)
