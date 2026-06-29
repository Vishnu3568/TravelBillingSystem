import requests
import logging
from datetime import date
from typing import List, Dict, Any, Optional
from app.config import settings
from app.schemas.ai import (
    AiBillResponse, AiSearchFilter, AiInsightResponse, AiAssistantRequest, 
    AiAssistantResponse, AiSuggestionRequest, AiSuggestionResponse
)

logger = logging.getLogger("gemini_service")

class GeminiService:
    def __init__(self):
        self.base_url = settings.AI_SERVICE_URL.rstrip('/')
        self.headers = {"Content-Type": "application/json"}
        if settings.INTERNAL_API_KEY:
            self.headers["x-api-key"] = settings.INTERNAL_API_KEY

    def _post(self, path: str, json_data: Any) -> Optional[requests.Response]:
        url = f"{self.base_url}{path}"
        try:
            # Connect and read timeout set to 5 minutes (300 seconds) matches Java's RestTemplateBuilder configuration
            response = requests.post(url, json=json_data, headers=self.headers, timeout=300)
            response.raise_for_status()
            return response
        except Exception as e:
            logger.error(f"Failed to connect to AI Service at {url}: {e}")
            return None

    def parse_bill_text(self, raw_text: str) -> List[Dict[str, Any]]:
        payload = {"text": raw_text}
        logger.info("Delegating parsing request to AI Service (Port 9001)...")
        res = self._post("/parse-bill", payload)
        if res:
            try:
                return res.json()
            except Exception:
                return []
        return [{"warnings": ["AI Service Connection Error. Ensure AI service is running on port 9001."]}]

    def extract_companies(self, raw_text: str) -> List[Dict[str, str]]:
        payload = {"text": raw_text}
        logger.info("Delegating company extraction to AI Service (Port 9001)...")
        res = self._post("/extract-companies", payload)
        if res:
            try:
                return res.json()
            except Exception:
                return []
        return []

    def parse_search_query(self, query: str) -> Optional[Dict[str, Any]]:
        payload = {"query": query, "currentDate": str(date.today())}
        logger.info("Delegating NL search parsing to AI Service (Port 9001)...")
        res = self._post("/nl-search", payload)
        if res:
            try:
                return res.json()
            except Exception:
                return None
        return None

    def generate_insights(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        payload = {"stats": stats}
        logger.info("Delegating insights generation to AI Service (Port 9001)...")
        res = self._post("/generate-insights", payload)
        if res:
            try:
                return res.json()
            except Exception:
                pass
        return {
            "insights": [
                {
                    "type": "WARNING",
                    "message": "AI Insights Service currently unavailable.",
                    "confidence": 0.0
                }
            ]
        }

    def ask_assistant(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Delegating assistant query to AI Service (Port 9001)...")
        res = self._post("/chat-assistant", request_data)
        if res:
            try:
                return res.json()
            except Exception:
                pass
        return {
            "answer": "I'm having trouble connecting to my brain right now. Please ensure the AI service is running.",
            "confidence": 0.0
        }

    def generate_suggestions(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Delegating suggestions generation to AI Service (Port 9001)...")
        res = self._post("/generate-suggestions", request_data)
        if res:
            try:
                return res.json()
            except Exception:
                pass
        return {"suggestions": []}

    def index_bill(self, bill_id: int, text: str):
        payload = {"billId": bill_id, "text": text}
        logger.info(f"Indexing bill #{bill_id} in AI Vector Store...")
        self._post("/index-bill", payload)

gemini_service = GeminiService()
