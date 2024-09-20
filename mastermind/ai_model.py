# mastermind/ai_model.py
import os
import requests
import yaml
import json
import re
from datetime import datetime
import pytz
#from dotenv import load_dotenv
from mastermind.utils import logger
from mastermind.models import Query, db, Response
from flask_login import current_user
from langfuse.decorators import langfuse_context, observe

# Load environment variables
# load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
CLOUDFLARE_AI_GATEWAY = os.getenv("CLOUDFLARE_AI_GATEWAY")

def construct_system_prompt():
    """Construct the system prompt for the AI model."""
    return (
        "You are an assistant that answers questions based solely on the provided data. "
        "Respond from Don Beyer's perspective using the first person. "
        "Avoid using phrases like 'as a member of Congress' or 'visit my website.' "
        "If the answer is not directly found in the data, you must set 'inference' to true "
        "and provide an answer based on reasonable inference from the available information. "
        "**Do not mention that the data does not specifically address the question in your response. "
        "Do not include phrases like 'the provided information does not specifically address...', 'I don't have information on...', 'There is no data about...', or any similar statements.** "
        "Instead, provide a thoughtful answer based on what can be reasonably inferred. "
        "Each piece of information includes a URL for reference; include this URL when citing specific content in your response. "
        "Only include source links when referring to specific content, and never suggest going back to the website for more information. "
        "**IMPORTANT:** Provide your response **EXACTLY** in the following JSON format, and **do not include any additional text, code blocks, or formatting**. Do not wrap the JSON in triple backticks or any markdown formatting. Do not include any comments or notes. Only output the pure JSON.\n"
        "{\n"
        '  "answer": "Your detailed answer here.",\n'
        '  "inference": true/false,\n'
        '  "links": [\n'
        '    {"url": "https://example.com", "text": "Description of the link."},\n'
        "    ...\n"
        "  ]\n"
        "}\n"
        "\n"
        "**Examples of what NOT to include in your response:**\n"
        "- 'The provided information does not specifically address...'\n"
        "- 'I don't have information on...'\n"
        "- 'There is no data about...'\n"
        "- Any mention that the data is lacking or doesn't cover the topic.\n"
        "\n"
        "**Example of a correct response when inferring:**\n"
        "{\n"
        '  "answer": "I prioritize national security and technological innovation. Any decision on banning DJI drones would involve carefully weighing security concerns against the benefits of technological advancement.",\n'
        '  "inference": true,\n'
        '  "links": []\n'
        "}"
    )

def construct_full_prompt(user_prompt, data_content, question):
    """Construct the full prompt for the assistant."""
    return f"{user_prompt}\n\n{data_content}\n\nQ: {question}\nA:"

def prepare_headers():
    """Prepare the headers for the API request."""
    return {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

def prepare_json_payload(system_prompt, full_prompt, config):
    """Prepare the JSON payload for the API request."""
    json_data = {
        "model": config['ai']['model'],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_prompt}
        ]
    }
    json_data.update(config['ai']['settings'])  # Add settings from config
    return json_data

def extract_json_from_response(text):
    """Extract the JSON object from the assistant's response."""
    text = text.strip()
    if text.startswith('```') and text.endswith('```'):
        text = text[3:-3].strip()
        if text.lower().startswith('json'):
            text = text[4:].strip()
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        return json_match.group(0)
    return None

def log_query(question, config):
    """Log the query to the database."""
    query_record = Query(
        query_text=question,
        settings_selected=json.dumps(config['ai']['settings']),
        user_id=current_user.user_id
    )
    db.session.add(query_record)
    db.session.commit()
    return query_record

def process_response(response):
    """Process the API response and extract useful information."""
    result = {
        'answer': '',
        'warning': '',
        'links': []
    }

    if response.status_code == 200:
        response_json = response.json()
        answer_content = response_json['choices'][0]['message']['content'].strip()

        # Extract the JSON string
        json_str = extract_json_from_response(answer_content)

        if json_str:
            try:
                answer_data = json.loads(json_str)
                result['answer'] = answer_data.get('answer', '')
                result['inference'] = answer_data.get('inference', False)

                if result['inference']:
                    result['warning'] = "The response uses inference or content not directly mentioned in the source data."

                result['links'] = answer_data.get('links', [])
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse assistant's response as JSON: {e}")
                result['answer'] = answer_content
                result['warning'] = "The assistant's response could not be parsed as JSON."
        else:
            logger.error("No JSON object found in the assistant's response.")
            result['answer'] = answer_content
            result['warning'] = "The assistant's response does not contain a JSON object."
    else:
        logger.error(f"API request failed with status code {response.status_code}.")
        result['answer'] = f"Error: {response.status_code} - {response.text}"

    return result

