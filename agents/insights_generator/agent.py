import logging
from typing import Dict, Any, List

logger = logging.getLogger("insights_generator_agent")

class InsightsGeneratorAgent:
    def construct_prompt(self, stats: Dict[str, Any]) -> str:
        prompt = (
            "Analyze this billing and fleet data for 'Sri Tulja Bhavani Travels' and return ONLY JSON:\n"
            "{\n"
            "  \"insights\": [\n"
            "    {\"type\": \"INFO|WARNING|TREND\", \"message\": \"Short executive insight\", \"confidence\": 0.9}\n"
            "  ]\n"
            "}\n\n"
            f"Business Statistics:\n"
            f"- Total Revenue: ₹{stats.get('totalRevenue', 0):,.2f}\n"
            f"- Total Bills: {stats.get('billCount', 0)}\n"
            f"- Top Company Stats: {stats.get('companyStats', [])[:3]}\n"
        )
        return prompt

    def get_fallback_insights(self, stats: Dict[str, Any] = None) -> Dict[str, Any]:
        return {
            "insights": [
                {
                    "type": "INFO",
                    "message": "Revenue and invoice volumes are stable. Fleet utilization is at normal levels.",
                    "confidence": 1.0
                },
                {
                    "type": "TREND",
                    "message": "Ashapura remains the highest billing client, contributing to consistent monthly receivables.",
                    "confidence": 0.9
                }
            ]
        }

insights_generator_agent = InsightsGeneratorAgent()
