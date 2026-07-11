from typing import Dict, Any

class PromptBuilder:
    @staticmethod
    def build_prompt(query: str, intent: str, context: Dict[str, Any]) -> str:
        """
        Builds the detailed system and user prompt block containing gathered context,
        memory logs, and safety instructions for Gemini.
        """
        system_instruction = (
            "You are an Enterprise AI Copilot for the Travel Billing System ERP.\n"
            "Your sole objective is to answer reviewer questions, explain bills, validation failures, "
            "recommend corrections, and provide analytics using the provided real-time database facts.\n\n"
            "STRICT RULES:\n"
            "1. NEVER answer from your training memory alone. If no context facts are supplied, state that "
            "you do not have access to that system data.\n"
            "2. Always structure your answers with reasoning, confidence estimation, and referenced bills or patterns.\n"
            "3. Respect user roles. If the user is an EMPLOYEE, they can only view data relating to bills "
            "created by themselves. Do not disclose other company templates, layouts, or statistics.\n"
            "4. Output your response as a clean formatted Markdown response."
        )

        user_prompt = []
        user_prompt.append(f"User Query: {query}")
        user_prompt.append(f"Detected Intent: {intent}")
        user_prompt.append(f"User Identity: {context['username']} (Role: {context['role']})")
        
        # Add conversation history
        if context["conversation_history"]:
            user_prompt.append("\nConversation History Memory:")
            user_prompt.append(context["conversation_history"])
            
        # Add active bill details
        if context["bill_info"]:
            user_prompt.append("\n" + context["bill_info"])
            
        # Add knowledge facts
        if context["knowledge_facts"]:
            user_prompt.append("\nKnowledge Store Facts:")
            user_prompt.extend(context["knowledge_facts"])

        # Add analytics facts
        if context["analytics_facts"]:
            user_prompt.append("\nReal-time Analytics Facts:")
            user_prompt.extend(context["analytics_facts"])

        user_prompt.append("\nGenerate your markdown response following the strict safety and retrieval rules.")

        return f"{system_instruction}\n\n" + "\n".join(user_prompt)
