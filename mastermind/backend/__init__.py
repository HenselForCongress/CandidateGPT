# mastermind/backend/__init__.py
from flask import Blueprint, request, jsonify
import requests
import yaml
from dotenv import load_dotenv
from mastermind.data_manager.load import load_data
from mastermind.ai_model import generate_response

load_dotenv()

api_bp = Blueprint('api_bp', __name__)
data = load_data()

# Load configurations from config.yml
def load_config():
    with open("config.yml", 'r') as config_file:
        config = yaml.safe_load(config_file)
    return config

config = load_config()

@api_bp.route('/api/ask', methods=['POST'])
def ask_question():
    """Handle the question from the user and return an answer."""
    user_question = request.json.get('question')
    response_type = request.json.get('response_type')

    # Find the appropriate prompt suffix based on response type
    response_prompt = next((option['prompt'] for option in config['options']['response'] if option['name'] == response_type), "")

    # Append the suffix to the prompt
    full_prompt = f"{user_question} {response_prompt}"
    response = generate_response(full_prompt, data, config)
    return jsonify(response)

@api_bp.route('/api/reload-config')
def reload_config():
    """Reload the configuration from config.yml"""
    global config
    config = load_config()
    return jsonify({'message': 'Configuration reloaded successfully.'})

@api_bp.route('/api/reload-data')
def reload_data():
    """Reload the data from the data directory"""
    global data
    data = load_data()
    return jsonify({'message': 'Data reloaded successfully.'})

@api_bp.route('/api/response-types')
def get_response_types():
    """Get the list of response types from the configuration"""
    response_types = [option['name'] for option in config['options']['response']]
    return jsonify({'response_types': response_types})
