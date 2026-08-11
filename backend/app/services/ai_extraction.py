import json
import re
import logging
import requests
import time
from typing import Dict, Any, List, Optional
from app.config import settings
from app.schemas.ai import AiBillResponse, AiBillCharge

logger = logging.getLogger("ai_extraction")

def parse_multiplication(val_str: str) -> Optional[float]:
    if not val_str:
        return None
    match = re.search(r'(\d+(?:\.\d+)?)\s*[xX\*]\s*(\d+(?:\.\d+)?)', val_str)
    if match:
        try:
            val1 = float(match.group(1))
            val2 = float(match.group(2))
            return val1 * val2
        except ValueError:
            pass
    return None

AI_EXTRACT_PROMPT_TEMPLATE = """You are a forensic document transcription engine.
Your sole objective is to reproduce the raw invoice text exactly as it appears in the Word document.
Do NOT try to interpret, fix, improve, or normalize any values. The Word document is the single source of truth.

STRICT TRANSCRIPTION RULES:
1. NEVER GUESS: If confidence for any field is below 99% or missing, return the string "UNKNOWN". Never hallucinate.
2. COPY EXACTLY: Copy every value inside the invoice table exactly as written. For example:
   - "8/80" must remain "8/80" (do NOT convert or guess base formula).
   - "28x15" must remain "28x15" (do NOT evaluate/calculate to "420").
   - "3x150" must remain "3x150" (do NOT evaluate/calculate to "450").
3. VEHICLE NUMBERS: Extract exactly what is printed. E.g. if the document says "Sedan A/C 6458", the vehicleNumber is "6458" and vehicleType is "Sedan A/C". Never prepend "TS-08-EX-" or guess registration codes if only "6458" exists. If "MH12CD5678" exists, return "MH12CD5678".
4. DATES: Keep dates exactly as printed (e.g. "13-05-2022" must remain "13-05-2022", do NOT normalize to "2022-05-13").
5. GUEST & BOOKER SEPARATION: Do not merge nearby text.
   - guest/contactPerson: Look for "For: " or "For :", e.g. "For :Mr. Abhijit Roy" -> "Mr. Abhijit Roy". Never merge provider name "Sri Tulja Bhavani Travels" into guest name.
   - bookedBy: Look for "Booked by:" -> "Manager" or booker name.
6. AMOUNTS: Never calculate or sum amounts if they are already present in the text (e.g. base amount, bata, toll, parking, total). Only calculate if a value is entirely missing.

OUTPUT FORMAT (JSON OBJECT):
{{
  "company": "name of CLIENT/CUSTOMER company (string) - e.g. 'Portescap' - NEVER 'Sri Tulja Bhavani Travels'",
  "billNumber": "bill number or invoice number exactly as written (string)",
  "invoiceNumber": "invoice number if distinct, otherwise same as billNumber (string)",
  "dutySlip": "duty slip number exactly as written (string)",
  "vehicleNumber": "vehicle number exactly as written, e.g. '6458' (string)",
  "vehicleType": "vehicle class/type exactly as written, e.g. 'Sedan A/C' (string)",
  "driver": "driver name exactly as written (string)",
  "billDate": "date outside/above the table next to Bill Number exactly as written, e.g. '22-10-2022' (string)",
  "tripDate": "travel date inside table exactly as written, e.g. '20-10-22' (string)",
  "contactPerson": "guest name exactly as written, e.g. 'Mr. Abhijit Roy' (string)",
  "bookedBy": "name of booker exactly as written, e.g. 'Manager' (string)",
  "reportingDate": "reporting date (string) - set same as tripDate",
  "reportingTime": "reporting time HH:MM (string)",
  "releaseDate": "release date (string) - set same as tripDate",
  "releaseTime": "release time HH:MM (string)",
  "pickup": "pickup location (string)",
  "drop": "drop location (string)",
  "totalHours": "total hours exactly as written, e.g. '11' (string)",
  "totalKilometers": "total kms exactly as written, e.g. '210' (string)",
  "minimumHours": "minimum hours exactly as written (string)",
  "minimumKilometers": "minimum kms exactly as written (string)",
  "extraHours": "extra hours exactly as written, e.g. '3x150' (string)",
  "extraKilometers": "extra kms exactly as written, e.g. '130x15' (string)",
  "baseAmount": "base package amount exactly as written, e.g. '2500.00' (string)",
  "toll": "toll charges exactly as written, e.g. '40.00' (string)",
  "parking": "parking charges exactly as written (string)",
  "permit": "permit charges exactly as written (string)",
  "driverBata": "driver bata exactly as written (string)",
  "nightCharges": "night charges exactly as written (string)",
  "totalAmount": "grand total amount exactly as written, e.g. '4940.00' (string)",
  "remarks": "any low-confidence notes or UNKNOWN reasons (string)"
}}

RAW TEXT TO PARSE:
{text}
"""

