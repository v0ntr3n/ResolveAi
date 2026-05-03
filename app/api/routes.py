from uuid import uuid4

from fastapi import APIRouter, Depends
from langsmith.run_helpers import traceable
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agent.graph import build_support_graph
from app.agent.nodes import get_node_performance_stats
from app.core.tracing import get_trace_url
from app.data.db import get_session_factory
from app.data.models import Escalation
from app.services.analytics import aggregate_metrics

router = APIRouter()
session_factory = get_session_factory()
support_graph = build_support_graph()


def get_db() -> Session:
    with session_factory() as session:
        yield session


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/chat")
@traceable(name="chat_endpoint", run_type="chain")
def chat(payload: ChatRequest, session: Session = Depends(get_db)) -> dict:
    """Chat endpoint with LangSmith tracing support."""
    conversation_id = payload.conversation_id or str(uuid4())
    result = support_graph.invoke(
        {"message": payload.message, "conversation_id": conversation_id, "db_session": session}
    )
    
    # Build response
    response = {
        "conversation_id": conversation_id,
        "intent": result["intent"],
        "language": result["language"],
        "response": result["response"],
        "tool_used": result["tool_used"],
        "resolved": result["resolved"],
        "requires_human": result["requires_human"],
        "confidence_score": result["confidence_score"],
    }
    
    # Add trace URL if available
    from langsmith import get_current_run_tree
    run = get_current_run_tree()
    if run:
        trace_url = get_trace_url(run.id)
        if trace_url:
            response["trace_url"] = trace_url
    
    return response


@router.get("/performance")
def performance() -> dict:
    """Get node performance statistics."""
    return get_node_performance_stats()


@router.get("/metrics")
def metrics(session: Session = Depends(get_db)) -> dict:
    """Get business metrics for dashboard."""
    return aggregate_metrics(session)


@router.get("/prometheus")
def prometheus_metrics():
    """Prometheus metrics endpoint for monitoring."""
    from app.core.metrics import metrics_endpoint
    return metrics_endpoint()


@router.get("/escalations")
def escalations(session: Session = Depends(get_db)) -> list[dict]:
    rows = session.scalars(select(Escalation).order_by(Escalation.created_at.desc())).all()
    return [
        {
            "id": row.id,
            "order_id": row.order_id,
            "intent": row.intent,
            "reason": row.reason,
            "status": row.status,
            "evidence_needed": row.evidence_needed,
            "sla_hours": row.sla_hours,
            "conversation_summary": row.conversation_summary,
        }
        for row in rows
    ]
