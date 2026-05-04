"""LLM operations for ResolveAI with RAG-optimized generation."""

from langchain_openai import ChatOpenAI
from langsmith.run_helpers import traceable
from pydantic import BaseModel

from app.agent.prompts import (
    build_policy_prompt,
    build_intent_classification_prompt,
    build_rag_context_prompt,
    RAG_SYSTEM_PROMPT,
)


class IntentClassification(BaseModel):
    """Structured intent classification result."""
    intent: str
    confidence: float


@traceable(name="llm_classification", run_type="llm")
def classify_intent_with_llm(message: str, api_key: str) -> str:
    """Use LLM for intelligent intent classification with LangSmith tracing."""
    if not api_key:
        return "policy_question"
    
    model = ChatOpenAI(
        model="deepseek-chat",
        api_key=api_key,
        base_url="https://api.deepseek.com",
        temperature=0,
    )
    
    prompt = build_intent_classification_prompt(message)
    response = model.invoke(prompt)
    
    # Parse response to extract intent
    content = response.content if isinstance(response.content, str) else ""
    
    # Map LLM response to supported intents
    intent_mapping = {
        "order_status": ["order_status", "track", "where is", "vận đơn", "ở đâu"],
        "refund": ["refund", "hoàn tiền", "return"],
        "address_change": ["address", "địa chỉ", "change address"],
        "policy_question": ["policy", "chính sách", "question"]
    }
    
    content_lower = content.lower()
    for intent, keywords in intent_mapping.items():
        if any(keyword in content_lower for keyword in keywords):
            return intent
    
    return "policy_question"


@traceable(name="llm_policy_generation", run_type="llm")
def generate_policy_answer(question: str, policy_context: str, language: str, api_key: str) -> str:
    """Generate policy answer with RAG-optimized prompt for high faithfulness."""
    if not api_key:
        return policy_context

    try:
        model = ChatOpenAI(
            model="deepseek-chat",
            api_key=api_key,
            base_url="https://api.deepseek.com",
            temperature=0.1,  # Low temperature for consistency
        )
        
        # Use the improved RAG-optimized prompt
        prompt = build_policy_prompt(question, policy_context, language)
        response = model.invoke([
            {"role": "system", "content": RAG_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ])
        
        return response.content if isinstance(response.content, str) else policy_context
    except Exception:
        # Fallback to raw policy context on any API error
        return policy_context


@traceable(name="llm_rag_generation", run_type="llm")
def generate_rag_answer(
    question: str,
    contexts: list[str],
    language: str,
    api_key: str,
) -> str:
    """Generate answer from multiple context chunks with citation.
    
    Optimized for RAGAS metrics:
    - Uses chunk numbering for citation
    - Explicit grounding instructions
    - Handles empty or insufficient context
    """
    if not api_key:
        return "\n\n---\n\n".join(contexts)

    if not contexts or not any(ctx.strip() for ctx in contexts):
        return "I don't have information about that topic. Please contact our support team for assistance."

    try:
        model = ChatOpenAI(
            model="deepseek-chat",
            api_key=api_key,
            base_url="https://api.deepseek.com",
            temperature=0.1,
        )
        
        prompt = build_rag_context_prompt(question, contexts, language)
        response = model.invoke([
            {"role": "system", "content": RAG_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ])
        
        return response.content if isinstance(response.content, str) else "\n\n---\n\n".join(contexts)
    except Exception:
        return "\n\n---\n\n".join(contexts)
