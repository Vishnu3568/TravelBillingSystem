import os
import sys
import logging
import requests
from sqlalchemy import text

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("verify_system")

def verify_system():
    logger.info("==================================================")
    logger.info("     ENTERPRISE LIVE RUNTIME VERIFICATION        ")
    logger.info("==================================================")

    errors = []

    # 1. Database connection check
    logger.info("⚡ Step 1/7: Verifying Database Connection...")
    try:
        from app.database import SessionLocal
        db = SessionLocal()
        res = db.execute(text("SELECT 1")).scalar()
        if res == 1:
            logger.info("✔ Database Connection verified successfully.")
        else:
            raise ValueError(f"Unexpected query result: {res}")
    except Exception as e:
        logger.error(f"❌ Database Connection failed: {e}")
        errors.append(f"Database: {e}")
        db = None

    # Stop early if database is unavailable
    if not db:
        logger.error("❌ CRITICAL: Database check failed. Aborting further verification.")
        sys.exit(1)

    # 2. Gemini API check
    logger.info("⚡ Step 2/7: Verifying Gemini Content Generation...")
    try:
        from app.services.gemini import gemini_service
        res = gemini_service.parse_bill_text("Sri Tulja Bhavani Travels bill DS-100 total amount 1500")
        if res and isinstance(res, list):
            logger.info(f"✔ Gemini Content Generation verified successfully. Result parsed elements count: {len(res)}")
        else:
            raise ValueError(f"Unexpected parser response format: {res}")
    except Exception as e:
        logger.error(f"❌ Gemini Content Generation failed: {e}")
        errors.append(f"Gemini: {e}")

    # 3. Vector Store check
    logger.info("⚡ Step 3/7: Verifying Vector Store Indexing...")
    try:
        from app.config import settings
        headers = {"x-api-key": settings.INTERNAL_API_KEY or "travel_billing_secret_token_123"}
        payload = {
            "billId": 99999,
            "text": "Verification test bill data total amount ₹1500 for company Portescap and vehicle TS09EX1111",
            "metadata": {
                "company": "Portescap",
                "vehicle": "TS09EX1111",
                "billNumber": "VERIFY-999"
            }
        }
        res = requests.post("http://localhost:9001/api/ai/index-bill", json=payload, headers=headers, timeout=5)
        res.raise_for_status()
        logger.info("✔ Vector Store Indexing verified successfully.")
    except Exception as e:
        logger.error(f"❌ Vector Store Indexing failed: {e}")
        errors.append(f"Vector Store: {e}")

    # 4. Knowledge Graph check
    logger.info("⚡ Step 4/7: Verifying Knowledge Graph Traversal...")
    try:
        from app.services.knowledge_graph import GraphService
        analytics = GraphService.get_analytics(db)
        if analytics is not None:
            logger.info(f"✔ Knowledge Graph verified. Node count: {analytics.get('total_nodes', 0)}, Edge count: {analytics.get('total_edges', 0)}")
        else:
            raise ValueError("Graph analytics returned None")
    except Exception as e:
        logger.error(f"❌ Knowledge Graph failed: {e}")
        errors.append(f"Knowledge Graph: {e}")

    # 5. Learning Engine check
    logger.info("⚡ Step 5/7: Verifying Learning Engine Updates...")
    try:
        from app.services.learning_engine.learning_models import CorrectionRecord
        from app.services.learning_engine.correction_store import CorrectionStore
        
        record = CorrectionRecord(
            original_value="100.00",
            corrected_value="200.00",
            field_type="driver_bata",
            company_name="Portescap",
            vehicle_number="TS09EX1111",
            bill_number="VERIFY-999",
            reviewer="verifier"
        )
        correction = CorrectionStore.save_correction(db, record)
        if correction:
            logger.info("✔ Learning Engine correction save verified successfully.")
        else:
            raise ValueError("CorrectionStore returned None")
    except Exception as e:
        logger.error(f"❌ Learning Engine failed: {e}")
        errors.append(f"Learning Engine: {e}")

    # 6. Predictive Engine check
    logger.info("⚡ Step 6/7: Verifying Predictive Engine Forecasting...")
    try:
        from app.services.predictive_engine.predictive_service import PredictiveService
        summary = PredictiveService.get_predictive_summary(db)
        if summary and summary.revenue_forecast:
            logger.info(f"✔ Predictive summary verified. Forecast: ₹{summary.revenue_forecast.monthly}")
        else:
            raise ValueError("Predictive summary or forecast was None")
    except Exception as e:
        logger.error(f"❌ Predictive Engine failed: {e}")
        errors.append(f"Predictive Engine: {e}")

    # 7. Copilot check
    logger.info("⚡ Step 7/7: Verifying AI Copilot Reasoning Context...")
    try:
        from app.services.enterprise_copilot import CopilotService, CopilotChatRequest
        req = CopilotChatRequest(
            query="Explain the status of company Portescap",
            sessionId="verify_session",
            billId=None
        )
        reply = CopilotService.ask_copilot(db, req, user_role="OWNER", username="verifier")
        if reply and reply.answer:
            logger.info(f"✔ AI Copilot reasoning verified. Answer snippet: \"{reply.answer[:60]}...\"")
        else:
            raise ValueError("Copilot returned empty answer")
    except Exception as e:
        logger.error(f"❌ AI Copilot reasoning failed: {e}")
        errors.append(f"AI Copilot: {e}")

    # Conclusion
    logger.info("==================================================")
    if not errors:
        logger.info("🚀 SYSTEM FULLY CERTIFIED & READY FOR PRODUCTION!  ")
        logger.info("==================================================")
        return True
    else:
        logger.error(f"❌ SYSTEM VERIFICATION FAILED WITH {len(errors)} ERROR(S):")
        for err in errors:
            logger.error(f"  - {err}")
        logger.info("==================================================")
        return False

if __name__ == "__main__":
    success = verify_system()
    sys.exit(0 if success else 1)
