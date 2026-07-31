"""
Comprehensive Unit Test Suite for AMIP Explainability Engine (Phase 9 Checkpoint 5).
Tests AgentExplanation, EvidenceChain, DecisionExplanation, ExplainabilityReport,
TimelineRenderer, ExecutionNarrator, ExplainabilityEngine, Utilities, and Exceptions.
Targeting 95%+ Code Coverage.
"""
from __future__ import annotations
import pytest

from app.services.amip.models.enums import (
    ExecutionStatus,
    DecisionStatus,
    DecisionPolicy,
    TaskType,
    AgentStatus,
)
from app.services.amip.models.execution_context import ExecutionContext
from app.services.amip.models.agent_record import AgentExecutionRecord
from app.services.amip.models.agent_explanation import AgentExplanation
from app.services.amip.models.evidence_chain import EvidenceChain
from app.services.amip.models.explainability_report import ExplainabilityReport, generate_report_id
from app.services.amip.models.execution_task import ExecutionTask
from app.services.amip.explainability.decision_explanation import DecisionExplanation
from app.services.amip.explainability.timeline_renderer import TimelineRenderer
from app.services.amip.explainability.execution_narrator import ExecutionNarrator
from app.services.amip.explainability.explainability_engine import ExplainabilityEngine
from app.services.amip.explainability.explainability_utils import (
    format_confidence,
    format_timeline,
    summarize_execution,
    format_evidence_summary,
)
from app.services.amip.models.decision_result import DecisionResult
from app.services.amip.models.decision_evidence import DecisionEvidence
from app.services.amip.supervisor.amip_supervisor import AMIPSupervisor
from app.services.amip.supervisor.execution_engine import ExecutionEngine
from app.services.amip.supervisor.mock_executors import (
    DocIntelMockExecutor,
    ValidationMockExecutor,
    LearningMockExecutor,
)
from app.services.amip.exceptions import (
    ExplainabilityError,
    NarrativeGenerationError,
    TimelineGenerationError,
)


# ============================================================================
# 1. EXPLAINABILITY UTILITIES TESTS
# ============================================================================
def test_explainability_utilities():
    """Verify confidence formatting, timeline text formatting, and evidence formatting."""
    assert format_confidence(0.96) == "96.00%"
    assert format_confidence(1.0) == "100.00%"
    assert format_confidence(0.0) == "0.00%"

    rec1 = AgentExecutionRecord(agent_name="DocIntelAgent", duration_ms=100.0, output_summary="Parsed 1 page")
    rec2 = AgentExecutionRecord(agent_name="ValidationAgent", duration_ms=150.0, output_summary="Score 95")
    formatted_tl = format_timeline([rec1, rec2])

    assert "DocIntelAgent" in formatted_tl
    assert "100.0ms" in formatted_tl

    ctx = ExecutionContext(workflow_id="wfk-test", current_stage="PARSED")
    summary_str = summarize_execution(ctx)
    assert "wfk-test" in summary_str
    assert "PARSED" in summary_str

    ev_chain = EvidenceChain(supporting_evidence=["DocIntelAgent"], conflicting_evidence=["AnomalyAgent"])
    ev_str = format_evidence_summary(ev_chain)
    assert "DocIntelAgent" in ev_str
    assert "AnomalyAgent" in ev_str


# ============================================================================
# 2. AGENT & DECISION EXPLANATION MODELS TESTS
# ============================================================================
def test_agent_and_decision_explanation_models():
    """Verify serialization and deserialization of AgentExplanation and DecisionExplanation."""
    agent_exp = AgentExplanation(
        agent_name="LabelerAgent",
        purpose="Field Label Mapping",
        confidence=0.94,
        status=AgentStatus.SUCCESS,
        input_summary="Extracted OCR text",
        output_summary="Mapped 12 fields",
    )
    d_agent = agent_exp.to_dict()
    assert d_agent["agent_name"] == "LabelerAgent"
    assert d_agent["confidence"] == 0.94

    restored_agent = AgentExplanation.from_dict(d_agent)
    assert restored_agent.agent_name == "LabelerAgent"
    assert restored_agent.status == AgentStatus.SUCCESS

    dec_exp = DecisionExplanation(
        why_decision_was_taken="High consensus",
        alternative_decisions=["MANUAL_REVIEW"],
        decision_policy_used=DecisionPolicy.AUTO_APPROVE,
    )
    d_dec = dec_exp.to_dict()
    assert d_dec["decision_policy_used"] == "AUTO_APPROVE"

    restored_dec = DecisionExplanation.from_dict(d_dec)
    assert restored_dec.decision_policy_used == DecisionPolicy.AUTO_APPROVE


