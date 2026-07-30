"""
AMIP Execution Narrator.
Generates natural language human-readable explanations summarizing workflow execution steps and decision rationale.
"""
from __future__ import annotations
from typing import Optional, Any, List
from app.services.amip.interfaces.explainability_interfaces import IExecutionNarrator
from app.services.amip.explainability.explainability_utils import format_confidence
from app.services.amip.exceptions import NarrativeGenerationError


class ExecutionNarrator(IExecutionNarrator):
    """
    Generates human-readable narrative summaries for executive audit trails and user interfaces.
    """

    def generate_narrative(
        self,
        context: Any,
        plan: Optional[Any] = None,
        decision: Optional[Any] = None,
    ) -> str:
        """
        Synthesizes context timeline, plan summary, and decision result into a structured text narrative.
        """
        if not context:
            raise NarrativeGenerationError("null_context", "ExecutionContext cannot be null.")

        try:
            sentences: List[str] = []

            # 1. Plan / Task Type Header
            task_type_str = getattr(context, "task_type", "GENERAL_QUERY")
            if hasattr(task_type_str, "value"):
                task_type_str = task_type_str.value

            req_summary = getattr(plan, "request_summary", f"Processing {task_type_str}") if plan else f"Processing {task_type_str}"
            sentences.append(f"Workflow initiated for: {req_summary}.")

            # 2. Agent Executions Narrative
            timeline = getattr(context, "timeline", None)
            records = getattr(timeline, "records", []) if timeline and hasattr(timeline, "records") else []

            agent_bullets: List[str] = []
            for rec in records:
                name = getattr(rec, "agent_name", "Agent")
                status = getattr(rec, "status", "SUCCESS")
                status_str = status.value if hasattr(status, "value") else str(status)
                out = getattr(rec, "output_summary", "")

                if name == "DocIntelAgent":
                    agent_bullets.append(f"Document Intelligence completed OCR parsing ({out or 'OK'}).")
                elif name == "ValidationAgent":
                    agent_bullets.append(f"Validation Engine checked mathematical formulas and duplicate rules ({out or 'OK'}).")
                elif name == "LearningAgent":
                    agent_bullets.append(f"Learning Engine matched company layout pattern ({out or 'OK'}).")
                elif name == "GraphAgent":
                    agent_bullets.append(f"Knowledge Graph linked entity nodes ({out or 'OK'}).")
                elif name == "PredictiveAgent":
                    agent_bullets.append(f"Predictive Engine evaluated financial risk and revenue forecast ({out or 'OK'}).")
                elif name == "CopilotAgent":
                    agent_bullets.append(f"Copilot Assistant formulated response ({out or 'OK'}).")
                else:
                    agent_bullets.append(f"{name} completed step with status {status_str}.")

            if agent_bullets:
                sentences.extend(agent_bullets)

            # 3. Decision Consensus & Confidence
            if decision:
                conf = getattr(decision, "confidence", 1.0)
                status = getattr(decision, "status", "COMPLETED")
                status_str = status.value if hasattr(status, "value") else str(status)
                reason = getattr(decision, "reason", "")

                conf_pct = format_confidence(conf)
                sentences.append(f"Decision Engine reached {conf_pct} confidence consensus.")
                if reason:
                    sentences.append(f"Reasoning: {reason}")
                sentences.append(f"Final Outcome: Workflow completed with status {status_str}.")
            else:
                sentences.append("Workflow completed successfully.")

            return "\n".join(sentences)

        except Exception as err:
            wf_id = getattr(context, "workflow_id", "unknown") if context else "unknown"
            raise NarrativeGenerationError(wf_id, str(err))
