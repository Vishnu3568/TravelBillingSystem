"""
AMIP Gateway Package.
Exports AMIPWorkflowGateway and singleton provider.
"""
from app.services.amip.gateway.workflow_gateway import (
    AMIPWorkflowGateway,
    get_workflow_gateway,
)

__all__ = [
    "AMIPWorkflowGateway",
    "get_workflow_gateway",
]
