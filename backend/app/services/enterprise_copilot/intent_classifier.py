import re
import logging

logger = logging.getLogger("intent_classifier")

class IntentClassifier:
    @staticmethod
    def classify_intent(query: str) -> str:
        """
        Classifies user query intent using regex keyword matching.
        """
        q = query.strip().lower()
        
        # 1. Explain Bill
        if any(w in q for w in ["explain bill", "why was this bill", "flagged", "mismatch", "which field caused", "explain slip", "explain duty"]):
            return "EXPLAIN_BILL"
            
        # 2. Search Bills
        if any(w in q for w in ["search", "show bills", "find bills", "find invoices", "find trips", "trips in", "above", "below ₹", "exceeded"]):
            return "SEARCH_BILLS"
            
        # 3. Compare Bills
        if "compare" in q:
            return "COMPARE_BILLS"

        # 4. Learning Insights
        if any(w in q for w in ["learned", "layout pattern", "company template", "preferred labels", "spatial rules", "vehicle rules"]):
            return "LEARNING_INSIGHTS"

        # 5. Validation Help
        if any(w in q for w in ["validation", "rule failed", "why error", "why warning"]):
            return "VALIDATION_HELP"

        # 6. Analytics
        if any(w in q for w in ["top customer", "most corrected", "highest revenue", "monthly revenue", "reviewer productivity", "reviewer activity", "pending bills", "revenue stats"]):
            return "ANALYTICS"

        return "GENERAL"
