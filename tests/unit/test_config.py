import pytest
from agent_aichain.core.config import Settings


def test_settings_default_values():
    """Test Settings default values"""
    settings = Settings(
        secret_key="test-secret-key",
        agno_api_key="test-agno-key"
    )
    assert settings.database_url == "postgresql+asyncpg://user:password@localhost:5432/agent_aichain"
    assert settings.redis_url == "redis://localhost:6379/0"
    assert settings.algorithm == "HS256"
    assert settings.access_token_expire_minutes == 30
    assert settings.log_level == "INFO"