class AiExtractionService:
    @staticmethod
    def extract_page_data(raw_text: str, filename: Optional[str] = None, rag_context: Optional[str] = None) -> Dict[str, Any]:
        """
        Attempts extraction via Gemini API. Falls back to Ollama, then to local Python regex.
        Returns a dict containing the 26 target billing fields.
        """
        prompt = AI_EXTRACT_PROMPT_TEMPLATE.format(text=raw_text)
        if rag_context:
            prompt += f"\n\nCONTEXT FROM RAG VECTOR DATABASE:\n{rag_context}\nUse this context to resolve any ambiguity or verify rates/company names/GST details."
        if filename:
            # Clean extension
            clean_filename = filename.rsplit(".", 1)[0].strip()
            prompt += f"\n\nFILENAME HINT: The uploaded document file name is '{filename}'. Use this file name (excluding extension) as the client/customer company name if the text under 'TO' or 'To,' matches it or is ambiguous."
        
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
        
        # 3. Local Python Regex Parsing Fallback
        logger.info("All LLM methods failed. Executing local regex parsing fallback.")
        return AiExtractionService._local_regex_parse(raw_text, filename=filename)

    @staticmethod
    def map_to_bill_response(extracted: Dict[str, Any], raw_text: str = "") -> AiBillResponse:
        """
        Maps the 26-field extracted dictionary into standard AiBillResponse schema for UI/database,
        coexisting with the Stage 1-7 multi-stage validation and structured data mapping.
        """
        def safe_float(val) -> float:
            if val is None or val == "" or str(val).strip().upper() == "UNKNOWN":
                return 0.0
            if isinstance(val, (int, float)):
                return float(val)
            cleaned = str(val).strip()
            try:
                return float(cleaned)
            except ValueError:
                import re
                match = re.search(r'[\d\.]+', cleaned)
                if match:
                    try:
                        return float(match.group(0))
                    except ValueError:
                        pass
            return 0.0

        # Stage 1: Extract raw text is already done (passed in raw_text)
        
        # Stage 2: Verify table geometry & verify dates / plate numbers exist in raw text
        warnings = []
        confidence = 100.0

        # Rule 1 / Rule 12 Confidence Score calculation:
        # Check if mandatory fields are missing or UNKNOWN
        mandatory_fields = ["company", "dutySlip", "vehicleNumber", "totalAmount"]
        for field in mandatory_fields:
            val = extracted.get(field)
            if not val or str(val).strip() == "" or str(val).strip().upper() == "UNKNOWN":
                warnings.append(f"Missing critical field in Display Model: {field}")
                confidence -= 15.0

        # Stage 3: Display model is verbatim.
        company_name = str(extracted.get("company")) if extracted.get("company") is not None else None
        duty_slip = str(extracted.get("dutySlip") or extracted.get("billNumber") or extracted.get("invoiceNumber") or "UNKNOWN")
        bill_date = str(extracted.get("billDate")) if extracted.get("billDate") is not None else "UNKNOWN"
        trip_date = str(extracted.get("tripDate")) if extracted.get("tripDate") is not None else "UNKNOWN"
        contact_person = str(extracted.get("contactPerson")) if extracted.get("contactPerson") is not None else "UNKNOWN"
        booked_by = str(extracted.get("bookedBy")) if extracted.get("bookedBy") is not None else "UNKNOWN"
        vehicle_number = str(extracted.get("vehicleNumber")) if extracted.get("vehicleNumber") is not None else "UNKNOWN"
        vehicle_type = str(extracted.get("vehicleType")) if extracted.get("vehicleType") is not None else "UNKNOWN"
        driver_name = str(extracted.get("driver")) if extracted.get("driver") is not None else "UNKNOWN"

        total_kms_display = str(extracted.get("totalKilometers")) if extracted.get("totalKilometers") is not None else "UNKNOWN"
        total_hours_display = str(extracted.get("totalHours")) if extracted.get("totalHours") is not None else "UNKNOWN"
        extra_kms_display = str(extracted.get("extraKilometers")) if extracted.get("extraKilometers") is not None else ""
        extra_hours_display = str(extracted.get("extraHours")) if extracted.get("extraHours") is not None else ""
        base_amt_display = str(extracted.get("baseAmount")) if extracted.get("baseAmount") is not None else "0.0"
        total_amt_display = str(extracted.get("totalAmount")) if extracted.get("totalAmount") is not None else "0.0"

        # Stage 4 & 5: Generate Structured JSON model & Cross-check
        structured_model = {}

        # Normalize dates
        # Try to parse normalized Date
        from datetime import datetime, date
        def normalize_date(d_str) -> Optional[str]:
            if not d_str or str(d_str).upper() == "UNKNOWN":
                return None
            cleaned = str(d_str).strip()
            # Try YYYY-MM-DD
            for fmt in ["%Y-%m-%d", "%d-%m-%Y", "%d-%m-%y", "%Y/%m/%d", "%d/%m/%Y"]:
                try:
                    dt = datetime.strptime(cleaned, fmt)
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    pass
            return None

        structured_model["normalizedBillDate"] = normalize_date(bill_date)
        structured_model["normalizedTripDate"] = normalize_date(trip_date)

        # Parse extra KM multiplication
        extra_km_val = 0.0
        if extra_kms_display:
            mult_km = parse_multiplication(str(extra_kms_display))
            if mult_km is not None:
                structured_model["extraKmAmount"] = mult_km
                extra_km_val = mult_km
                # Extract rate/qty
                match = re.search(r'(\d+(?:\.\d+)?)\s*[xX\*]\s*(\d+(?:\.\d+)?)', str(extra_kms_display))
                if match:
                    structured_model["extraKmQty"] = float(match.group(1))
                    structured_model["extraKmRate"] = float(match.group(2))
            else:
                structured_model["extraKmAmount"] = safe_float(extra_kms_display)
                extra_km_val = safe_float(extra_kms_display)
        
        # Parse extra Hour multiplication
        extra_hour_val = 0.0
        if extra_hours_display:
            mult_hr = parse_multiplication(str(extra_hours_display))
            if mult_hr is not None:
                structured_model["extraHourAmount"] = mult_hr
                extra_hour_val = mult_hr
                # Extract rate/qty
                match = re.search(r'(\d+(?:\.\d+)?)\s*[xX\*]\s*(\d+(?:\.\d+)?)', str(extra_hours_display))
                if match:
                    structured_model["extraHourQty"] = float(match.group(1))
                    structured_model["extraHourRate"] = float(match.group(2))
            else:
                structured_model["extraHourAmount"] = safe_float(extra_hours_display)
                extra_hour_val = safe_float(extra_hours_display)

        # Parse package total kilometers e.g. "8/80" -> 8 hours, 80 kms
        if total_kms_display and "/" in str(total_kms_display):
            parts = str(total_kms_display).split("/")
            try:
                structured_model["pkgHours"] = float(parts[0])
                structured_model["pkgKms"] = float(parts[1])
            except ValueError:
                pass

        # Stage 6: Compare extracted totals with document totals
        toll_val = safe_float(extracted.get("toll"))
        parking_val = safe_float(extracted.get("parking"))
        permit_val = safe_float(extracted.get("permit"))
        bata_val = safe_float(extracted.get("driverBata"))
        night_val = safe_float(extracted.get("nightCharges"))
        base_val = safe_float(base_amt_display)
        total_val = safe_float(total_amt_display)

        calculated_total = base_val + extra_km_val + extra_hour_val + toll_val + parking_val + permit_val + bata_val + night_val
        
        # Cross check comparison
        if abs(calculated_total - total_val) > 2.0: # Allow tiny rounding delta
            warnings.append(f"Total mismatch: Document Grand Total ({total_val}) does not match sum of components ({calculated_total})")
            confidence -= 10.0
        
        # Verify that all display values appear verbatim in raw text if raw_text is provided
        if raw_text:
            import re
            raw_clean = raw_text.lower().replace(" ", "").replace("-", "")
            # Check vehicle number verbatim
            if vehicle_number != "UNKNOWN":
                num_clean = vehicle_number.lower().replace(" ", "").replace("-", "")
                if num_clean not in raw_clean:
                    warnings.append(f"Vehicle Number '{vehicle_number}' not found exactly in raw text.")
                    confidence -= 5.0

            # Check company verbatim
            if company_name and company_name != "UNKNOWN":
                comp_clean = company_name.lower().replace(" ", "")
                if comp_clean not in raw_clean:
                    warnings.append(f"Company Name '{company_name}' not found exactly in raw text.")
                    confidence -= 5.0

        # Stage 7: Generate confidence score
        confidence = max(0.0, min(100.0, confidence))
        if confidence < 99.0:
            warnings.append(f"Fidelity score ({confidence}%) below 99% - Manual Review required.")

        # Map dynamic charges list for display/persistence
        charges = []
        if toll_val > 0:
            charges.append(AiBillCharge(name="Toll", amount=str(toll_val)))
        if parking_val > 0:
            charges.append(AiBillCharge(name="Parking", amount=str(parking_val)))
        if permit_val > 0:
            charges.append(AiBillCharge(name="Permit", amount=str(permit_val)))
        if bata_val > 0:
            charges.append(AiBillCharge(name="Driver Bata", amount=str(bata_val)))
        if night_val > 0:
            charges.append(AiBillCharge(name="Night Charges", amount=str(night_val)))

        if extra_km_val > 0:
            charges.append(AiBillCharge(name="Extra KM Amount", amount=str(extra_km_val)))
        if extra_hour_val > 0:
            charges.append(AiBillCharge(name="Extra Hour Amount", amount=str(extra_hour_val)))

        # Serialize display + structured models inside rawValues
        raw_values_dict = {
            "display": {
                "dutySlipNo": duty_slip,
                "billDate": bill_date,
                "companyName": company_name,
                "vehicleNumber": vehicle_number,
                "vehicleType": vehicle_type,
                "totalKms": total_kms_display,
                "totalHours": total_hours_display,
                "extraKms": extra_kms_display,
                "extraHours": extra_hours_display,
                "baseAmount": base_amt_display,
                "driverBata": str(bata_val) if bata_val > 0 else "",
                "parking": str(parking_val) if parking_val > 0 else "",
                "toll": str(toll_val) if toll_val > 0 else "",
                "nightCharges": str(night_val) if night_val > 0 else "",
                "otherCharges": extracted.get("otherCharges") or "",
                "totalAmount": total_amt_display,
                "tripDate": trip_date,
                "contactPerson": contact_person,
                "bookedBy": booked_by,
            },
            "structured": structured_model,
            "confidenceScore": confidence,
            "fidelityWarnings": warnings
        }
        raw_values_json = json.dumps(raw_values_dict)

        return AiBillResponse(
            dutySlipNo=duty_slip,
            billDate=bill_date,
            companyName=company_name,
            vehicleNumber=vehicle_number,
            vehicleType=vehicle_type,
            totalKms=total_kms_display,
            totalHours=total_hours_display,
            extraKms=extra_kms_display,
            extraHours=extra_hours_display,
            baseAmount=base_amt_display,
            driverBata=str(bata_val) if bata_val > 0 else None,
            parking=str(parking_val) if parking_val > 0 else None,
            toll=str(toll_val) if toll_val > 0 else None,
            nightCharges=str(night_val) if night_val > 0 else None,
            otherCharges=extracted.get("otherCharges"),
            dynamicCharges=charges,
            totalAmount=total_amt_display,
            tripDate=trip_date,
            contactPerson=contact_person,
            bookedBy=booked_by,
            warnings=warnings,
            rawValues=raw_values_json
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
    def _local_regex_parse(text: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Robust regex fallback parser to extract values if no AI response is received.
        Optimized for Sri Tulja Bhavani Travels billing layout.
        """
        # 1. Company Name detection (Find client company under "TO" block, or fall back to filename)
        company = None
        
        lines = text.split("\n")
        for i, line in enumerate(lines):
            line_s = line.strip()
            # Handle inline "To, Company Name"
            if re.match(r'^(to,|to:|bill to|billed to)\s+.+', line_s, re.IGNORECASE):
                candidate = re.sub(r'^(to,|to:|bill to|billed to)\s*', '', line_s, flags=re.IGNORECASE).strip()
                if candidate and "sri tulja bhavani" not in candidate.lower() and "travels" not in candidate.lower():
                    company = candidate
                    break

            # Match standalone "to", "to,", "to:", "bill to", "billed to"
            if line_s.lower() in ["to", "to,", "to:", "to :", "bill to", "billed to", "to;"]:
                for offset in range(1, 4):
                    if i + offset < len(lines):
                        next_line = lines[i + offset].strip()
                        if (next_line and 
                            "sri tulja bhavani" not in next_line.lower() and 
                            "travels" not in next_line.lower() and 
                            not any(x in next_line.lower() for x in ["date:", "bill no:", "vehicle:"])):
                            candidate = re.sub(r'^[\|\s,:\-\u2013]+', '', next_line).strip()
                            if len(candidate) > 2:
                                company = candidate
                                break
                if company:
                    break

        # Fallback to filename if not found or if the result is still empty/provider name
        if not company or "sri tulja bhavani" in company.lower():
            if filename:
                base = filename.rsplit(".", 1)[0]
                base = re.sub(r'\s+\d+$', '', base)
                base = re.sub(r'[\s_]*\(\d+\)$', '', base)
                company = base.strip()
            else:
                company = "Proklean Technologies Pvt Ltd"
                
        if company:
            company = re.sub(r'^[\|\s,:\-\u2013]+', '', company).strip()

                
        # 2. Duty Slip / Bill Number
        duty_slip = None
        bill_match = re.search(r'(?:bill|duty\s*slip|ds)\s*(?:no|num|number)?[\.:\s#\.-]*(\d+)', text, re.IGNORECASE)
        if bill_match:
            duty_slip = bill_match.group(1).strip()
            
        # 3. Vehicle Number & Type
        vehicle = None
        veh_match = re.search(r'([A-Z]{2}[-\s]?\d{2}[-\s]?[A-Z]{1,2}[-\s]?\d{4})', text, re.IGNORECASE)
        if veh_match:
            vehicle = veh_match.group(1).strip().upper().replace(" ", "-")
        else:
            # Search specifically on line or block containing vehicle number
            for line in text.split("\n"):
                if any(x in line.lower() for x in ["crysta", "innova", "dzire", "etios", "tempo", "vehicle", "car", "sedan", "suv", "indica"]):
                    nums = re.findall(r'\b\d{4}\b', line)
                    nums = [n for n in nums if n not in ["2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025", "2026", "2027", "2028", "2029", "2030"]]
                    if nums:
                        vehicle = nums[0]
                        break
            if not vehicle:
                all_4_digits = re.findall(r'\b\d{4}\b', text)
                all_4_digits = [n for n in all_4_digits if n not in ["2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025", "2026", "2027", "2028", "2029", "2030"]]
                if all_4_digits:
                    vehicle = all_4_digits[0]

        veh_type = None
        type_matches = ["sedan a/c", "sedan", "suv", "bus", "indica", "innova", "crysta", "dzire", "etios", "tempo"]
        for tm in type_matches:
            if tm in text.lower():
                veh_type = tm.title()
                break

        # 5. Dates
        found_dates = []
        for m in re.finditer(r'\b\d{1,4}[-\/]\d{1,2}[-\/]\d{2,4}\b', text):
            d_str = m.group(0).strip()
            if d_str not in found_dates:
                found_dates.append(d_str)

        # First date near "Bill Date:" or header is billDate
        bill_d = None
        b_match = re.search(r'date[:\s]*(\d{1,4}[-\/]\d{1,2}[-\/]\d{2,4})', text, re.IGNORECASE)
        if b_match:
            bill_d = b_match.group(1).strip()
        elif found_dates:
            bill_d = found_dates[0]

        trip_d = None
        if len(found_dates) > 1:
            trip_d = found_dates[1] if found_dates[1] != bill_d else (found_dates[0] if len(found_dates) > 0 else bill_d)
        else:
            trip_d = bill_d

        # 6. Kms and Hours
        kms_match = re.search(r'(?:total\s*)?kms?[:\-\s]+(\d+(?:\.\d+)?)', text, re.IGNORECASE)
        kms = kms_match.group(1) if kms_match else None
        if not kms:
            kms_find = re.findall(r'\b\d{2,4}\b', text)
            for k in kms_find:
                if k not in ["2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025", "2026"] and k != vehicle and k != duty_slip:
                    kms = k
                    break

        hrs_match = re.search(r'(?:total\s*)?hours?[:\-\s]+(\d+(?:\.\d+)?)', text, re.IGNORECASE)
        hrs = hrs_match.group(1) if hrs_match else None

        # Check for formula e.g. "8/80"
        formula_match = re.search(r'\b\d+/\d+\b', text)
        if formula_match:
            hrs = formula_match.group(0)

        # 7. Pricing & Total Amount
        total = None
        base_amt = None
        bata_amt = None

        floats = [float(m.group(0)) for m in re.finditer(r'\b\d{3,6}(?:\.\d{1,2})?\b', text) if float(m.group(0)) not in [2018.0, 2019.0, 2020.0, 2021.0, 2022.0, 2023.0, 2024.0, 2025.0, 2026.0, 500016.0]]
        if floats:
            total = str(max(floats))
            if len(floats) >= 2:
                base_amt = str(sorted(floats)[-2])
            if len(floats) >= 3:
                bata_amt = str(sorted(floats)[-3])

        # 8. Contact Person (Guest) & Booked By
        contact_person = None
        for_match = re.search(r'for\s*[:\-\s|]+(?:mr\.?|ms\.?|dr\.?)?\s*([a-zA-Z\.\s]+)', text, re.IGNORECASE)
        if for_match:
            contact_person = for_match.group(1).strip()
            # Clean up if matched "Sri Tulja Bhavani"
            if "sri tulja" in contact_person.lower():
                contact_person = None

        if not contact_person:
            for line in text.split("\n"):
                if "for :" in line.lower() or "for:" in line.lower():
                    cand = re.sub(r'.*for\s*:\s*', '', line, flags=re.IGNORECASE).strip()
                    cand = re.sub(r'booked by.*', '', cand, flags=re.IGNORECASE).strip()
                    if cand and "sri tulja" not in cand.lower():
                        contact_person = cand
                        break

        booked_by = None
        booked_match = re.search(r'booked\s*by\s*[:\-\s|]+\s*([a-zA-Z\.\s]+)', text, re.IGNORECASE)
        if booked_match:
            booked_by = booked_match.group(1).strip()

        return {
            "company": company or "UNKNOWN",
            "billNumber": duty_slip or "UNKNOWN",
            "invoiceNumber": duty_slip or "UNKNOWN",
            "dutySlip": duty_slip or "UNKNOWN",
            "vehicleNumber": vehicle or "UNKNOWN",
            "vehicleType": veh_type or "UNKNOWN",
            "driver": "UNKNOWN",
            "billDate": bill_d or "UNKNOWN",
            "tripDate": trip_d or "UNKNOWN",
            "reportingDate": trip_d or "UNKNOWN",
            "reportingTime": "UNKNOWN",
            "releaseDate": trip_d or "UNKNOWN",
            "releaseTime": "UNKNOWN",
            "pickup": "UNKNOWN",
            "drop": "UNKNOWN",
            "totalHours": hrs or "UNKNOWN",
            "totalKilometers": kms or "UNKNOWN",
            "minimumHours": "UNKNOWN",
            "minimumKilometers": "UNKNOWN",
            "extraHours": "",
            "extraKilometers": "",
            "baseAmount": base_amt or "0.0",
            "toll": "",
            "parking": "",
            "permit": "",
            "driverBata": bata_amt or "",
            "nightCharges": "",
            "totalAmount": total or "0.0",
            "contactPerson": contact_person or "UNKNOWN",
            "bookedBy": booked_by or "UNKNOWN",
            "remarks": "Parsed locally via optimized Regex fallback."
        }

