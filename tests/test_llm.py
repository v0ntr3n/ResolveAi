from app.agent.llm import generate_policy_answer


def test_generate_policy_answer_falls_back_without_api_key():
    answer = generate_policy_answer(
        question="What is the refund policy?",
        policy_context="Refunds within 7 days.",
        language="en",
        api_key="",
    )

    assert "Refunds within 7 days." in answer
