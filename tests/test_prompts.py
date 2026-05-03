from app.agent.prompts import build_policy_prompt


def test_build_policy_prompt_includes_question_and_context():
    prompt = build_policy_prompt("What is the refund policy?", "Refunds within 7 days.", "en")

    assert "What is the refund policy?" in prompt
    assert "Refunds within 7 days." in prompt
    assert "English" in prompt
