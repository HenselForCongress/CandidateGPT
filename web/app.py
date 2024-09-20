# web/app.py
from flask import Blueprint, render_template, request, redirect, url_for
from mastermind.utils import logger
from flask_login import current_user, login_required



web_bp = Blueprint('web_bp', __name__)

@web_bp.route('/')
def index():
    """Render the main page."""
    logger.info("🎵 It's a perfect night, the user's visiting the main page.")
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error("💔 Oops, something went wrong while rendering the main page: %s", e)
        return "An error occurred", 500

@web_bp.route('/chat')
@login_required
def chat():
    """Render the main page."""
    logger.info("🎵 It's a perfect night, the user's visiting the chat page.")
    try:
        return render_template('chat.html')
    except Exception as e:
        logger.error("💔 Oops, something went wrong while rendering the main page: %s", e)
        return "An error occurred", 500

@web_bp.route('/about')
def about():
    """Render the about page."""
    logger.info("☕ Look what you made me do, the user is curious about us.")
    try:
        return render_template('about.html')
    except Exception as e:
        logger.error("💔 Oops, something went wrong while rendering the about page: %s", e)
        return "An error occurred", 500

# Error handler for 404
@web_bp.app_errorhandler(404)
def page_not_found(e):
    logger.warning(f"404 Error: {e}")
    return render_template('404.html'), 404

# Error handler for 403
@web_bp.app_errorhandler(403)
def page_not_found(e):
    logger.warning(f"403 Error: {e}")
    return render_template('403.html'), 403

# Debug Route
@web_bp.route('/debug')
def debug():
    return {key: value for key, value in request.headers.items()}

# Test Route
@web_bp.route('/test')
def test():
    """Render the about page."""
    logger.info("☕ Look what you made me do, the user is curious about us.")
    try:
        return render_template('test.html')
    except Exception as e:
        logger.error("💔 Oops, something went wrong while rendering the about page: %s", e)
        return "An error occurred", 500
