def build_intent_classification_prompt(message: str) -> str:
    """Build prompt for intent classification."""
    return f"""Classify the following customer message into one of these intents:
- order_status: Customer asking about order location, tracking, or delivery status
- refund: Customer requesting a refund or return
- address_change: Customer wanting to change shipping address
- policy_question: Customer asking about policies (shipping, returns, etc.)

Message: {message}

Intent:"""


def build_policy_prompt(question: str, policy_context: str, language: str) -> str:
    language_name = "Vietnamese" if language == "vi" else "English"
    return (
        f"You are a support agent. Answer in {language_name} using only the policy context below.\n\n"
        f"Question:\n{question}\n\n"
        f"Policy Context:\n{policy_context}\n\n"
        "If the policy context is incomplete, say that a human agent should review the request."
    )
