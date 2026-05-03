from typing import Any, TypedDict

from sqlalchemy.orm import Session


class SupportState(TypedDict, total=False):
    message: str
    conversation_id: str
    db_session: Session
    language: str
    intent: str
    order_id: str | None
    new_address: str | None
    policy_context: dict[str, str] | None
    tool_used: str
    response: str
    resolved: bool
    requires_human: bool
    confidence_score: float
    action_result: Any
