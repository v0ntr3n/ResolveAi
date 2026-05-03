from __future__ import annotations

import os
from typing import Any

import httpx
import streamlit as st


def backend_url() -> str:
    explicit_url = os.getenv("RESOLVEAI_BACKEND_URL")
    if explicit_url:
        return explicit_url

    hostport = os.getenv("RESOLVEAI_BACKEND_HOSTPORT")
    if hostport:
        return f"http://{hostport}"

    return "http://127.0.0.1:8000"


def detect_local_language(message: str) -> str:
    lowered = message.lower()
    return "vi" if any(token in lowered for token in ("đơn", "hoàn tiền", "địa chỉ", "chính sách")) else "en"


def fetch_json(method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
    with httpx.Client(base_url=backend_url(), timeout=15.0) as client:
        response = client.request(method, path, json=payload)
        response.raise_for_status()
        return response.json()


def render_metrics() -> None:
    metrics = fetch_json("GET", "/metrics")
    cols = st.columns(3)
    cols[0].metric("Total Conversations", metrics.get("total_conversations", 0))
    cols[1].metric("Resolved", metrics.get("resolved_count", 0))
    cols[2].metric("Escalations", metrics.get("escalation_count", 0))


def render_escalations() -> None:
    with st.expander("Recent Escalations", expanded=False):
        rows = fetch_json("GET", "/escalations")
        if not rows:
            st.write("No escalations yet.")
            return
        for row in rows[:5]:
            st.write(
                f"Order: {row['order_id']} | Intent: {row['intent']} | "
                f"Reason: {row['reason']} | Evidence: {row['evidence_needed']} | SLA: {row['sla_hours']}h"
            )


def main() -> None:
    st.set_page_config(page_title="ResolveAI", page_icon=":telephone_receiver:", layout="wide")
    st.title("ResolveAI")
    st.caption("Autonomous Tier-1 support demo for order status, refunds, and address changes.")

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "last_response" not in st.session_state:
        st.session_state.last_response = None

    with st.sidebar:
        st.subheader("Dashboard")
        render_metrics()
        render_escalations()
        if st.session_state.last_response:
            st.subheader("Last Decision")
            st.write(f"Language: {st.session_state.last_response['language']}")
            st.write(f"Intent: {st.session_state.last_response['intent']}")
            st.write(f"Tool: {st.session_state.last_response['tool_used']}")
            st.write(f"Confidence: {st.session_state.last_response['confidence_score']}")
            st.write(f"Needs human: {st.session_state.last_response['requires_human']}")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Ask about an order, refund, address change, or policy.")
    if not prompt:
        return

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    response = fetch_json("POST", "/chat", {"message": prompt})
    st.session_state.last_response = response
    st.session_state.messages.append({"role": "assistant", "content": response["response"]})

    with st.chat_message("assistant"):
        st.markdown(response["response"])


if __name__ == "__main__":
    main()
