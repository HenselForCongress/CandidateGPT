# mastermind/__init__.py
import os
from flask import Flask
from .utils import configure_logger, logger
from .backend import api_bp
from web.app import web_bp


def begin_era():
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, static_folder="../web/static", template_folder="../web/templates")

    # Add stuff from jack repo eventually

    configure_logger()

    # Register Blueprints
    app.register_blueprint(api_bp)
    app.register_blueprint(web_bp, url_prefix='/')


    return app
