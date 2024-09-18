# mastermind/ai_model.py
import os
import requests
import yaml
import json
import re
from dotenv import load_dotenv
from mastermind.utils import logger
from mastermind.models import Query, db

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
CLOUDFLARE_AI_GATEWAY = os.getenv("CLOUDFLARE_AI_GATEWAY")

def generate_response(question, data, config):
    """Generate a response using the OpenAI API based on the question provided and configuration settings."""
    logger.debug("🎤 We're starting the generate_response function. Ready for it?")

    data_content = "\n\n".join(data.values())
    user_prompt = config['ai']['prompt']
    logger.debug("Loaded user prompt from config. Shake it off!")

    # Construct the system prompt with updated instructions
    system_prompt = (
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
    logger.debug("Constructed system prompt. This is why we can't have nice things...without good logging!")

    full_prompt = f"{user_prompt}\n\n{data_content}\n\nQ: {question}\nA:"
    logger.debug("Constructed full prompt for the assistant. Ready to begin again.")

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    logger.debug("Set up headers for the API request. Stay, stay, stay...on this page!")

    json_data = {
        "model": config['ai']['model'],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_prompt}
        ]
    }

    # Dynamically add settings from config.yml to json_data
    json_data.update(config['ai']['settings'])
    logger.debug("Prepared JSON payload for the API request. It's time to go!")

    result = {
        'answer': '',
        'warning': '',
        'links': []
    }

    # Log query
    query_record = Query(
        query_text=question,
        response_text='',  # Placeholder
        settings_selected=json.dumps(config['ai']['settings']),
        user_id=current_user.user_id
    )
    db.session.add(query_record)
    db.session.commit()

    try:
        logger.info("Sending request to OpenAI API. Are you ready for it?")
        response = requests.post(
            f"https://gateway.ai.cloudflare.com/v1/{CLOUDFLARE_ACCOUNT_ID}/{CLOUDFLARE_AI_GATEWAY}/openai/chat/completions",
            headers=headers,
            json=json_data
        )
        logger.debug(f"Received response with status code {response.status_code}. Everything has changed!")

        if response.status_code == 200:
            response_json = response.json()
            logger.debug("Parsed response JSON successfully. Gorgeous!")

            answer_content = response_json['choices'][0]['message']['content'].strip()
            logger.debug(f"Assistant's raw response: {answer_content}")

            # Function to extract JSON object from the assistant's response
            def extract_json_from_response(text):
                text = text.strip()
                if text.startswith('```') and text.endswith('```'):
                    text = text[3:-3].strip()
                    if text.lower().startswith('json'):
                        text = text[4:].strip()
                json_match = re.search(r'\{.*\}', text, re.DOTALL)
                if json_match:
                    return json_match.group(0)
                else:
                    return None

            # Extract the JSON string
            json_str = extract_json_from_response(answer_content)

            if json_str:
                try:
                    answer_data = json.loads(json_str)
                    result['answer'] = answer_data.get('answer', '')
                    inference = answer_data.get('inference', False)
                    if inference:
                        result['warning'] = "The response uses inference or content not directly mentioned in the source data."
                        logger.warning("Inference detected in the assistant's response. You need to calm down.")
                    result['links'] = answer_data.get('links', [])
                    logger.debug("Extracted data from the assistant's response. Clean.")
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse assistant's response as JSON: {e} This is why we can't have nice things.")
                    result['answer'] = answer_content
                    result['warning'] = "The assistant's response could not be parsed as JSON."
            else:
                logger.error("No JSON object found in the assistant's response. Bad blood!")
                result['answer'] = answer_content
                result['warning'] = "The assistant's response does not contain a JSON object."
        else:
            logger.error(f"API request failed with status code {response.status_code}. I knew you were trouble.")
            result['answer'] = f"Error: {response.status_code} - {response.text}"

    except Exception as e:
        logger.exception("An exception occurred during the API request. Out of the woods?")
        result['answer'] = f"Exception: {str(e)}"

    logger.debug("Finished processing the generate_response function. Long live.")
    return result
