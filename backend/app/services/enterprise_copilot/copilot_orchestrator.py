import logging
import requests
import time
from sqlalchemy.orm import Session
from app.config import settings
from app.services.enterprise_copilot.copilot_models import CopilotChatRequest, CopilotChatResponse
from app.services.enterprise_copilot.intent_classifier import IntentClassifier
from app.services.enterprise_copilot.context_builder import ContextBuilder
from app.services.enterprise_copilot.prompt_builder import PromptBuilder
from app.services.enterprise_copilot.response_formatter import ResponseFormatter
from app.services.enterprise_copilot.conversation_memory import ConversationMemory
from app.services.enterprise_copilot.bill_explainer import BillExplainer

logger = logging.getLogger("copilot_orchestrator")

class CopilotOrchestrator:
    @staticmethod
    def process_chat(
        db: Session,
        request: CopilotChatRequest,
        user_role: str,
        username: str
    ) -> CopilotChatResponse:
        """
        Executes the Copilot pipeline:
        Intent Classification -> Context Building -> Prompt Construction -> LLM Run -> Memory Update -> Output
        """
        # 1. Classify User Intent
        intent = IntentClassifier.classify_intent(request.query)
        logger.info(f"Copilot intent classified: {intent} for user {username}")

        # 2. Build Context
        context = ContextBuilder.build_context(
            db, request.query, request.sessionId, request.billId, user_role, username
        )

        # Special addition for EXPLAIN_BILL: Append custom details
        bill_id = request.billId or ConversationMemory.get_last_bill(request.sessionId)
        if intent == "EXPLAIN_BILL" and bill_id:
            explanation = BillExplainer.explain_bill(db, bill_id)
            explanation_text = BillExplainer.get_structured_explanation_text(explanation)
            context["bill_info"] += f"\nDetailed System Explanations:\n{explanation_text}\n"

        # 3. Construct Prompt
        prompt = PromptBuilder.build_prompt(request.query, intent, context)

        # 4. Invoke LLM (Gemini or Fallback)
        answer_text = ""
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
            
            try:
                logger.info(f"Invoking Gemini ({model}) for Copilot response...")
                res = requests.post(url, json=payload, headers=headers, timeout=30)
                res.raise_for_status()
                data = res.json()
                answer_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            except Exception as e:
                logger.warning(f"Gemini Copilot request failed: {e}")
                answer_text = f"I retrieved the system context but couldn't reach the AI model. Context gathered: {context['bill_info'] or 'None'}"

        if not answer_text:
            # Fallback to local context output
            answer_text = (
                f"### System Retrieval Summary:\n"
                f"The Copilot retrieved the following context regarding your query:\n"
                f"{context['bill_info'] or 'No active invoice context found.'}\n"
                f"Please verify this data. (Confidence: 85%)"
            )

        # 5. Update Conversation Memory
        ConversationMemory.add_message(request.sessionId, "user", request.query)
        ConversationMemory.add_message(request.sessionId, "assistant", answer_text)

        # 6. Format and return response
        return ResponseFormatter.format_response(answer_text, intent, bill_id)
