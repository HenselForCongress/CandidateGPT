# mastermind/ai_model.py
import os
import requests
import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
CLOUDFLARE_AI_GATEWAY = os.getenv("CLOUDFLARE_AI_GATEWAY")

def generate_response(question, data, config):
    """Generate a response using the OpenAI API based on the question provided and configuration settings."""
    data_content = "\n\n".join(data.values())
    user_prompt = config['ai']['prompt']
    full_prompt = f"{user_prompt}\n\n{data_content}\n\nQ: {question}\nA:"

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    json_data = {
        "model": config['ai']['model'],
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": full_prompt}
        ]
    }

    # Dynamically add settings from config.yml to json_data
    json_data.update(config['ai']['settings'])

    response = requests.post(
        # "https://api.openai.com/v1/chat/completions",
        f"https://gateway.ai.cloudflare.com/v1/{CLOUDFLARE_ACCOUNT_ID}/{CLOUDFLARE_AI_GATEWAY}/openai/chat/completions",
        headers=headers,
        json=json_data
    )

    result = {
        'answer': '',
        'warning': '',
        'links': []
    }

    if response.status_code == 200:
        response_json = response.json()
        answer_content = response_json['choices'][0]['message']['content'].strip()

        # Check for inference markers or missing direct answers
        if 'inference' in answer_content.lower() or 'not directly answered' in answer_content.lower():
            result['warning'] = "The response uses inference or content not directly mentioned in the source data."

        # Extract and hyperlink references
        # Example: Collect URLs mentioned in the response, this is simplified and might need regex for complex extraction
        for link in response_json.get('choices', [])[0].get('message', {}).get('metadata', {}).get('references', []):
            result['links'].append({'url': link['url'], 'text': link.get('text', 'Resource Link')})

        result['answer'] = answer_content
    else:
        result['answer'] = f"Error: {response.status_code} - {response.text}"

    return result
