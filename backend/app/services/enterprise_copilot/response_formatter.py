import re
from typing import List, Dict, Any
from app.services.enterprise_copilot.copilot_models import CopilotChatResponse

class ResponseFormatter:
    @staticmethod
    def format_response(text: str, intent: str, bill_id: int = None) -> CopilotChatResponse:
        """
        Parses text output and formats it as a structured CopilotChatResponse.
        Extracts references and estimates a confidence score from the response content.
        """
        # Find references to duty slips or bills (e.g. DS-4001, BILL-12345)
        references = re.findall(r'\b(?:DS|BILL)-\d+\b', text)
        if bill_id and f"Bill #{bill_id}" not in references:
            references.append(f"Bill #{bill_id}")

        # Extract confidence score (e.g. 95% or 0.95)
        conf_match = re.search(r'\b(\d{2,3})%\b', text)
        confidence = 0.95
        if conf_match:
            confidence = float(conf_match.group(1)) / 100.0

        # Construct action intent for the UI if relevant
        action = None
        if intent == "SEARCH_BILLS":
            action = {"type": "FILTER_GRID", "query": text}
        elif intent == "EXPLAIN_BILL" and bill_id:
            action = {"type": "HIGHLIGHT_WORKSPACE", "billId": bill_id}

        return CopilotChatResponse(
            answer=text,
            confidence=confidence,
            references=list(set(references)),
            action=action
        )
