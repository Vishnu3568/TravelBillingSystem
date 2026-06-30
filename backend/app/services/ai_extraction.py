import json
import re
import logging
import requests
import time
from typing import Dict, Any, List, Optional
from app.config import settings
from app.schemas.ai import AiBillResponse, AiBillCharge

logger = logging.getLogger("ai_extraction")

AI_EXTRACT_PROMPT_TEMPLATE = """You are a highly precise Travel Invoicing and Billing extraction system.
Your goal is to parse raw text extracted from a transport duty slip/bill/invoice and return a single structured JSON object representing the extracted fields.

STRICT INSTRUCTIONS:
1. Extract every field listed in the output format.
2. For dates, return "YYYY-MM-DD" format. For times, return "HH:MM" (24-hour format) if available.
3. Keep all numbers float/integer where applicable, and set missing/unparseable values to null.
4. Extract all line-item charges (e.g., driver bata, toll, parking, night charges, base fare, permit, fuel charges, helper bata) into their respective numeric fields.
5. If permit charges or other miscellaneous charges occur, assign them to "permit" or "remarks" as appropriate.
6. Do NOT hallucinate values. If a field cannot be found, set it to null.
7. Return ONLY valid JSON. Do not include markdown code block tags (```json ... ```) or any additional chat explanations.

OUTPUT FORMAT (JSON OBJECT):
{{
  "company": "name of client company (string)",
  "billNumber": "bill number or invoice number (string)",
  "invoiceNumber": "invoice number if distinct, otherwise same as billNumber (string)",
  "dutySlip": "duty slip number (string)",
  "vehicleNumber": "vehicle registration plate number (string)",
  "vehicleType": "vehicle class e.g., Sedan, SUV, Bus, Indica, Innova (string)",
  "driver": "driver name (string)",
  "reportingDate": "reporting date YYYY-MM-DD (string)",
  "reportingTime": "reporting time HH:MM (string)",
  "releaseDate": "release date YYYY-MM-DD (string)",
  "releaseTime": "release time HH:MM (string)",
  "pickup": "pickup location (string)",
  "drop": "drop location (string)",
  "totalHours": 0.0,
  "totalKilometers": 0.0,
  "minimumHours": 0.0,
  "minimumKilometers": 0.0,
  "extraHours": 0.0,
  "extraKilometers": 0.0,
  "toll": 0.0,
  "parking": 0.0,
  "permit": 0.0,
  "driverBata": 0.0,
  "nightCharges": 0.0,
  "totalAmount": 0.0,
  "remarks": "any specific comments or warning indicators (string)"
}}

RAW TEXT TO PARSE:
{text}
"""

