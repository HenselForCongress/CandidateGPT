# web/app.py
from flask import Blueprint, render_template
from mastermind.utils import logger

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

@web_bp.route('/about')
def about():
    """Render the about page."""
    logger.info("☕ Look what you made me do, the user is curious about us.")
    try:
        return render_template('about.html')
    except Exception as e:
        logger.error("💔 Oops, something went wrong while rendering the about page: %s", e)
        return "An error occurred", 500
