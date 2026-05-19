import pytest

from app.ai.factory import clear_provider_cache, get_provider
from app.ai.providers.anthropic import AnthropicProvider
from app.ai.providers.ollama import OllamaProvider
from app.ai.providers.openai import OpenAIProvider
from app.core.config import LLMProvider as LLMProviderName
from app.core.config import Settings
from app.core.exceptions import LLMProviderNotConfigured


def settings_with(**overrides) -> Settings:
    base = {
        "database_url": "postgresql+asyncpg://x:x@localhost:5432/x",
        "openai_api_key": "sk-test",
        "anthropic_api_key": "test-key",
    }
    base.update(overrides)
    return Settings(**base)


@pytest.fixture(autouse=True)
def clear_cache():
    clear_provider_cache()
    yield
    clear_provider_cache()


def test_get_openai_provider():
    settings = settings_with(default_llm_provider=LLMProviderName.openai)
    provider = get_provider(LLMProviderName.openai, settings=settings)
    assert isinstance(provider, OpenAIProvider)


def test_get_anthropic_provider():
    settings = settings_with(default_llm_provider=LLMProviderName.anthropic)
    provider = get_provider(LLMProviderName.anthropic, settings=settings)
    assert isinstance(provider, AnthropicProvider)


def test_get_ollama_provider():
    settings = settings_with(default_llm_provider=LLMProviderName.ollama)
    provider = get_provider(LLMProviderName.ollama, settings=settings)
    assert isinstance(provider, OllamaProvider)


def test_openai_missing_key_raises():
    settings = settings_with(openai_api_key="")
    with pytest.raises(LLMProviderNotConfigured) as exc_info:
        get_provider(LLMProviderName.openai, settings=settings)
    assert exc_info.value.provider == "openai"


def test_anthropic_missing_key_raises():
    settings = settings_with(anthropic_api_key="")
    with pytest.raises(LLMProviderNotConfigured) as exc_info:
        get_provider(LLMProviderName.anthropic, settings=settings)
    assert exc_info.value.provider == "anthropic"


def test_same_instance_returned_on_second_call():
    settings = settings_with(default_llm_provider=LLMProviderName.openai)
    p1 = get_provider(LLMProviderName.openai, settings=settings)
    p2 = get_provider(LLMProviderName.openai, settings=settings)
    assert p1 is p2


def test_provider_satisfies_protocol():
    from app.ai.base import LLMProvider

    settings = settings_with()
    provider = get_provider(LLMProviderName.openai, settings=settings)
    assert isinstance(provider, LLMProvider)
