# mastermind/backend/__init__.py
from flask import Blueprint, request, jsonify
import yaml
#from dotenv import load_dotenv
from mastermind.data_manager.load import load_data
from mastermind.ai_model import generate_response
from mastermind import logger

# load_dotenv()

# Initialize Blueprint
api_bp = Blueprint('api_bp', __name__)

logger.debug("Loading initial data.")
data = load_data()

# Load configurations from config.yml
def load_config():
    logger.info("Loading configuration from config.yml.")
    try:
        with open("config.yml", 'r') as config_file:
            config = yaml.safe_load(config_file)
        logger.debug("Configuration loaded successfully.")
        return config
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        raise

config = load_config()

@api_bp.route('/api/ask', methods=['POST'])
def ask_question():
    """Handle the question from the user and return an answer."""
    user_question = request.json.get('question')
    response_type = request.json.get('response_type')

    logger.debug(f"Received question: {user_question} with response type: {response_type}")

    response_option = next((option for option in config['options']['response'] if option['name'] == response_type), None)
    response_prompt = response_option['prompt'] if response_option else ""

    full_prompt = f"{user_question} {response_prompt}"
    logger.info(f"Full prompt generated: {full_prompt}")

    try:
        response = generate_response(full_prompt, data, config)
        logger.info(f"Response generated successfully for question: {user_question}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return jsonify({'error': 'Failed to generate response.'}), 500

@api_bp.route('/api/reload-config')
def reload_config():
    """Reload the configuration from config.yml"""
    global config
    try:
        config = load_config()
        logger.info("Configuration reloaded successfully.")
        return jsonify({'message': 'Configuration reloaded successfully.'})
    except Exception as e:
        logger.error(f"Failed to reload configuration: {e}")
        return jsonify({'error': 'Failed to reload configuration.'}), 500

@api_bp.route('/api/reload-data')
def reload_data():
    """Reload the data from the data directory"""
    global data
    try:
        data = load_data()
        logger.info("Data reloaded successfully.")
        return jsonify({'message': 'Data reloaded successfully.'})
    except Exception as e:
        logger.error(f"Failed to reload data: {e}")
        return jsonify({'error': 'Failed to reload data.'}), 500

@api_bp.route('/api/response-types')
def get_response_types():
    """Get the list of response types from the configuration"""
    try:
        response_types = [
            {
                'name': option['name'],
                'about': option.get('about', ''),
            }
            for option in config['options']['response']
        ]
        logger.info("Response types retrieved successfully.")
        return jsonify({'response_types': response_types})
    except Exception as e:
        logger.error(f"Failed to retrieve response types: {e}")
        return jsonify({'error': 'Failed to retrieve response types.'}), 500
