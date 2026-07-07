from __future__ import annotations

import json
import logging
import re
import time
import requests
from typing import Dict, Any, List, Optional
from app.config import settings
from app.services.field_labeling.field_constants import FieldLabel
from app.services.field_labeling.label_prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

logger = logging.getLogger("field_classifier")

class FieldClassifier:
    @staticmethod
    def classify_elements(elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Classifies elements by invoking Gemini API, failing over to Ollama,
        and finally falling back to a deterministic local rule-based classifier.
        """
        if not elements:
            return []

        elements_json = json.dumps(elements, indent=2)
        user_prompt = USER_PROMPT_TEMPLATE.format(elements_json=elements_json)
        prompt = f"{SYSTEM_PROMPT}\n\n{user_prompt}"

        # 1. Try Gemini API
        if settings.GEMINI_API_KEY:
            model = settings.GEMINI_MODEL or "gemini-1.5-pro"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={settings.GEMINI_API_KEY}"
            payload = {
                "contents": [
                    {
                        "parts": [{"text": prompt}]
                    }
                ]
            }
            headers = {"Content-Type": "application/json"}

            for attempt in range(3):
                try:
                    logger.info(f"Invoking Gemini ({model}) for field classification. Attempt {attempt + 1}")
                    res = requests.post(url, json=payload, headers=headers, timeout=60)
                    if res.status_code == 429:
                        wait_sec = 3 * (attempt + 1)
                        logger.warning(f"Gemini API rate limited (429). Retrying in {wait_sec}s...")
                        time.sleep(wait_sec)
                        continue
                    res.raise_for_status()
                    data = res.json()

                    text_out = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    parsed = FieldClassifier._clean_and_parse_json(text_out)
                    if parsed and "classifications" in parsed:
                        logger.info("Successfully classified elements using Gemini API.")
                        return parsed["classifications"]
                except Exception as e:
                    logger.warning(f"Gemini classification attempt {attempt + 1} failed: {e}")
                    time.sleep(1)

        # 2. Try Ollama Fallback
        try:
            logger.info("Attempting Ollama field classification failover...")
            ollama_url = "http://localhost:11434/api/generate"
            ollama_payload = {
                "model": "gemma",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1
                }
            }
            res = requests.post(ollama_url, json=ollama_payload, timeout=90)
            if res.status_code == 200:
                text_out = res.json().get("response", "").strip()
                parsed = FieldClassifier._clean_and_parse_json(text_out)
                if parsed and "classifications" in parsed:
                    logger.info("Successfully classified elements using Ollama.")
                    return parsed["classifications"]
        except Exception as e:
            logger.warning(f"Ollama failover failed: {e}")

        # 3. Rule-based local fallback classifier
        logger.info("All LLM methods failed. Executing local rule-based classifier fallback.")
        return FieldClassifier._local_rule_classify(elements)

    @staticmethod
    def _clean_and_parse_json(text: str) -> Optional[Dict[str, Any]]:
        text_clean = text.strip()
        if text_clean.startswith("```"):
            text_clean = re.sub(r"^```(?:json)?\n", "", text_clean)
            text_clean = re.sub(r"\n```$", "", text_clean)
            text_clean = text_clean.strip()
        try:
            return json.loads(text_clean)
        except Exception as e:
            logger.warning(f"Failed to parse JSON output: {e}. Raw: {text}")
            match = re.search(r"\{.*\}", text_clean, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except Exception:
                    pass
            return None

    @staticmethod
    def _local_rule_classify(elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        classifications = []
        for el in elements:
            el_id = el.get("id")
            text = str(el.get("text", "")).strip()
            text_lower = text.lower()

            label = FieldLabel.UNKNOWN
            confidence = 0.50

            # Simple rule mapping based on text contents
            if "portescap" in text_lower or "ashapura" in text_lower:
                label = FieldLabel.HEADER_COMPANY
                confidence = 0.98
            elif re.search(r"\b(bill|invoice)\s*(no|number|#)\b", text_lower) and any(char.isdigit() for char in text):
                label = FieldLabel.HEADER_BILL_NUMBER
                confidence = 0.98
            elif re.search(r"^ds[-\s]?\d+$", text_lower):
                label = FieldLabel.HEADER_DUTY_SLIP
                confidence = 0.98
            elif "gst" in text_lower and any(char.isdigit() for char in text):
                label = FieldLabel.HEADER_GST
                confidence = 0.98
            elif "address" in text_lower and not any(k in text_lower for k in ["to", "company", "name"]):
                label = FieldLabel.HEADER_ADDRESS
                confidence = 0.98
            elif ("phone" in text_lower or "mobile" in text_lower or re.match(r"^\+?[\d\s-]{10,15}$", text)) and any(char.isdigit() for char in text):
                label = FieldLabel.HEADER_PHONE
                confidence = 0.98
            elif re.search(r"\b(sedan|suv|indica|bus|tempo|innova|dezire)\b", text_lower):
                label = FieldLabel.VEHICLE_TYPE
                confidence = 0.98
            elif re.search(r"^[A-Z]{2}[-\s]?\d{2}[-\s]?[A-Z0-9-\s]{2,10}$", text.upper()) and any(char.isdigit() for char in text):
                label = FieldLabel.VEHICLE_NUMBER
                confidence = 0.98
            elif ("guest" in text_lower or "passenger" in text_lower or "mr." in text_lower or "ms." in text_lower) and not any(k in text_lower for k in ["name", "signature"]):
                label = FieldLabel.GUEST_NAME
                confidence = 0.98
            elif "booked by" in text_lower and not text_lower.endswith("by"):
                label = FieldLabel.BOOKED_BY
                confidence = 0.98
            elif "bata" in text_lower and any(char.isdigit() for char in text):
                label = FieldLabel.DRIVER_BATA
                confidence = 0.98
            elif "toll" in text_lower and any(char.isdigit() for char in text):
                label = FieldLabel.TOLL
                confidence = 0.98
            elif "parking" in text_lower and any(char.isdigit() for char in text):
                label = FieldLabel.PARKING
                confidence = 0.98
            elif "permit" in text_lower and any(char.isdigit() for char in text):
                label = FieldLabel.PERMIT
                confidence = 0.98
            elif ("total" in text_lower or "grand total" in text_lower) and any(char.isdigit() for char in text):
                label = FieldLabel.TOTAL_AMOUNT
                confidence = 0.98
            elif "rupees" in text_lower or "only" in text_lower:
                label = FieldLabel.AMOUNT_WORDS
                confidence = 0.98
            elif "signature" in text_lower:
                label = FieldLabel.SIGNATURE
                confidence = 0.98
            elif re.search(r"\b\d+\s*[xX\*]\s*\d+\b", text):
                if "150" in text or "bata" in text_lower:
                    label = FieldLabel.EXTRA_HOUR_FORMULA
                else:
                    label = FieldLabel.EXTRA_KM_FORMULA
                confidence = 0.98
            elif (re.search(r"\b\d{2}-\d{2}-\d{4}\b", text) or re.search(r"\b\d{4}-\d{2}-\d{2}\b", text)) and any(char.isdigit() for char in text):
                label = FieldLabel.HEADER_DATE
                confidence = 0.98

            # Neighbor context rules
            neighbors = el.get("neighbors", {})
            left = str(neighbors.get("left", "")).lower() if neighbors.get("left") else ""
            above = str(neighbors.get("above", "")).lower() if neighbors.get("above") else ""

            if label == FieldLabel.UNKNOWN:
                if any(char.isdigit() for char in text):
                    if "bill no" in left or "bill number" in left:
                        label = FieldLabel.HEADER_BILL_NUMBER
                        confidence = 0.98
                    elif "duty slip" in left or "slip no" in left:
                        label = FieldLabel.HEADER_DUTY_SLIP
                        confidence = 0.98
                    elif "vehicle no" in left or "reg no" in left:
                        label = FieldLabel.VEHICLE_NUMBER
                        confidence = 0.98
                    elif "date" in left:
                        label = FieldLabel.HEADER_DATE
                        confidence = 0.98
                    elif "toll" in left:
                        label = FieldLabel.TOLL
                        confidence = 0.98
                    elif "parking" in left:
                        label = FieldLabel.PARKING
                        confidence = 0.98
                    elif "driver bata" in left or "bata" in left:
                        label = FieldLabel.DRIVER_BATA
                        confidence = 0.98
                    elif "grand total" in left or "total" in left or "total amount" in left:
                        label = FieldLabel.TOTAL_AMOUNT
                        confidence = 0.98
                    elif "km" in left or "kms" in left:
                        label = FieldLabel.TOTAL_KM
                        confidence = 0.98
                    elif "hours" in left or "hrs" in left:
                        label = FieldLabel.TOTAL_HOURS
                        confidence = 0.98
                else:
                    if "guest" in left or "passenger" in left:
                        label = FieldLabel.GUEST_NAME
                        confidence = 0.98
                    elif "booked by" in left:
                        label = FieldLabel.BOOKED_BY
                        confidence = 0.98
                    elif "vehicle type" in left or "car type" in left:
                        label = FieldLabel.VEHICLE_TYPE
                        confidence = 0.98

            classifications.append({
                "id": el_id,
                "label": label.value,
                "confidence": confidence
            })

        return classifications
