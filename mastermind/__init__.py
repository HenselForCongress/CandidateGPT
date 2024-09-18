# mastermind/__init__.py
import os
from datetime import timedelta
from flask import Flask
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import sentry_sdk
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy import text
from werkzeug.middleware.proxy_fix import ProxyFix
import psycopg2

# Imported modules from your project
from web.auth import auth_bp, login_manager, limiter
from .utils import configure_logger, logger, test_logger
from .models import db, migrate
from web.admin import csrf
from .backend import api_bp
from web.app import web_bp
from web.admin import admin_bp

def test_db_connection():
    """Test the database connection."""
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('POSTGRES_DATABASE'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            host=os.getenv('POSTGRES_HOST'),
            port=os.getenv('POSTGRES_PORT'),
        )
        conn.close()
        logger.info("Database connection successful.")
    except Exception as e:
        logger.error(f"Error connecting to the database: {str(e)}", exc_info=True)
        raise

def begin_era():
    """Create and configure an instance of the Flask application."""
    try:
        app = Flask(__name__, static_folder="../web/static", template_folder="../web/templates")
        logger.info("Flask application instance created successfully.")
    except Exception as e:
        logger.error(f"Error creating Flask application instance: {str(e)}", exc_info=True)
        raise

    # Initialize CSRF protection
    try:
        csrf = CSRFProtect(app)
        logger.info("CSRF protection initialized.")
    except Exception as e:
        logger.error(f"Error initializing CSRF protection: {str(e)}", exc_info=True)
        raise

    try:
        # Update database URI to use PostgreSQL
        username = os.getenv('POSTGRES_USER')
        password = os.getenv('POSTGRES_PASSWORD')
        host = os.getenv('POSTGRES_HOST')
        port = os.getenv('POSTGRES_PORT')
        database = os.getenv('POSTGRES_DATABASE')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{username}:{password}@{host}:{port}/{database}'
        logger.info(f"Database URI configured: {app.config['SQLALCHEMY_DATABASE_URI']}")
    except KeyError as e:
        logger.error(f"Missing environment variable: {str(e)}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Error setting up database URI: {str(e)}", exc_info=True)
        raise

    try:
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key')
        app.config['SESSION_COOKIE_SECURE'] = False  # Temporary disable
        app.config['SESSION_COOKIE_HTTPONLY'] = True
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
        app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
        logger.info("Application configuration set up successfully.")
    except Exception as e:
        logger.error(f"Error configuring application: {str(e)}", exc_info=True)
        raise

    try:
        # Check if the database exists and create it if it doesn't
        if not database_exists(app.config['SQLALCHEMY_DATABASE_URI']):
            create_database(app.config['SQLALCHEMY_DATABASE_URI'])
            logger.info(f"Database created at {app.config['SQLALCHEMY_DATABASE_URI']}")
    except Exception as e:
        logger.error(f"Error checking/creating database: {str(e)}", exc_info=True)
        raise

    try:
        configure_logger()
        test_logger()
        logger.info("Logger configured successfully.")
    except Exception as e:
        logger.error(f"Error configuring logger: {str(e)}", exc_info=True)
        raise

    try:
        # Add ProxyFix middleware
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)
        logger.info("ProxyFix middleware added.")
    except Exception as e:
        logger.error(f"Error adding ProxyFix middleware: {str(e)}", exc_info=True)
        raise

    try:
        # Initialize database and migration with app
        db.init_app(app)
        migrate.init_app(app, db)
        logger.info("Database initialized with Flask app.")
    except Exception as e:
        logger.error(f"Error initializing database with app: {str(e)}", exc_info=True)
        raise

    try:
        # Initialize login manager
        login_manager.init_app(app)
        logger.info("Login manager initialized with app.")
    except Exception as e:
        logger.error(f"Error initializing login manager: {str(e)}", exc_info=True)
        raise

    try:
        # Initialize CSRF protection
        csrf.init_app(app)
        logger.info("CSRF protection initialized with app.")
    except Exception as e:
        logger.error(f"Error initializing CSRF protection with app: {str(e)}", exc_info=True)
        raise

    try:
        # Register Blueprints
        app.register_blueprint(api_bp)
        app.register_blueprint(web_bp, url_prefix='/')
        app.register_blueprint(auth_bp)
        app.register_blueprint(admin_bp)
        logger.info("Blueprints registered successfully.")
    except Exception as e:
        logger.error(f"Error registering blueprints: {str(e)}", exc_info=True)
        raise

    try:
        sentry_sdk.init(
            dsn=os.getenv('SENRTY_DSN'),
            traces_sample_rate=1.0,
            sample_rate=0.25,
            profiles_sample_rate=1.0,
        )
        logger.info("Sentry SDK initialized.")
    except Exception as e:
        logger.error(f"Error initializing Sentry SDK: {str(e)}", exc_info=True)
        raise

    # Test database connection
    try:
        logger.info("Testing database connection...")
        test_db_connection()
    except Exception as e:
        logger.error("Database connection test failed.", exc_info=True)
        raise

    return app
