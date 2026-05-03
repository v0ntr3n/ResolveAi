from app.core.config import Settings


def test_settings_defaults():
    settings = Settings(DEEPSEEK_API_KEY="test-key")

    assert settings.DEEPSEEK_MODEL == "deepseek-chat"
    assert settings.DATABASE_URL.endswith("data/orders.db")
    assert settings.REFUND_APPROVAL_THRESHOLD == 50.0
    assert settings.AUTO_SEED_DATA is True
