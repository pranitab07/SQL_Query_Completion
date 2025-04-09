import os
import re
import requests
import yaml
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

def query_groq_llama(user_input: str, context: str = "", config_path: str = "params.yaml") -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable not set.")
    
    with open(config_path) as f:
        config = yaml.safe_load(f)
    model = config["llm"]["model"]
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Combine context and user input into one prompt
    full_prompt = f"""You are an expert SQL assistant. Only respond with the completed SQL query. 
Do not include explanations, comments, or extra text.

Context: {context}

User Input: {user_input}
"""

    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are an expert SQL assistant. Only return valid SQL code. No explanations."},
            {"role": "user", "content": full_prompt}
        ],
        "temperature": 0.3
    }

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    raw_output = response.json()["choices"][0]["message"]["content"]

    # Extract valid SQL using regex (starts with common SQL keywords)
    match = re.search(r"(?i)\b(select|insert|update|delete|with|create|drop|alter)\b.+", raw_output, re.DOTALL)
    clean_sql = match.group(0).strip() if match else raw_output.strip()
    return clean_sql