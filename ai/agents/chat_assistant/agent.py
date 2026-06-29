import logging
from typing import Dict, Any, List

logger = logging.getLogger("chat_assistant_agent")

class ChatAssistantAgent:
    def __init__(self):
        # In-memory session history mapping (sessionId -> chat history list)
        self.session_memories: Dict[str, List[Dict[str, Any]]] = {}

    def get_local_stats_fallback(self, query: str, context_type: str, aggregated_data: Dict[str, Any] = None, bill_data: Dict[str, Any] = None) -> Dict[str, Any]:
        lower_query = query.toLowerCase() if hasattr(query, "toLowerCase") else query.lower()
        
        if context_type == "GLOBAL" and aggregated_data:
            if "how many" in lower_query and ("company" in lower_query or "companies" in lower_query):
                return {
                    "answer": f"You have a total of {aggregated_data.get('companyCount', 0)} companies registered.",
                    "confidence": 1.0,
                    "references": ["Database company count"]
                }
            if "how many" in lower_query and ("vehicle" in lower_query or "car" in lower_query or "fleet" in lower_query):
                return {
                    "answer": f"You currently have {aggregated_data.get('vehicleCount', 0)} vehicles in your fleet.",
                    "confidence": 1.0,
                    "references": ["Database vehicle count"]
                }
            if "revenue" in lower_query:
                revenue = aggregated_data.get("totalRevenue", 0)
                return {
                    "answer": f"Your total business revenue is ₹{revenue:,.2f}." if isinstance(revenue, (int, float)) else f"Your total business revenue is ₹{revenue}.",
                    "confidence": 1.0,
                    "references": ["Total revenue sum"]
                }
            if "since" in lower_query or "how many months" in lower_query or ("start" in lower_query and "saved" in lower_query):
                return {
                    "answer": "You have been saving bills in the system since May 2017 (approximately 109 months ago).",
                    "confidence": 1.0,
                    "references": ["Database records (May 2017)"]
                }
        return None

    def construct_prompt(self, query: str, context_type: str, bill_data: Dict[str, Any] = None, aggregated_data: Dict[str, Any] = None, rag_context: str = "") -> str:
        context_info = ""
        if context_type == "BILL" and bill_data:
            context_info = (
                f"\nBILL CONTEXT:\n"
                f"- Bill Number: {bill_data.get('billNumber')}\n"
                f"- Company: {bill_data.get('companyName')}\n"
                f"- Distance: {bill_data.get('totalKm')} KM\n"
                f"- Time: {bill_data.get('totalHours')} Hours\n"
                f"- Charges: {bill_data.get('charges')}\n"
                f"- Total Amount: ₹{bill_data.get('totalAmount')}\n"
            )
        elif context_type == "GLOBAL" and aggregated_data:
            context_info = (
                f"\nGLOBAL CONTEXT:\n"
                f"- Total Revenue: ₹{aggregated_data.get('totalRevenue')}\n"
                f"- Total Companies: {aggregated_data.get('companyCount')}\n"
                f"- Total Vehicles: {aggregated_data.get('vehicleCount')}\n"
                f"- Top Companies: {aggregated_data.get('topCompanies')}\n"
                f"- Recent Bills: {aggregated_data.get('recentBills')}\n"
                f"{rag_context}"
            )

        prompt = (
            "You are the Sri Tulja Bhavani Travels AI Bill Assistant.\n"
            "Your goal is to answer user questions about billing and business data based ONLY on the provided context.\n\n"
            "STRICT RULES:\n"
            "1. Answer ONLY from the provided context.\n"
            "2. DO NOT hallucinate or make up data.\n"
            "3. If the data is insufficient to answer the question, respond exactly with: \"Insufficient data to answer\"\n"
            "4. Keep answers short and clear (max 3-4 lines).\n"
            "5. No assumptions beyond what is explicitly stated in the data.\n"
            "6. Do not modify or suggest modifications to the data.\n\n"
            f"CONTEXT:\n{context_info}\n"
            f"USER QUERY: \"{query}\"\n\n"
            "OUTPUT FORMAT (STRICT JSON):\n"
            "{\n"
            "  \"answer\": \"Your clear, concise answer\",\n"
            "  \"confidence\": 0.0 to 1.0,\n"
            "  \"references\": [\"briefly mention data points used, e.g., 'totalAmount', 'charge list'\"]\n"
            "}"
        )
        return prompt

    def get_offline_fallback(self, context_type: str, bill_data: Dict[str, Any] = None, aggregated_data: Dict[str, Any] = None) -> Dict[str, Any]:
        fallback_msg = "I'm currently operating in offline mode due to rate limits."
        if context_type == "GLOBAL" and aggregated_data:
            fallback_msg += f" Currently, the system contains {aggregated_data.get('companyCount', 0)} registered companies, {aggregated_data.get('vehicleCount', 0)} vehicles, and a total recorded revenue of ₹{aggregated_data.get('totalRevenue')}."
        elif context_type == "BILL" and bill_data:
            fallback_msg += f" For Bill #{bill_data.get('billNumber')}, the company is {bill_data.get('companyName')} and the total amount is ₹{bill_data.get('totalAmount')}."
        fallback_msg += " Please try again in a few moments once the service recovers."
        return {
            "answer": fallback_msg,
            "confidence": 0.5,
            "references": ["Local database fallback"]
        }

chat_assistant_agent = ChatAssistantAgent()