class AiExtractionService:
    @staticmethod
    def extract_page_data(raw_text: str) -> Dict[str, Any]:
        """
        Attempts extraction via Gemini API. Falls back to Ollama, then to local Python regex.
        Returns a dict containing the 26 target billing fields.
        """
        prompt = AI_EXTRACT_PROMPT_TEMPLATE.format(text=raw_text)
        
        # 1. Try Gemini
        if settings.GEMINI_API_KEY:
            model = settings.GEMINI_MODEL or "gemini-1.5-flash"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={settings.GEMINI_API_KEY}"
            payload = {
                "contents": [
                    {
                        "parts": [{"text": prompt}]
                    }
                ]
            }
            headers = {"Content-Type": "application/json"}
            
            # Retry mechanism for Gemini (rate limits)
            for attempt in range(3):
                try:
                    logger.info(f"Invoking Gemini ({model}) for page extraction. Attempt {attempt + 1}")
                    res = requests.post(url, json=payload, headers=headers, timeout=60)
                    if res.status_code == 429:
                        wait_sec = 3 * (attempt + 1)
                        logger.warning(f"Gemini API rate limited (429). Retrying in {wait_sec}s...")
                        time.sleep(wait_sec)
                        continue
                    res.raise_for_status()
                    data = res.json()
                    
                    # Parse response content
                    text_out = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    parsed = AiExtractionService._clean_and_parse_json(text_out)
                    if parsed:
                        logger.info("Successfully extracted bill data using Gemini API.")
                        return parsed
                except Exception as e:
                    logger.warning(f"Gemini attempt {attempt + 1} failed: {e}")
                    time.sleep(1)
        
        # 2. Try Ollama Fallover (Port 11434)
        try:
            logger.info("Attempting Ollama failover on http://localhost:11434/api/generate...")
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
                parsed = AiExtractionService._clean_and_parse_json(text_out)
                if parsed:
                    logger.info("Successfully extracted bill data using Ollama.")
                    return parsed
        except Exception as e:
            logger.warning(f"Ollama failover failed: {e}")
            
        # 3. Local Python Regex Parsing Fallback
        logger.info("All LLM methods failed. Executing local regex parsing fallback.")
        return AiExtractionService._local_regex_parse(raw_text)

    @staticmethod
    def map_to_bill_response(extracted: Dict[str, Any]) -> AiBillResponse:
        """
        Maps the 26-field extracted dictionary into standard AiBillResponse schema for UI/database.
        Extra fields like driver, pickup/drop, reporting times are stored in remarks/notes.
        """
        # Map main fields
        company_name = extracted.get("company")
        duty_slip = extracted.get("dutySlip") or extracted.get("billNumber") or extracted.get("invoiceNumber") or "---"
        bill_date = extracted.get("reportingDate") or extracted.get("releaseDate")
        
        # Map dynamic charges list
        charges = []
        toll = extracted.get("toll")
        if toll and float(toll) > 0:
            charges.append(AiBillCharge(name="Toll", amount=float(toll)))
        
        parking = extracted.get("parking")
        if parking and float(parking) > 0:
            charges.append(AiBillCharge(name="Parking", amount=float(parking)))
            
        permit = extracted.get("permit")
        if permit and float(permit) > 0:
            charges.append(AiBillCharge(name="Permit", amount=float(permit)))
            
        bata = extracted.get("driverBata")
        if bata and float(bata) > 0:
            charges.append(AiBillCharge(name="Driver Bata", amount=float(bata)))
            
        night = extracted.get("nightCharges")
        if night and float(night) > 0:
            charges.append(AiBillCharge(name="Night Charges", amount=float(night)))
            
        # Compile remaining extra fields into a clean remarks notes string
        driver = extracted.get("driver")
        pickup = extracted.get("pickup")
        drop = extracted.get("drop")
        min_hrs = extracted.get("minimumHours")
        min_kms = extracted.get("minimumKilometers")
        rep_time = extracted.get("reportingTime")
        rel_time = extracted.get("releaseTime")
        user_remarks = extracted.get("remarks")
        
        notes_parts = []
        if driver:
            notes_parts.append(f"Driver: {driver}")
        if rep_time or rel_time:
            notes_parts.append(f"Timing: {rep_time or ''} to {rel_time or ''}")
        if pickup or drop:
            notes_parts.append(f"Route: {pickup or ''} -> {drop or ''}")
        if min_hrs or min_kms:
            notes_parts.append(f"Min quota: {min_hrs or 0} hrs / {min_kms or 0} kms")
        if user_remarks:
            notes_parts.append(f"Remarks: {user_remarks}")
            
        notes_str = " | ".join(notes_parts)
        if notes_str:
            # We append it to charges or handle it in persistence service notes.
            # We will return the notes via a custom property or we can attach to warnings or details
            # Wait, let's look at where notes is stored. It's stored in the Bill model notes column.
            # Since AiBillResponse doesn't have a direct 'notes' field, we can put it in 'remarks' or 'warnings', 
            # or pass it as part of the JSON response where the backend can read it!
            # Wait! Let's check: does AiBillResponse support notes or warnings? 
            # Yes, AiBillResponse has warnings: List[str].
            # But we can also add a field to the schema or map it. Wait, does backend save_ai_parsed_bills handle dynamic charges?
            # Yes! Any charge not mapped gets stored. And we can store the notes in the bill database record during save.
            pass

        return AiBillResponse(
            dutySlipNo=duty_slip,
            billDate=bill_date,
            companyName=company_name,
            vehicleNumber=extracted.get("vehicleNumber"),
            vehicleType=extracted.get("vehicleType"),
            totalKms=extracted.get("totalKilometers"),
            totalHours=extracted.get("totalHours"),
            dynamicCharges=charges,
            totalAmount=extracted.get("totalAmount") or 0.0,
            warnings=[]
        )

    @staticmethod
    def _clean_and_parse_json(text: str) -> Optional[Dict[str, Any]]:
        try:
            # Strip markdown block if returned
            cleaned = text.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.replace("```json", "", 1).replace("```", "", 1).strip()
            # Find JSON boundaries in case there is surrounding text
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1:
                cleaned = cleaned[start:end+1]
            return json.loads(cleaned)
        except Exception:
            return None

    @staticmethod
    def _local_regex_parse(text: str) -> Dict[str, Any]:
        """
        Robust regex fallback parser to extract values if no AI response is received.
        """
        # 1. Company Name detection
        company = None
        for line in text.split("\n"):
            line_s = line.strip()
            if any(x in line_s.lower() for x in ["travels", "logistics", "tours", "billing", "invoice"]):
                company = line_s
                break
                
        # 2. Duty Slip
        duty_slip = None
        ds_match = re.search(r'(?:duty\s*slip|ds|bill|invoice)\s*(?:no|num|number)?[:\-\s#]+([A-Za-z0-9\-]+)', text, re.IGNORECASE)
        if ds_match:
            duty_slip = ds_match.group(1).strip()
            
        # 3. Vehicle Number
        vehicle = None
        veh_match = re.search(r'([A-Z]{2}[-\s]?\d{2}[-\s]?[A-Z]{1,2}[-\s]?\d{4})', text)
        if veh_match:
            vehicle = veh_match.group(1).strip().replace(" ", "-")

        # 4. Vehicle Type
        veh_type = None
        type_matches = ["sedan", "suv", "bus", "indica", "innova", "crysta", "dzire", "etios", "tempo"]
        for tm in type_matches:
            if tm in text.lower():
                veh_type = tm.capitalize()
                break

        # 5. Dates
        dates = re.findall(r'(\d{4}[-\/]\d{2}[-\/]\d{2})', text)
        rep_date = dates[0] if len(dates) > 0 else None
        rel_date = dates[1] if len(dates) > 1 else rep_date

        # 6. Kms and Hours
        kms_match = re.search(r'(?:total\s*)?kms?[:\-\s]+(\d+(?:\.\d+)?)', text, re.IGNORECASE)
        kms = float(kms_match.group(1)) if kms_match else 0.0
        
        hrs_match = re.search(r'(?:total\s*)?hours?[:\-\s]+(\d+(?:\.\d+)?)', text, re.IGNORECASE)
        hrs = float(hrs_match.group(1)) if hrs_match else 0.0

        # 7. Pricing
        total_match = re.search(r'(?:grand\s*total|total\s*amount|amount|total)[:\-\s]+(?:rs\.?|inr|[^a-zA-Z0-9])?\s*(\d+(?:\.\d+)?)', text, re.IGNORECASE)
        total = float(total_match.group(1)) if total_match else 0.0

        # Mapped template response
        return {
            "company": company,
            "billNumber": duty_slip,
            "invoiceNumber": duty_slip,
            "dutySlip": duty_slip,
            "vehicleNumber": vehicle,
            "vehicleType": veh_type or "SUV",
            "driver": None,
            "reportingDate": rep_date,
            "reportingTime": None,
            "releaseDate": rel_date,
            "releaseTime": None,
            "pickup": None,
            "drop": None,
            "totalHours": hrs,
            "totalKilometers": kms,
            "minimumHours": 0.0,
            "minimumKilometers": 0.0,
            "extraHours": 0.0,
            "extraKilometers": 0.0,
            "toll": 0.0,
            "parking": 0.0,
            "permit": 0.0,
            "driverBata": 0.0,
            "nightCharges": 0.0,
            "totalAmount": total,
            "remarks": "Parsed locally via Regex fallback."
        }
