from pathlib import Path


def test_policy_files_have_bilingual_sections():
    base_dir = Path("data/knowledge_base")
    files = [
        "return_policy.md",
        "shipping_policy.md",
        "address_change_policy.md",
        "escalation_policy.md",
    ]

    for file_name in files:
        content = (base_dir / file_name).read_text(encoding="utf-8")
        assert "## English" in content
        assert "## Vietnamese" in content
