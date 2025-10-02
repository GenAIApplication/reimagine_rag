from google import genai
from config import env_config

def get_client():
    client = genai.Client(api_key=env_config.get("GEMINI_API",None))
    return client