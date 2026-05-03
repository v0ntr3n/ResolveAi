from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.data.db import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    customer_email: Mapped[str] = mapped_column(String(255))
    customer_name: Mapped[str] = mapped_column(String(255))
    language_preference: Mapped[str] = mapped_column(String(8), default="en")
    status: Mapped[str] = mapped_column(String(32))
    tracking_number: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    payment_status: Mapped[str] = mapped_column(String(32))
    refund_status: Mapped[str] = mapped_column(String(32), default="not_requested")
    refund_eligible: Mapped[bool] = mapped_column(Boolean, default=False)
    refund_reason: Mapped[str] = mapped_column(String(64), default="")
    shipping_address: Mapped[str] = mapped_column(Text)
    special_handling: Mapped[str] = mapped_column(String(32), default="standard")
    address_change_allowed: Mapped[bool] = mapped_column(Boolean, default=True)
    risk_flag: Mapped[str] = mapped_column(String(16), default="low")
    evidence_required: Mapped[str] = mapped_column(String(64), default="none")


class Escalation(Base):
    __tablename__ = "escalations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    intent: Mapped[str] = mapped_column(String(64))
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    conversation_summary: Mapped[str] = mapped_column(Text)
    evidence_needed: Mapped[str] = mapped_column(String(64), default="none")
    sla_hours: Mapped[int] = mapped_column(Integer, default=24)
    review_notes: Mapped[str] = mapped_column(Text, default="")


class ConversationLog(Base):
    __tablename__ = "conversation_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[str] = mapped_column(String(64), index=True)
    user_message: Mapped[str] = mapped_column(Text)
    detected_language: Mapped[str] = mapped_column(String(8))
    intent: Mapped[str] = mapped_column(String(64))
    resolved: Mapped[bool] = mapped_column(Boolean)
    tool_used: Mapped[str] = mapped_column(String(64))
    confidence_score: Mapped[float] = mapped_column(Float)
    human_intervention_required: Mapped[bool] = mapped_column(Boolean, default=False)
    latency_ms: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
