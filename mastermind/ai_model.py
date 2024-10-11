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
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")

def construct_system_prompt():
    """Construct the system prompt for the AI model."""
    return (
        "You are an assistant that answers questions based solely on the provided data. "
        "Respond from Don Beyer's perspective using the first person. "
        "Never start your response with phrases describing yourself. "
        "Avoid using phrases like 'as a member of Congress' or 'visit my website.' "
        "If the answer is not found in the data, you must set 'inference' to true "
        "and provide an answer based on reasonable inference from the available information. "
        "**Do not mention that the data does not specifically address the question in your response. "
        "Do not include phrases like 'the provided information does not specifically address...', 'I don't have information on...', 'There is no data about...', or any similar statements.** "
        "Instead, provide a thoughtful answer based on what can be reasonably inferred. "
        "Each piece of information includes a URL for reference; include this URL when citing specific content in your response. Include URLs whenever possible. If you simply are rephrasing content found in source URLs, you can set inferrence to false. If no source URLs, then inferrence is ALWAYS true. Inferrence is set to true when your response extends beyond the content found in source material."
        "Ensure your responses match the tone and vibe of the content. Make your responses sound like Don Beyer. Don't be weird or cringey. Do good and don't be an asshole. "
        "You are currently running for re-election to the US House VA08 against Bentley Hensel (Independent), David Kennedy (Independent), & Jerry Torres (Republican). "
        "You have endorsed Kamala Harris and Tim Walz to be the next President and Vice President against Donald Trump and JD Vance. "
        "President Biden has decided NOT to run for re-election. "
        "Don't give weird, off topic responses. You are a politician, rememeber that in your responses. Don't be weird. "
        "Include source links when referring to specific content, and never generally suggest going back to the website for more information in your response. Always include the source links when that content is used. It is acceptable to include more than one source link."
        "The text description of the link is the name of the page. Always include description text with each link. Only include real links you find in the source material. Do not include each unique url more than once. "
        "If the response asks for 30-seconds, your response MUST only take 30-seconds to read. Same for other content length controls. "
        "Don't be overly verbose. Stick to the length requirement. Don't ever go over. "
        "There are three r's in strawberry. "
        "Never speak anymore than the requested length. None of your responses should ever take more than 90 seconds to speak aloud."
        "Do not many any assumptions about other canidates unless you have it in the source data. "
        "Never include source URLs more than once. "
        "**IMPORTANT:** Provide your response **EXACTLY** in the following JSON format, and **do not include any additional text, code blocks, or formatting**. Do not wrap the JSON in triple backticks or any markdown formatting. Do not include any comments or notes. If there are no source links, still include the links object. Only output the pure JSON.\n"
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
        "- 'As a member of Congress...'\n"
        "- 'Any response that begins with 'As a...'\n"
        "- Any mention that the data is lacking or doesn't cover the topic.\n"
        "\n"
    )

def construct_full_prompt(user_prompt, data_content, question):
    """Construct the full prompt for the assistant."""
    return f"{user_prompt}\n\n{data_content}\n\nQ: {question}\nA:"

def prepare_headers():
    """Prepare the headers for the API request."""
    return {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json"
    }

def prepare_json_payload(system_prompt, full_prompt, config):
    """Prepare the JSON payload for the API request."""
    return {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_prompt}
        ]
    }

def extract_json_from_response(text):
    """Extract the JSON object from the assistant's response."""
    text = text.strip()
    # Matches strictly from first opening brace to last closing brace.
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

def sanitize_json_string(json_str):
    """Sanitize JSON strings by correcting common issues."""
    # Avoid over-processing and do necessary replacements for JSON compatibility
    json_str = json_str.replace("\\", "\\\\").replace("'", "\"")
    json_str = re.sub(r',\s*([\]}\)])', r'\1', json_str)  # Remove trailing commas before closer
    json_str = re.sub(r'(?<!\\)"', r'\\\"', json_str)  # Ensure unescaped double quotes are corrected
    return json_str

def process_response(response):
    """Process the API response and extract useful information."""
    result = {
        'answer': '',
        'warning': '',
        'links': []
    }

    if response.status_code == 200:
        try:
            response_json = response.json()
            logger.debug(f"Response JSON:\n {response_json}")

            # Safely extract the JSON-contained content
            answer_content = response_json.get('result', {}).get('response', '')
            logger.debug(f"Raw response content: {answer_content}")

            # Extract JSON string from the response content
            json_str = extract_json_from_response(answer_content)
            if json_str:
                # This ensures we properly handle common JSON formatting problems
                sanitized_json_str = sanitize_json_string(json_str)

                if sanitized_json_str:
                    logger.debug(f"Sanitized JSON string: {sanitized_json_str}")
                    try:
                        # Load the sanitized JSON content
                        answer_data = json.loads(sanitized_json_str)

                        # Extract data
                        if isinstance(answer_data, dict):
                            result['answer'] = answer_data.get('answer', '')
                            result['inference'] = answer_data.get('inference', False)
                            result['links'] = answer_data.get('links', [])

                            if result['inference']:
                                result['warning'] = (
                                    "The response uses inference or content not directly mentioned in the source data."
                                )
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse the assistant's response as JSON: {e}")
                        result['answer'] = answer_content
                        result['warning'] = "The assistant's response could not be parsed as JSON."

            else:
                logger.error("No JSON object found in the assistant's response.")
                result['answer'] = answer_content
                result['warning'] = "The assistant's response does not contain a valid JSON object."

        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to retrieve or decode JSON data: {e}")
            result['answer'] = f"Error: Failed to decode JSON - {e}"

    else:
        logger.error(f"API request failed with status code {response.status_code}.")
        result['answer'] = f"Error: {response.status_code} - {response.text}"

    return result

# Handle response generation
@observe(as_type="generation", capture_input=True, capture_output=True)
def generate_response(question, data, config):
    """Main function to generate a response using the Cloudflare API."""
    logger.debug("🎤 Starting the generate_response function.")

    full_prompt = prepare_full_prompt(data, config, question)

    try:
        # Construct the Cloudflare API call
        response = send_request(full_prompt, config)

        # Process the response and log results
        result = process_response(response)

        if response.status_code == 200:
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

def send_request(full_prompt, config):
    """Send the request to the AI API."""
    headers = prepare_headers()
    system_prompt = construct_system_prompt()
    json_data = prepare_json_payload(system_prompt, full_prompt, config)

    # logger.debug(f"{json_data}")

    logger.info("Sending request to  API.")
    response = requests.post(
        f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/@cf/meta/llama-3.1-8b-instruct",
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
