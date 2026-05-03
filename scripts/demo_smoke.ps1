@'
from fastapi.testclient import TestClient
from app.main import app

demo_prompts = [
    "Where is my order ORD-000001?",
    "Refund order ORD-000055 because it is damaged",
    "Change shipping address for ORD-000001 to 456 New Street, Hanoi",
    "Chính sách hoàn tiền là gì?",
]

with TestClient(app) as client:
    for prompt in demo_prompts:
        result = client.post("/chat", json={"message": prompt}).json()
        print("=" * 80)
        print(f"Prompt: {prompt}")
        print(f"Intent: {result['intent']}")
        print(f"Resolved: {result['resolved']}")
        print(f"Needs human: {result['requires_human']}")
        print(f"Tool: {result['tool_used']}")
        print(f"Response: {result['response']}")
'@ | uv run python -
