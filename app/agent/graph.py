from langgraph.graph import END, START, StateGraph

from app.agent.nodes import (
    classify_node,
    execute_address_change_node,
    execute_order_status_node,
    execute_policy_node,
    execute_refund_node,
    log_node,
    retrieve_policy_node,
)
from app.agent.state import SupportState


def route_intent(state: SupportState) -> str:
    intent = state["intent"]
    if intent == "order_status":
        return "order_status"
    if intent == "refund":
        return "refund"
    if intent == "address_change":
        return "address_change"
    return "policy"


def build_support_graph():
    graph = StateGraph(SupportState)
    graph.add_node("classify", classify_node)
    graph.add_node("retrieve_policy", retrieve_policy_node)
    graph.add_node("order_status", execute_order_status_node)
    graph.add_node("refund", execute_refund_node)
    graph.add_node("address_change", execute_address_change_node)
    graph.add_node("policy", execute_policy_node)
    graph.add_node("log", log_node)

    graph.add_edge(START, "classify")
    graph.add_conditional_edges(
        "classify",
        route_intent,
        {
            "order_status": "order_status",
            "refund": "refund",
            "address_change": "address_change",
            "policy": "retrieve_policy",
        },
    )
    graph.add_edge("retrieve_policy", "policy")
    graph.add_edge("order_status", "log")
    graph.add_edge("refund", "log")
    graph.add_edge("address_change", "log")
    graph.add_edge("policy", "log")
    graph.add_edge("log", END)
    return graph.compile()
