import logging
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from app.models.bill import Bill
from app.models.learning import CorrectionHistory, CompanyPatterns, VehiclePatterns
from app.services.enterprise_copilot.conversation_memory import ConversationMemory
from app.services.enterprise_copilot.knowledge_retriever import KnowledgeRetriever
from app.services.enterprise_copilot.analytics_assistant import AnalyticsAssistant

logger = logging.getLogger("context_builder")

class ContextBuilder:
    @staticmethod
    def build_context(
        db: Session,
        query: str,
        session_id: str,
        bill_id: Optional[int],
        user_role: str,
        username: str
    ) -> Dict[str, Any]:
        """
        Collects active layout patterns, recent reviewer corrections,
        and database facts to provide rich evidence context for Copilot prompts.
        Applies strict RBAC filtering.
        """
        context = {
            "conversation_history": ConversationMemory.get_history_as_text(session_id),
            "role": user_role,
            "username": username,
            "bill_info": "",
            "knowledge_facts": [],
            "analytics_facts": []
        }

        # 1. Resolve Bill Context (check input or conversation history)
        active_bill_id = bill_id
        if active_bill_id is None:
            active_bill_id = ConversationMemory.get_last_bill(session_id)

        if active_bill_id is not None:
            bill = db.query(Bill).filter(Bill.id == active_bill_id).first()
            if bill:
                # Apply Security (Employee can only access their own bills)
                if user_role == "EMPLOYEE" and bill.created_by != username:
                    context["bill_info"] = "Access Denied: You do not have permissions to view this invoice context."
                else:
                    ConversationMemory.set_last_bill(session_id, active_bill_id)
                    context["bill_info"] = (
                        f"Active Bill Context:\n"
                        f"- ID: {bill.id}\n"
                        f"- Number: {bill.bill_number}\n"
                        f"- Company: {bill.company_name}\n"
                        f"- Slip Number: {bill.duty_slip_no}\n"
                        f"- Vehicle: {bill.vehicle_name}\n"
                        f"- Total Billed: ₹{bill.grand_total}\n"
                        f"- Warnings/Issues: {bill.notes or 'None'}\n"
                    )

        # 2. Gather Knowledge Store facts (Templates, preferred coordinates)
        if user_role in ("OWNER", "MANAGER"):
            templates = KnowledgeRetriever.get_company_templates(db)
            if templates:
                context["knowledge_facts"].append("Learned Company Layout Templates:")
                for t in templates[:3]:
                    context["knowledge_facts"].append(
                        f"  * Company '{t['company_name']}' uses layout '{t['layout_name']}' (conf={t['average_confidence']:.2f})"
                    )
            
            # Fetch vehicle column structures
            vehicles = KnowledgeRetriever.get_vehicle_structures(db)
            if vehicles:
                context["knowledge_facts"].append("Learned Vehicle Structures:")
                for v in vehicles[:3]:
                    context["knowledge_facts"].append(
                        f"  * Vehicle Type '{v['vehicle_type']}': layouts={v['recurring_structures']}"
                    )
        
        # 3. Gather Correction History (filtered by security role)
        corr_query = db.query(CorrectionHistory)
        if user_role == "EMPLOYEE":
            corr_query = corr_query.filter(CorrectionHistory.reviewer == username)
        
        corrections = corr_query.order_by(CorrectionHistory.timestamp.desc()).limit(5).all()
        if corrections:
            context["knowledge_facts"].append("Recent Manual Reviewer Corrections:")
            for c in corrections:
                context["knowledge_facts"].append(
                    f"  * Field '{c.field_type}' in bill {c.bill_number}: AI extracted '{c.original_value}', corrected to '{c.corrected_value}' by {c.reviewer}"
                )

        # 4. Gather Analytics (RBAC checks)
        if user_role == "OWNER":
            # Owner receives all analytics
            top_cust = AnalyticsAssistant.get_top_customers(db, limit=3)
            context["analytics_facts"].append(f"Top Billed Customers: {top_cust}")
            
            most_corr = AnalyticsAssistant.get_most_corrected_fields(db, limit=3)
            context["analytics_facts"].append(f"Most Corrected Fields: {most_corr}")
            
            rev_stats = AnalyticsAssistant.get_reviewer_stats(db)
            context["analytics_facts"].append(f"Reviewer Action Summary: {rev_stats}")
            
        elif user_role == "MANAGER":
            # Manager receives operational insights but not reviewer productivity
            top_cust = AnalyticsAssistant.get_top_customers(db, limit=3)
            context["analytics_facts"].append(f"Top Billed Customers: {top_cust}")
            
            most_corr = AnalyticsAssistant.get_most_corrected_fields(db, limit=3)
            context["analytics_facts"].append(f"Most Corrected Fields: {most_corr}")
            
        else:
            # Employee only sees statistics about their own imports
            my_bills_cnt = db.query(func.count(Bill.id)).filter(Bill.created_by == username).scalar() or 0
            context["analytics_facts"].append(f"Your Billed Trips Count: {my_bills_cnt}")

        return context
