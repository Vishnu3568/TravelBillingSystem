"""
AMIP Autonomous Workflow API Router.
Exposes endpoints to trigger autonomous multi-agent workflows, cancel executions, retrieve audit bundles,
and manage Human-in-the-Loop (HITL) review queues and operator overrides.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.utils.security import RoleChecker
from app.schemas.amip_workflow import (
    WorkflowExecutionRequest,
    WorkflowExecutionResponse,
    WorkflowCancelResponse,
    WorkflowAuditBundleResponse,
)
from app.schemas.amip_hitl import (
    HITLReviewItemResponse,
    HITLOverrideRequest,
    HITLOverrideResponse,
)
from app.services.amip.gateway import get_workflow_gateway, AMIPWorkflowGateway

router = APIRouter(prefix="/api/amip", tags=["AMIP Workflows"])

# Enforce OWNER or MANAGER role for all AMIP workflow operations
admin_guard = RoleChecker(["OWNER", "MANAGER"])


@router.post(
    "/workflows/execute",
    response_model=WorkflowExecutionResponse,
    summary="Trigger Autonomous AMIP Workflow",
)
def execute_workflow(
    request: WorkflowExecutionRequest,
    current_user: dict = Depends(admin_guard),
    gateway: AMIPWorkflowGateway = Depends(get_workflow_gateway),
):
    """
    Triggers an autonomous AMIP multi-agent workflow for the requested task,
    orchestrating context, planning, consensus decisioning, and explainability reporting.
    """
    user_id = current_user.get("sub") or current_user.get("username", "system")
    user_role = current_user.get("role", "MANAGER")

    return gateway.execute_workflow(
        request=request,
        user_id=user_id,
        user_role=user_role,
    )


@router.post(
    "/workflows/{workflow_id}/cancel",
    response_model=WorkflowCancelResponse,
    summary="Cancel Autonomous AMIP Workflow",
)
def cancel_workflow(
    workflow_id: str,
    current_user: dict = Depends(admin_guard),
    gateway: AMIPWorkflowGateway = Depends(get_workflow_gateway),
):
    """
    Dispatches a cooperative cancellation signal to an active workflow execution.
    """
    user_id = current_user.get("sub") or current_user.get("username", "system")
    return gateway.cancel_workflow(
        workflow_id=workflow_id,
        user_id=user_id,
    )


@router.get(
    "/workflows/{workflow_id}/audit",
    response_model=WorkflowAuditBundleResponse,
    summary="Get Complete Workflow Audit Bundle",
)
def get_workflow_audit(
    workflow_id: str,
    current_user: dict = Depends(admin_guard),
    gateway: AMIPWorkflowGateway = Depends(get_workflow_gateway),
):
    """
    Retrieves the complete audit bundle for a workflow including consensus decision,
    narrative explanation, execution timeline, structured logs, and telemetry spans.
    """
    audit_bundle = gateway.get_workflow_audit_bundle(workflow_id)
    if not audit_bundle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit bundle for workflow '{workflow_id}' not found",
        )
    return audit_bundle


@router.get(
    "/reviews/pending",
    response_model=List[HITLReviewItemResponse],
    summary="Get Pending Human-in-the-Loop Review Queue",
)
@router.get(
    "/workflows/reviews/pending",
    response_model=List[HITLReviewItemResponse],
    include_in_schema=False,
)
def get_pending_reviews(
    current_user: dict = Depends(admin_guard),
    gateway: AMIPWorkflowGateway = Depends(get_workflow_gateway),
):
    """
    Retrieves all workflows currently in REVIEW_REQUIRED status awaiting human operator intervention.
    """
    return gateway.get_pending_reviews()


@router.post(
    "/workflows/{workflow_id}/override",
    response_model=HITLOverrideResponse,
    summary="Submit Human Operator Decision Override",
)
def submit_workflow_override(
    workflow_id: str,
    override_req: HITLOverrideRequest,
    current_user: dict = Depends(admin_guard),
    gateway: AMIPWorkflowGateway = Depends(get_workflow_gateway),
):
    """
    Submits a human operator decision override (APPROVE, REJECT, ESCALATE)
    for a workflow in REVIEW_REQUIRED status.
    """
    operator = current_user.get("sub") or current_user.get("username", "system")
    return gateway.submit_human_override(
        workflow_id=workflow_id,
        action=override_req.action,
        reason=override_req.reason,
        notes=override_req.notes,
        operator=operator,
    )
