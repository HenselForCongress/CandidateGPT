# mastermind/backend/__init__.py
from flask import Blueprint, request, jsonify, abort
from flask_login import login_required, current_user
import json
import yaml
#from dotenv import load_dotenv
from mastermind.data_manager.load import load_data
from mastermind.ai_model import generate_response
from mastermind import logger
from flask_wtf.csrf import CSRFProtect
from mastermind.models import User, ResponseType, Query, UserTypeEnum, Response, db
from mastermind.utils.auth import role_required

from langfuse.decorators import langfuse_context, observe

csrf = CSRFProtect()

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
@observe(name="api_ask_endpoint")
@login_required
@role_required(UserTypeEnum.USER.name, UserTypeEnum.ADMIN.name)
def ask_question():
    logger.debug('Entered /api/ask endpoint.')
    logger.debug(f'Headers: {request.headers}')
    logger.debug(f'Request data (raw): {request.data}')
    logger.debug(f'JSON data (parsed): {request.get_json()}')

    try:
        user_question = request.json.get('question')
        response_type = request.json.get('response_type')
        showcase = request.json.get('showcase', False)

        # Get the User-ID from the logged-in user
        user_id = current_user.get_id() if current_user.is_authenticated else 'anonymous'

        response_option = next((option for option in config['options']['response'] if option['name'] == response_type), None)
        response_prompt = response_option['prompt'] if response_option else ""

        full_prompt = f"{user_question} {response_prompt}"
        logger.info(f"Full prompt generated: {full_prompt}")

        # Generate the AI response
        response_result = generate_response(full_prompt, data, config)
        response_text = response_result.get('answer', '')
        warning = response_result.get('warning', '')
        links = response_result.get('links', [])

        logger.info(f"Response generated successfully for question: {user_question}")

        # Fetch or create response type in database
        response_type_record = ResponseType.query.filter_by(name=response_type).first()
        if not response_type_record and response_option:
            response_type_record = ResponseType(name=response_option['name'], prompt=response_option['prompt'], about=response_option['about'])
            db.session.add(response_type_record)
            db.session.commit()

        # Save the response
        response_record = Response(
            response_text=response_text
        )
        db.session.add(response_record)
        db.session.commit()

        # Save the query and link the response
        query = Query(
            query_text=user_question,
            response_id=response_record.id,
            response_type_id=response_type_record.id if response_type_record else None,
            user_id=user_id,
            showcase=showcase,
            ip_address=request.remote_addr,
            settings_selected=json.dumps(config['ai']['settings'])  # Store the settings
        )
        db.session.add(query)
        db.session.commit()

        langfuse_context.update_current_observation(
            user_id=user_id,
            input={"question": user_question, "response_type": response_type},
            output={
                "answer": response_text,
                "warning": warning,
                "links": links
            },
            name="api_response_generated",
            metadata={"endpoint": "/api/ask", "response_type": response_type},
            tags=[f"Response Type: {response_type}"],
            public=True
        )

        return jsonify({"answer": response_text, "warning": warning, "links": links})

    except Exception as e:
        logger.error(f"Error generating response: {e}", exc_info=True)

        langfuse_context.update_current_observation(
            user_id=user_id,
            output={"error": str(e)},
            name="api_ask_error",
            metadata={"endpoint": "/api/ask"},
            tags=["error"],
            public=False
        )

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