# Handle response generation
@observe(as_type="generation", capture_input=True, capture_output=True)
def generate_response(question, data, config):
    """Main function to generate a response using the OpenAI API."""
    logger.debug("🎤 Starting the generate_response function.")

    # Prepare data
    full_prompt = prepare_full_prompt(data, config, question)

    try:
        # Execute the OpenAI API call
        response = send_openai_request(full_prompt, config)

        # Process the response and log results
        result = process_response(response)

        if response.status_code == 200:
            log_token_usage(response.json().get('usage', {}), config, full_prompt)
            # Note: We will only return in this function, commit in the main route to avoid duplicate commits
            logger.info(f"Response generated successfully for question: {question}")
        else:
            logger.error(f"Failed API response: {response.status_code}")

    except Exception as e:
        logger.exception("Error during response generation")
        db.session.rollback()
        result = {
            'answer': f"Exception: {str(e)}",
            'warning': '',
            'links': []
        }

    return result


def log_token_usage(usage_data, config, full_prompt):
    """Log token usage and generation-specific parameters to Langfuse."""
    prompt_tokens = usage_data.get('prompt_tokens', 0)
    completion_tokens = usage_data.get('completion_tokens', 0)
    total_tokens = usage_data.get('total_tokens', prompt_tokens + completion_tokens)

    logger.debug(f"Token usage: Prompt: {prompt_tokens}, Completion: {completion_tokens}, Total: {total_tokens}")

    # Extract dynamic model parameters from config['ai']['settings']
    model_parameters = config['ai'].get('settings', {})

    # Prepare usage payload
    usage_payload = {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "unit": "TOKENS"
    }

    # Capture completion start time in EST
    est = pytz.timezone('US/Eastern')
    completion_start_time = datetime.now(est)

    # Send the update to Langfuse with generation-specific params
    langfuse_context.update_current_observation(
        usage=usage_payload,
        model=config['ai']['model'],
        metadata={"model": config['ai']['model']},
        completion_start_time=completion_start_time,
        model_parameters=model_parameters,
        public=True
    )

    logger.debug(f"Langfuse Usage Payload:\n{usage_payload}")


def prepare_full_prompt(data, config, question):
    """Prepare the full prompt and headers for the OpenAI API request."""
    user_prompt = config['ai']['prompt']
    data_content = "\n\n".join(data.values())

    full_prompt = construct_full_prompt(user_prompt, data_content, question)
    logger.debug("Constructed full prompt.")

    return full_prompt

def send_openai_request(full_prompt, config):
    """Send the request to the OpenAI API."""
    headers = prepare_headers()
    system_prompt = construct_system_prompt()
    json_data = prepare_json_payload(system_prompt, full_prompt, config)

    logger.info("Sending request to OpenAI API.")
    response = requests.post(
        f"https://gateway.ai.cloudflare.com/v1/{CLOUDFLARE_ACCOUNT_ID}/{CLOUDFLARE_AI_GATEWAY}/openai/chat/completions",
        headers=headers,
        json=json_data
    )

    logger.debug(f"Received response with status code {response.status_code}.")
    return response

def process_and_log_response(response, query_record, config):
    """Process the API response and update logs, Langfuse, and the database."""
    result = process_response(response)

    # Check for successful response
    if response.status_code == 200:
        handle_successful_response(result, query_record, response, config)
    else:
        logger.error(f"API request failed: {response.status_code}")

    return result

def handle_successful_response(result, query_record, response, config):
    """Handle a successful response, including logging token usage and saving data."""
    usage_data = response.json().get('usage', {})
    log_token_usage(usage_data, config)

    # Save the response to the database
    if result['answer']:
        save_response_to_db(result['answer'], query_record)

        # Log the successful response processing with Langfuse
        log_langfuse_success(query_record.response_id, result['answer'], config)

def log_langfuse_success(response_id, answer, config):
    """Log the successful processing of the response in Langfuse."""
    langfuse_context.update_current_observation(
        output={"response_id": response_id, "answer": answer},
        name="ai_query_success",
        metadata={
            "api_key": "OpenAI",
            "model": config['ai']['model'],
            "prompt": config['ai']['prompt'],
            "model_parameters": config['ai'].get('settings', {})
        },
        tags=["ai", "openai", "success"],
        public=True
    )

def save_response_to_db(answer, query_record):
    """Save the generated response to the database."""
    new_response = Response(response_text=answer)
    db.session.add(new_response)
    db.session.flush()  # Get the new response ID

    # Update the query with the response ID
    query_record.response_id = new_response.id
    db.session.commit()

    logger.info("Response saved and query updated successfully.")

def handle_request_error(e, query_record, config):
    """Handle errors during the API request."""
    logger.exception("An exception occurred during the API request.")
    db.session.rollback()

    # Log error with Langfuse
    langfuse_context.update_current_observation(
        output={"error": str(e)},
        name="ai_query_error",
        metadata={"api_key": "OpenAI", "model": config['ai']['model']},
        tags=["ai", "openai", "error"],
        public=False  # Keep errors private
    )

    return {
        'answer': f"Exception: {str(e)}",
        'warning': '',
        'links': []
    }
