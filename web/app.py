# web/app.py
from flask import Blueprint, render_template

web_bp = Blueprint('web_bp', __name__)

@web_bp.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@web_bp.route('/about')
def about():
    """Render the about page."""
    return render_template('about.html')
