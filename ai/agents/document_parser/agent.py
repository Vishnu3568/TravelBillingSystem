import re
from datetime import datetime
from typing import Dict, Any, List

class DocumentParserAgent:
    def construct_parser_prompt(self, text: str) -> str:
        prompt = (
            "You are a professional Travel Invoicing Specialist.\n"
            "Your task is to parse the following raw text extracted from a transport duty slip/bill/invoice and return a structured JSON array of parsed bills.\n\n"
            "STRICT RULES:\n"
            "1. Extract all bills/duty slips found in the text.\n"
            "2. Return a JSON array matching the specified format.\n"
            "3. For dates, format as \"YYYY-MM-DD\". If only day/month is provided, assume current year or logical context.\n"
            "4. Extract all line item charges (e.g., driver bata, toll, parking, night charges, extra km charges, extra hour charges, base fare) into the \"dynamicCharges\" array.\n"
            "5. \"dynamicCharges\" must be a list of objects containing \"name\" (string) and \"amount\" (numeric).\n"
            "6. Convert all numeric values (totalKms, totalHours, totalAmount, amounts in dynamicCharges) to standard numbers.\n"
            "7. If data is missing for a field, use null or empty array/list.\n"
            "8. If there are any ambiguities, discrepancies, or missing mandatory values, add a warning message in the \"warnings\" array.\n"
            "9. Return ONLY valid JSON, no markdown formatting blocks.\n\n"
            "OUTPUT FORMAT (STRICT JSON ARRAY):\n"
            "[\n"
            "  {\n"
            "    \"dutySlipNo\": \"duty slip or bill number (string)\",\n"
            "    \"billDate\": \"YYYY-MM-DD (string)\",\n"
            "    \"companyName\": \"name of client company (string)\",\n"
            "    \"vehicleNumber\": \"registration plate number (string)\",\n"
            "    \"vehicleType\": \"car type e.g., Sedan, SUV, Bus, Indica (string)\",\n"
            "    \"totalKms\": 0.0,\n"
            "    \"totalHours\": 0.0,\n"
            "    \"dynamicCharges\": [\n"
            "      { \"name\": \"charge name\", \"amount\": 0.0 }\n"
            "    ],\n"
            "    \"totalAmount\": 0.0,\n"
            "    \"warnings\": [\"warning messages if any\"]\n"
            "  }\n"
            "]\n\n"
            f"RAW TEXT:\n{text}"
        )
        return prompt

    def construct_company_prompt(self, text: str) -> str:
        prompt = (
            "You are a Data Extraction Assistant.\n"
            "Your task is to identify and extract all company/client profiles mentioned in the following text.\n\n"
            "STRICT RULES:\n"
            "1. Extract the name, address (if mentioned), and GST/Tax number (if mentioned) for each company.\n"
            "2. Return a JSON array matching the specified format.\n"
            "3. Clean and format the name, address, and GST number (remove extra spaces or noise).\n"
            "4. Return ONLY valid JSON, no markdown formatting blocks.\n\n"
            "OUTPUT FORMAT (STRICT JSON ARRAY):\n"
            "[\n"
            "  {\n"
            "    \"name\": \"Full Company Name (string, required)\",\n"
            "    \"address\": \"Company Address (string, optional/null)\",\n"
            "    \"gstNumber\": \"GSTIN / Tax Registration Number (string, optional/null)\"\n"
            "  }\n"
            "]\n\n"
            f"TEXT:\n{text}"
        )
        return prompt

    def construct_nl_search_prompt(self, query: str, current_date: str) -> str:
        prompt = (
            "You are a Database Query Assistant.\n"
            "Your task is to interpret a natural language search query for travel bills and translate it into a structured JSON filter config.\n\n"
            f"The current system date is: {current_date}.\n\n"
            "STRICT RULES:\n"
            "1. Interpret time-related expressions relative to the current date:\n"
            "   - \"this month\": from the first day of the current month to the current date or end of month.\n"
            "   - \"last month\": from the first to last day of the previous month.\n"
            "   - \"this year\": from January 1st of current year.\n"
            "   - \"yesterday\": date of the day before current date.\n"
            "   - \"last week\": 7 days preceding current date, or the previous calendar week.\n"
            "2. Identify company name or vehicle type if explicitly or implicitly mentioned (e.g., \"Indica bills\", \"Ashapura bills\").\n"
            "3. Identify price constraints: \"more than 5000\" -> minAmount: 5000, \"between 2000 and 4000\" -> minAmount: 2000, maxAmount: 4000.\n"
            "4. Identify distance constraints: \"kms over 500\" -> minKm: 500.\n"
            "5. Capture any other searchable terms as \"keywords\".\n"
            "6. Populate the \"summary\" field with a clear, user-friendly description of what was understood.\n"
            "7. Return ONLY valid JSON, no markdown formatting blocks.\n\n"
            "OUTPUT FORMAT (STRICT JSON):\n"
            "{\n"
            "  \"companyName\": \"extracted company name or null\",\n"
            "  \"vehicleType\": \"extracted vehicle type (e.g., Sedan, SUV, Bus) or null\",\n"
            "  \"minAmount\": null or numeric,\n"
            "  \"maxAmount\": null or numeric,\n"
            "  \"minKm\": null or numeric,\n"
            "  \"maxKm\": null or numeric,\n"
            "  \"dateFrom\": \"YYYY-MM-DD or null\",\n"
            "  \"dateTo\": \"YYYY-MM-DD or null\",\n"
            "  \"status\": \"extracted payment status or null\",\n"
            "  \"keywords\": [\"array of extra keywords/terms to search for\"],\n"
            "  \"summary\": \"Short user-friendly summary of the parsed criteria\"\n"
            "}\n\n"
            f"USER QUERY: \"{query}\""
        )
        return prompt

    def local_fallback_parse_bill(self, text: str) -> List[Dict[str, Any]]:
        clean_text = text or ""
        
        # Regex scans
        duty_slip_match = re.search(r"(?:duty\s*slip\s*no|slip\s*no|bill\s*no)[:\s]+([a-z0-9-]+)", clean_text, re.IGNORECASE)
        date_match = re.search(r"(?:date)[:\s]+([\d]{2}-[\d]{2}-[\d]{4}|[\d]{4}-[\d]{2}-[\d]{2})", clean_text, re.IGNORECASE)
        company_match = re.search(r"(?:to|company|client)[:\s]+([^\n\r]+)", clean_text, re.IGNORECASE)
        vehicle_no_match = re.search(r"(?:vehicle|car|reg)[:\s]+([a-z]{2}[-\s]*\d{2}[-\s]*[a-z0-9-\s]+)", clean_text, re.IGNORECASE)
        kms_match = re.search(r"(?:kms|km|distance)[:\s]+(\d+)", clean_text, re.IGNORECASE)
        hours_match = re.search(r"(?:hours|hrs|time)[:\s]+(\d+)", clean_text, re.IGNORECASE)
        
        charges = []
        bata_match = re.search(r"(?:driver\s*bata|bata)[:\s]+(\d+)", clean_text, re.IGNORECASE)
        if bata_match:
            charges.append({"name": "Driver Bata", "amount": float(bata_match.group(1))})
        
        toll_match = re.search(r"(?:toll|tolls)[:\s]+(\d+)", clean_text, re.IGNORECASE)
        if toll_match:
            charges.append({"name": "Toll", "amount": float(toll_match.group(1))})
            
        parking_match = re.search(r"(?:parking)[:\s]+(\d+)", clean_text, re.IGNORECASE)
        if parking_match:
            charges.append({"name": "Parking", "amount": float(parking_match.group(1))})
            
        amount_match = re.search(r"(?:total\s*amount|amount|total)[:\s]+(\d+)", clean_text, re.IGNORECASE)
        total_amount = float(amount_match.group(1)) if amount_match else (sum(c["amount"] for c in charges) or 1500.0)
        
        formatted_date = datetime.now().strftime("%Y-%m-%d")
        if date_match:
            d_str = date_match.group(1).strip()
            if "-" in d_str:
                parts = d_str.split("-")
                if len(parts[0]) == 2:
                    # DD-MM-YYYY -> YYYY-MM-DD
                    formatted_date = f"{parts[2]}-{parts[1]}-{parts[0]}"
                else:
                    formatted_date = d_str
                    
        return [
            {
                "dutySlipNo": duty_slip_match.group(1).strip().upper() if duty_slip_match else f"MOCK-DS-{datetime.now().strftime('%f')[:4]}",
                "billDate": formatted_date,
                "companyName": company_match.group(1).strip() if company_match else "Mock Transport Client Ltd",
                "vehicleNumber": vehicle_no_match.group(1).strip().upper() if vehicle_no_match else "KA-01-MC-9999",
                "vehicleType": "Indica" if "indica" in clean_text.lower() else ("SUV" if "suv" in clean_text.lower() else "Sedan"),
                "totalKms": float(kms_match.group(1)) if kms_match else 120.0,
                "totalHours": float(hours_match.group(1)) if hours_match else 8.0,
                "dynamicCharges": charges if charges else [{"name": "Base Amount", "amount": total_amount}],
                "totalAmount": total_amount,
                "warnings": ["Local Parsing Fallback (Gemini API Quota Exceeded/Rate Limited)"]
            }
        ]

    def local_fallback_extract_companies(self, text: str) -> List[Dict[str, Any]]:
        clean_text = text or ""
        company_match = re.search(r"(?:to|company|client)[:\s]+([^\n\r]+)", clean_text, re.IGNORECASE)
        gst_match = re.search(r"(?:gst|gstin)[:\s]+([a-z0-9]{15})", clean_text, re.IGNORECASE)
        return [
            {
                "name": company_match.group(1).strip() if company_match else "Mock Company Ltd",
                "address": "Extracted via local fallback address scanner",
                "gstNumber": gst_match.group(1).upper() if gst_match else "24MOCKGST1234F1Z"
            }
        ]

    def local_fallback_nl_search(self, query: str, current_date: str) -> Dict[str, Any]:
        lower_query = query.lower()
        filter_config = {
            "companyName": None,
            "vehicleType": None,
            "minAmount": None,
            "maxAmount": None,
            "minKm": None,
            "maxKm": None,
            "dateFrom": None,
            "dateTo": None,
            "status": None,
            "keywords": [],
            "summary": f"Local search fallback: \"{query}\""
        }

        if "ashapura" in lower_query:
            filter_config["companyName"] = "Ashapura"
        elif "bhavani" in lower_query:
            filter_config["companyName"] = "Sri Tulja Bhavani Travels"
            
        if "indica" in lower_query:
            filter_config["vehicleType"] = "Indica"
        elif "sedan" in lower_query:
            filter_config["vehicleType"] = "Sedan"
        elif "suv" in lower_query:
            filter_config["vehicleType"] = "SUV"

        above_match = re.search(r"(?:above|greater\s*than|over|>\s*)\s*(\d+)", lower_query)
        if above_match:
            filter_config["minAmount"] = float(above_match.group(1))
            
        below_match = re.search(r"(?:below|less\s*than|under|<\s*)\s*(\d+)", lower_query)
        if below_match:
            filter_config["maxAmount"] = float(below_match.group(1))

        # Date boundaries
        try:
            sys_date = datetime.strptime(current_date, "%Y-%m-%d")
        except Exception:
            sys_date = datetime.now()
            
        if "this month" in lower_query:
            filter_config["dateFrom"] = sys_date.replace(day=1).strftime("%Y-%m-%d")
            filter_config["dateTo"] = sys_date.strftime("%Y-%m-%d")
        elif "last month" in lower_query:
            # Handle previous month
            if sys_date.month == 1:
                prev_month = sys_date.replace(year=sys_date.year - 1, month=12, day=1)
                last_day = datetime(sys_date.year - 1, 12, 31)
            else:
                prev_month = sys_date.replace(month=sys_date.month - 1, day=1)
                import calendar
                _, last_day_num = calendar.monthrange(sys_date.year, sys_date.month - 1)
                last_day = sys_date.replace(month=sys_date.month - 1, day=last_day_num)
            filter_config["dateFrom"] = prev_month.strftime("%Y-%m-%d")
            filter_config["dateTo"] = last_day.strftime("%Y-%m-%d")

        return filter_config

document_parser_agent = DocumentParserAgent()
