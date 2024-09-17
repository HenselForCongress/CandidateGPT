# mastermind/__init__.py
import os
from datetime import timedelta
from flask import Flask
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy_utils import database_exists, create_database

from web.auth import auth_bp, login_manager, limiter
from .utils import configure_logger, logger, test_logger
from .models import db, migrate

from .backend import api_bp
from web.app import web_bp
from web.admin import admin_bp



def begin_era():
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, static_folder="../web/static", template_folder="../web/templates")

    try:
        # Update database URI to use PostgreSQL
        username = os.getenv('POSTGRES_USER')
        password = os.getenv('POSTGRES_PASSWORD')
        host = os.getenv('POSTGRES_HOST')
        port = os.getenv('POSTGRES_PORT')
        database = os.getenv('POSTGRES_DATABASE')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{username}:{password}@{host}:{port}/{database}'
    except KeyError as e:
        logger.error(f"Missing environment variable: {str(e)}")
        raise

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key')

    # Addl Security stuff
    app.config['SESSION_COOKIE_SECURE'] = True  # Use HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

    # Check if the database exists and create it if it doesn't
    if not database_exists(app.config['SQLALCHEMY_DATABASE_URI']):
        create_database(app.config['SQLALCHEMY_DATABASE_URI'])
        logger.info(f"Database created at {app.config['SQLALCHEMY_DATABASE_URI']}")

    configure_logger()
    test_logger()

    # Initialize database and migration with app
    db.init_app(app)
    migrate.init_app(app, db)

    # Initialize login manager
    login_manager.init_app(app)

    # Register Blueprints
    app.register_blueprint(api_bp)
    app.register_blueprint(web_bp, url_prefix='/')
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)


    return app
