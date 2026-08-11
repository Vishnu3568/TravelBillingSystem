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
    def classify_elements(elements: List[Dict[str, Any]], learned_context: str = "") -> List[Dict[str, Any]]:
        """
        Classifies elements by invoking Gemini API, failing over to Ollama,
        and finally falling back to a deterministic local rule-based classifier.
        """
        if not elements:
            return []

        elements_json = json.dumps(elements, indent=2)
        user_prompt = USER_PROMPT_TEMPLATE.format(elements_json=elements_json)
        
        prompt_parts = []
        if learned_context:
            prompt_parts.append(learned_context)
        prompt_parts.append(SYSTEM_PROMPT)
        prompt_parts.append(user_prompt)
        prompt = "\n\n".join(prompt_parts)

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

            # 1. Company Name classification
            if ("to," in text_lower or "to:" in text_lower or "billed to" in text_lower) and "sri tulja bhavani" not in text_lower:
                label = FieldLabel.HEADER_COMPANY
                confidence = 0.98
            elif any(k in text_lower for k in ["pvt ltd", "technologies", "solutions", "industries", "limited", "enterprises", "portescap", "ashapura"]) and "sri tulja bhavani" not in text_lower:
                label = FieldLabel.HEADER_COMPANY
                confidence = 0.98

            # 2. Bill Number / Duty Slip classification
            elif re.search(r"^ds[-\s]?\d+$", text_lower) or re.search(r"\b(duty\s*slip|ds)\s*(no|num|number|#)?[\.:\s\-]*\d+\b", text_lower):
                label = FieldLabel.HEADER_DUTY_SLIP
                confidence = 0.98
            elif re.search(r"\b(bill|invoice)\s*(no|num|number|#)?[\.:\s\-]*\d+\b", text_lower):
                label = FieldLabel.HEADER_BILL_NUMBER
                confidence = 0.98

            # 3. GST classification
            elif "gst" in text_lower and any(char.isdigit() for char in text):
                label = FieldLabel.HEADER_GST
                confidence = 0.98

            # 4. Address classification
            elif "address" in text_lower and not any(k in text_lower for k in ["to", "company", "name"]):
                label = FieldLabel.HEADER_ADDRESS
                confidence = 0.98

            # 5. Phone / Mobile classification
            elif ("phone" in text_lower or "mobile" in text_lower or re.match(r"^\+?[\d\s-]{10,15}$", text)) and any(char.isdigit() for char in text):
                label = FieldLabel.HEADER_PHONE
                confidence = 0.98

            # 6. Vehicle Type & Number classification
            elif re.search(r"\b(sedan|suv|indica|bus|tempo|innova|crysta|dzire|etios)\b", text_lower):
                label = FieldLabel.VEHICLE_TYPE
                confidence = 0.98
            elif not text_lower.startswith("ds-") and not text_lower.startswith("bill-") and re.search(r"\b[A-Z]{2}[-\s]?\d{2}[-\s]?[A-Z0-9-\s]{2,10}\b", text.upper()) and any(char.isdigit() for char in text):
                label = FieldLabel.VEHICLE_NUMBER
                confidence = 0.98

            # 7. Dates classification
            elif (re.search(r"\b\d{1,2}[-\/\.]\d{1,2}[-\/\.]\d{2,4}\b", text) or re.search(r"\b\d{4}[-\/\.]\d{1,2}[-\/\.]\d{1,2}\b", text)) and any(char.isdigit() for char in text):
                label = FieldLabel.HEADER_DATE
                confidence = 0.98

            # 8. Guest Name & Booker
            elif ("guest" in text_lower or "passenger" in text_lower or "mr." in text_lower or "ms." in text_lower) and not any(k in text_lower for k in ["name", "signature", "travels"]):
                label = FieldLabel.GUEST_NAME
                confidence = 0.98
            elif "booked by" in text_lower and not text_lower.endswith("by"):
                label = FieldLabel.BOOKED_BY
                confidence = 0.98

            # 9. Charges & Pricing classification
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

            # Neighbor context fallback rules
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
                    elif "vehicle no" in left or "reg no" in left or "vehicle" in left or "car" in left:
                        label = FieldLabel.VEHICLE_NUMBER
                        confidence = 0.98
                    elif "date" in left or "date" in above:
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
                    elif "grand total" in left or "total" in left or "total amount" in left or "grand total" in above or "total amount" in above:
                        label = FieldLabel.TOTAL_AMOUNT
                        confidence = 0.98
                    elif "km" in left or "kms" in left:
                        label = FieldLabel.TOTAL_KM
                        confidence = 0.98
                    elif "hours" in left or "hrs" in left:
                        label = FieldLabel.TOTAL_HOURS
                        confidence = 0.98
                    elif re.match(r"^\d{4}$", text) and text not in ["2020", "2021", "2022", "2023", "2024", "2025", "2026"]:
                        label = FieldLabel.VEHICLE_NUMBER
                        confidence = 0.95
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
                    elif "to" in left or "billed to" in left:
                        label = FieldLabel.HEADER_COMPANY
                        confidence = 0.98

            classifications.append({
                "id": el_id,
                "label": label.value,
                "confidence": confidence
            })

        return classifications
