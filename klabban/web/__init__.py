import optparse
import ast
from flask import Flask

from . import views
from .. import models
from . import redis_rq

from .utils.error_handling import init_error_handling
from .utils import acl
from dotenv import dotenv_values
from . import oauth2
from . import caches

app = Flask(__name__)


def create_app():
    app.config.from_object("klabban.default_settings")
    app.config.from_envvar("KLABBAN_SETTINGS", silent=True)

    config = dotenv_values(".env")
    for k, v in config.items():
        if "CLIENT_KWARGS" in k:
            # convert string to dict
            config[k] = ast.literal_eval(v)

        if v.lower() == "true":
            config[k] = True
        elif v.lower() == "false":
            config[k] = False

    app.config.update(config)

    views.register_blueprint(app)
    caches.init_cache(app)
    models.init_db(app)
    acl.init_acl(app)
    redis_rq.init_rq(app)
    oauth2.init_oauth(app)
    init_error_handling(app)

    return app


def get_program_options(default_host="127.0.0.1", default_port="8080"):
    """
    Takes a flask.Flask instance and runs it. Parses
    command-line flags to configure the app.
    """

    # Set up the command-line options
    parser = optparse.OptionParser()
    parser.add_option(
        "-H",
        "--host",
        help="Hostname of the Flask app " + "[default %s]" % default_host,
        default=default_host,
    )
    parser.add_option(
        "-P",
        "--port",
        help="Port for the Flask app " + "[default %s]" % default_port,
        default=default_port,
    )

    # Two options useful for debugging purposes, but
    # a bit dangerous so not exposed in the help message.
    parser.add_option(
        "-c", "--config", dest="config", help=optparse.SUPPRESS_HELP, default=None
    )
    parser.add_option(
        "-d", "--debug", action="store_true", dest="debug", help=optparse.SUPPRESS_HELP
    )
    parser.add_option(
        "-p",
        "--profile",
        action="store_true",
        dest="profile",
        help=optparse.SUPPRESS_HELP,
    )

    options, _ = parser.parse_args()

    # If the user selects the profiling option, then we need
    # to do a little extra setup
    if options.profile:
        from werkzeug.middleware.profiler import ProfilerMiddleware

        app.config["PROFILE"] = True
        app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])
        options.debug = True

    return options
