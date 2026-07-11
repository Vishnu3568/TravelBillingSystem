import logging
import requests
import json
from .llm_interface import BaseLlmClient
from config import settings


logger = logging.getLogger("gemini_llm")

class GeminiLlmClient(BaseLlmClient):
    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.GEMINI_MODEL
        self.api_key = settings.GEMINI_API_KEY

    def generate_response(self, system_instruction: str, prompt: str) -> str:
        if not self.api_key or self.api_key == "AIzaSyDmncG2GztNQgfJhXuGIRE1ej2Q9ghEVoc" or self.api_key.startswith("YOUR_"):
            raise ValueError("Gemini API key is missing or is the default mock placeholder. Cannot execute LLM queries.")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 1000,
                "responseMimeType": "application/json"
            }
        }
        
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }
            
        try:
            res = requests.post(url, json=payload, headers=headers, timeout=30)
            res.raise_for_status()
            text = res.json()["candidates"][0]["content"]["parts"][0]["text"]
            return text.strip()
        except Exception as e:
            logger.error(f"Gemini API invocation failed: {e}")
            raise e
