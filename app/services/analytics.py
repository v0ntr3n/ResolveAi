from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.data.models import ConversationLog
from app.services.cache import get_metrics_cache


def log_conversation(
    session: Session,
    conversation_id: str,
    user_message: str,
    detected_language: str,
    intent: str,
    resolved: bool,
    tool_used: str,
    confidence_score: float,
    human_intervention_required: bool,
    latency_ms: int,
) -> ConversationLog:
    log = ConversationLog(
        conversation_id=conversation_id,
        user_message=user_message,
        detected_language=detected_language,
        intent=intent,
        resolved=resolved,
        tool_used=tool_used,
        confidence_score=confidence_score,
        human_intervention_required=human_intervention_required,
        latency_ms=latency_ms,
    )
    session.add(log)
    session.commit()
    session.refresh(log)
    
    # Invalidate metrics cache when new conversation is logged
    cache = get_metrics_cache()
    cache.invalidate_metrics()
    
    return log


def aggregate_metrics(session: Session, use_cache: bool = True) -> dict[str, int]:
    """Aggregate metrics with caching for better performance."""
    cache = get_metrics_cache()
    
    # Try cache first
    if use_cache:
        cached_metrics = cache.get_metrics()
        if cached_metrics:
            return cached_metrics
    
    # Query database
    total_conversations = session.scalar(select(func.count()).select_from(ConversationLog)) or 0
    resolved_count = (
        session.scalar(
            select(func.count()).select_from(ConversationLog).where(ConversationLog.resolved.is_(True))
        )
        or 0
    )
    escalation_count = (
        session.scalar(
            select(func.count())
            .select_from(ConversationLog)
            .where(ConversationLog.human_intervention_required.is_(True))
        )
        or 0
    )
    
    metrics = {
        "total_conversations": total_conversations,
        "resolved_count": resolved_count,
        "escalation_count": escalation_count,
    }
    
    # Cache result
    if use_cache:
        cache.set_metrics(metrics)
    
    return metrics
