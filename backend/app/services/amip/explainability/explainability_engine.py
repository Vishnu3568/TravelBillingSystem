"""
AMIP Explainability Engine.
Central reporting component synthesizing timeline rendering, evidence aggregation, decision justification,
agent explanations, and human narrative generation into an ExplainabilityReport DTO.
"""
from __future__ import annotations
from typing import Optional, Any, List, Dict
from app.services.amip.interfaces.explainability_interfaces import (
    IExplainabilityEngine,
    ITimelineRenderer,
    IExecutionNarrator,
)
from app.services.amip.models.explainability_report import ExplainabilityReport, generate_report_id
from app.services.amip.models.agent_explanation import AgentExplanation
from app.services.amip.models.evidence_chain import EvidenceChain
from app.services.amip.explainability.decision_explanation import DecisionExplanation
from app.services.amip.explainability.timeline_renderer import TimelineRenderer
from app.services.amip.explainability.execution_narrator import ExecutionNarrator
from app.services.amip.models.enums import ExecutionStatus, DecisionPolicy
from app.services.amip.exceptions import ExplainabilityError


class ExplainabilityEngine(IExplainabilityEngine):
    """
    Enterprise explainability engine synthesizing multi-agent execution telemetry into audit reports.
    """

    def __init__(
        self,
        timeline_renderer: Optional[ITimelineRenderer] = None,
        narrator: Optional[IExecutionNarrator] = None,
    ):
        self.renderer = timeline_renderer or TimelineRenderer()
        self.narrator = narrator or ExecutionNarrator()

    def generate_report(
        self,
        context: Any,
        plan: Optional[Any] = None,
        state: Optional[Any] = None,
        decision: Optional[Any] = None,
    ) -> ExplainabilityReport:
        """
        Generates a complete, structured ExplainabilityReport for an execution workflow.
        """
        if not context:
            raise ExplainabilityError("null_context", "ExecutionContext cannot be null.")

        try:
            workflow_id = getattr(context, "workflow_id", "")
            trace_id = getattr(context, "trace_id", "")
            overall_status = getattr(context, "overall_status", ExecutionStatus.COMPLETED)

            # 1. Render Timeline
            timeline = getattr(context, "timeline", None)
            timeline_summary = self.renderer.render_timeline(timeline)
            total_duration_ms = timeline_summary.get("total_duration_ms", 0.0)

            # 2. Extract Agent Explanations from Timeline Records
            records = getattr(timeline, "records", []) if timeline and hasattr(timeline, "records") else []
            agent_explanations: List[AgentExplanation] = []

            for rec in records:
                agent_name = getattr(rec, "agent_name", "UnknownAgent")
                status = getattr(rec, "status", ExecutionStatus.COMPLETED)
                conf = getattr(rec, "confidence", 1.0)
                in_sum = getattr(rec, "input_summary", "")
                out_sum = getattr(rec, "output_summary", "")
                start_ts = getattr(rec, "start_time", "")
                warns = getattr(rec, "warnings", [])
                errs = getattr(rec, "errors", [])

                exp = AgentExplanation(
                    agent_name=agent_name,
                    purpose=f"Execution step for {agent_name}",
                    execution_time=start_ts,
                    confidence=float(conf),
                    status=status,
                    input_summary=in_sum,
                    output_summary=out_sum,
                    warnings=list(warns),
                    errors=list(errs),
                )
                agent_explanations.append(exp)

            # 3. Build Evidence Chain
            evidence_chain = EvidenceChain()
            if decision and hasattr(decision, "evidence") and decision.evidence:
                ev_dto = decision.evidence
                evidence_chain.supporting_evidence = getattr(ev_dto, "supporting_agents", [])
                evidence_chain.conflicting_evidence = getattr(ev_dto, "conflicting_agents", [])
                evidence_chain.validation_notes = [f"Validation summary: {getattr(ev_dto, 'validation_summary', {})}"]
                evidence_chain.graph_references = getattr(ev_dto, "graph_summary", {})
                evidence_chain.learning_references = getattr(ev_dto, "learning_summary", {})
                evidence_chain.predictive_references = getattr(ev_dto, "predictive_summary", {})

            # 4. Build Decision Explanation
            decision_explanation = DecisionExplanation()
            if decision:
                policy_used = getattr(decision, "policy", DecisionPolicy.AUTO_APPROVE)
                reason_str = getattr(decision, "reason", "Consensus reached")
                rec_str = getattr(decision, "recommended_action", "AUTO_APPROVE")

                decision_explanation.why_decision_was_taken = reason_str
                decision_explanation.confidence_reasoning = f"Confidence score reached {getattr(decision, 'confidence', 1.0):.4f}"
                decision_explanation.decision_policy_used = policy_used
                decision_explanation.alternative_decisions = ["MANUAL_REVIEW", "AUTO_REJECT"]
                decision_explanation.rejected_alternatives = ["AUTO_REJECT"]

            # 5. Generate Narrative
            narrative = self.narrator.generate_narrative(context, plan, decision)

            # 6. Formulate ExplainabilityReport
            report = ExplainabilityReport(
                report_id=generate_report_id(),
                trace_id=trace_id,
                workflow_id=workflow_id,
                overall_status=overall_status,
                overall_confidence=float(getattr(decision, "confidence", 1.0) if decision else 1.0),
                execution_duration_ms=float(total_duration_ms),
                decision_summary=getattr(decision, "reason", "Workflow completed.") if decision else "Completed.",
                recommendation=getattr(decision, "recommended_action", "AUTO_APPROVE") if decision else "AUTO_APPROVE",
                agent_explanations=agent_explanations,
                evidence_chain=evidence_chain,
                decision_explanation=decision_explanation,
                timeline_summary=timeline_summary,
                narrative_summary=narrative,
            )

            return report

        except Exception as err:
            wf_id = getattr(context, "workflow_id", "unknown") if context else "unknown"
            raise ExplainabilityError(wf_id, str(err))
