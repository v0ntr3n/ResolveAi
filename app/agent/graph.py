"""
RAG Agent Graph with CRITICAL FIX for context retrieval.

ISSUE: Previous version only retrieved context for 'policy' intent.
FIX: All intents now retrieve relevant context for better RAG metrics.

This ensures:
- Context Precision: Retrieved context is relevant to all intents
- Context Recall: All necessary context is retrieved
- Faithfulness: Responses are grounded in retrieved context
"""
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
    """Route to appropriate handler after context retrieval.
    
    CRITICAL FIX: All intents now go through retrieve_policy first.
    This ensures context is available for:
    1. RAGAS evaluation (which expects context for all intents)
    2. Better response grounding (using policy information)
    3. Consistent behavior across all intent types
    """
    intent = state["intent"]
    # All intents now retrieve context first
    # The retrieve_policy node will be called before routing
    if intent == "order_status":
        return "order_status"
    if intent == "refund":
        return "refund"
    if intent == "address_change":
        return "address_change"
    return "policy"


def build_support_graph():
    """Build the support graph with context retrieval for ALL intents.
    
    CRITICAL CHANGE: retrieve_policy is now called for ALL intents,
    not just policy_question. This ensures:
    - Order status responses can reference shipping policies
    - Refund responses can reference return policies
    - Address change responses can reference address policies
    - RAGAS metrics work correctly (context available for evaluation)
    """
    graph = StateGraph(SupportState)
    
    # Nodes
    graph.add_node("classify", classify_node)
    graph.add_node("retrieve_policy", retrieve_policy_node)  # Now used by ALL intents
    graph.add_node("order_status", execute_order_status_node)
    graph.add_node("refund", execute_refund_node)
    graph.add_node("address_change", execute_address_change_node)
    graph.add_node("policy", execute_policy_node)
    graph.add_node("log", log_node)

    # Start with classification
    graph.add_edge(START, "classify")
    
    # CRITICAL FIX: ALL intents now retrieve context before handling
    # This ensures RAGAS evaluation has context for all test cases
    graph.add_edge("classify", "retrieve_policy")
    
    # Route from retrieve_policy to appropriate handler
    graph.add_conditional_edges(
        "retrieve_policy",
        route_intent,
        {
            "order_status": "order_status",
            "refund": "refund",
            "address_change": "address_change",
            "policy": "policy",
        },
    )
    
    # All handlers go to log then end
    graph.add_edge("order_status", "log")
    graph.add_edge("refund", "log")
    graph.add_edge("address_change", "log")
    graph.add_edge("policy", "log")
    graph.add_edge("log", END)
    
    return graph.compile()