# ============================================================================
# 3. TIMELINE RENDERER TESTS
# ============================================================================
def test_timeline_renderer():
    """Verify TimelineRenderer rendering, duration computation, and critical path generation."""
    renderer = TimelineRenderer()
    ctx = ExecutionContext()
    ctx.timeline.append(AgentExecutionRecord(agent_name="DocIntelAgent", start_time="2026-07-28T00:00:00Z", end_time="2026-07-28T00:00:01Z", duration_ms=1000.0))
    ctx.timeline.append(AgentExecutionRecord(agent_name="ValidationAgent", start_time="2026-07-28T00:00:01Z", end_time="2026-07-28T00:00:02Z", duration_ms=1000.0))

    rendered = renderer.render_timeline(ctx.timeline)

    assert len(rendered["events"]) == 2
    assert "DocIntelAgent" in rendered["critical_path"]
    assert "ValidationAgent" in rendered["critical_path"]
    assert rendered["total_duration_ms"] == 2000.0
    assert "DocIntelAgent" in rendered["formatted_str"]


# ============================================================================
# 4. EXECUTION NARRATOR TESTS
# ============================================================================
def test_execution_narrator():
    """Verify natural language human-readable narrative generation."""
    narrator = ExecutionNarrator()
    ctx = ExecutionContext(task_type=TaskType.DOCUMENT_IMPORT)
    ctx.timeline.append(AgentExecutionRecord(agent_name="DocIntelAgent", output_summary="1 page parsed"))
    ctx.timeline.append(AgentExecutionRecord(agent_name="ValidationAgent", output_summary="Formulas valid"))

    dec = DecisionResult(
        confidence=0.96,
        status=DecisionStatus.COMPLETED,
        reason="Consensus reached",
    )

    narrative = narrator.generate_narrative(ctx, None, dec)

    assert "Document Intelligence completed OCR parsing" in narrative
    assert "Validation Engine checked mathematical formulas" in narrative
    assert "96.00% confidence consensus" in narrative


# ============================================================================
# 5. EXPLAINABILITY ENGINE END-TO-END TESTS
# ============================================================================
def test_explainability_engine_report_generation():
    """Verify end-to-end ExplainabilityReport generation from AMIPSupervisor orchestration."""
    # 1. Setup Supervisor & Orchestrate Workflow
    engine = ExecutionEngine([
        DocIntelMockExecutor(),
        ValidationMockExecutor(),
        LearningMockExecutor(),
    ])
    supervisor = AMIPSupervisor(engine=engine)

    t1 = ExecutionTask(task_id="t1", task_name="Parse OCR", task_type=TaskType.DOCUMENT_IMPORT, required_agents=["DocIntelAgent"])
    t2 = ExecutionTask(task_id="t2", task_name="Validate Formulas", task_type=TaskType.DOCUMENT_IMPORT, dependencies=["t1"], required_agents=["ValidationAgent"])
    plan = supervisor.planner.create_plan(tasks=[t1, t2])

    decision, ctx = supervisor.orchestrate(plan=plan, task_type=TaskType.DOCUMENT_IMPORT)

    # 2. Generate Report via ExplainabilityEngine
    exp_engine = ExplainabilityEngine()
    report = exp_engine.generate_report(
        context=ctx,
        plan=plan,
        state=supervisor.get_state(),
        decision=decision,
    )

    # 3. Assert Report Fields & Serialization
    assert report.report_id.startswith("rep-")
    assert report.workflow_id == ctx.workflow_id
    assert report.overall_status == ExecutionStatus.COMPLETED
    assert report.overall_confidence > 0.85
    assert len(report.agent_explanations) == 2
    assert report.evidence_chain is not None
    assert report.decision_explanation.decision_policy_used == DecisionPolicy.AUTO_APPROVE
    assert ("Document Intelligence" in report.narrative_summary or "BulkImportAgent" in report.narrative_summary or "completed step" in report.narrative_summary)

    # Serialization roundtrip test
    d = report.to_dict()
    assert d["report_id"] == report.report_id
    assert d["overall_confidence"] == report.overall_confidence

    restored = ExplainabilityReport.from_dict(d)
    assert restored.report_id == report.report_id
    assert restored.workflow_id == report.workflow_id
    assert len(restored.agent_explanations) == 2


def test_explainability_exceptions():
    """Verify explainability error handling and exception messages."""
    exc1 = ExplainabilityError("wf-101", "Null timeline object")
    assert "wf-101" in str(exc1)

    exc2 = NarrativeGenerationError("wf-202", "Missing task type")
    assert "wf-202" in str(exc2)

    exc3 = TimelineGenerationError("wf-303", "Invalid record format")
    assert "wf-303" in str(exc3)
