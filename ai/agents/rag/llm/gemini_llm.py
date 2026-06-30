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
        if not self.api_key:
            logger.warning("Gemini API key is missing. Falling back to local Ollama...")
            return self._generate_ollama(prompt, system_instruction)
            
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
            logger.error(f"Gemini API invocation failed: {e}. Falling back to local Ollama...")
            return self._generate_ollama(prompt, system_instruction)

    def _generate_ollama(self, prompt: str, system_instruction: str) -> str:
        url = "http://localhost:11434/api/generate"
        full_prompt = f"{system_instruction}\n\n{prompt}" if system_instruction else prompt
        payload = {
            "model": "gemma",
            "prompt": full_prompt,
            "stream": False,
            "format": "json"
        }
        try:
            res = requests.post(url, json=payload, timeout=15)
            res.raise_for_status()
            return res.json().get("response", "").strip()
        except Exception as err:
            logger.error(f"Ollama local fallback failed: {err}")
            return json.dumps({
                "answer": "Failed to connect to both Gemini API and local Ollama instance.",
                "confidence": 0.0,
                "citations": []
            })
