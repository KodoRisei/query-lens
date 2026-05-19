from app.ai.base import LLMProvider
from app.ai.providers.anthropic import AnthropicProvider
from app.ai.providers.ollama import OllamaProvider
from app.ai.providers.openai import OpenAIProvider
from app.core.config import LLMProvider as LLMProviderName
from app.core.config import Settings, get_settings
from app.core.exceptions import LLMProviderNotConfigured

_registry: dict[LLMProviderName, type] = {
    LLMProviderName.openai: OpenAIProvider,
    LLMProviderName.anthropic: AnthropicProvider,
    LLMProviderName.ollama: OllamaProvider,
}

# Module-level cache: one instance per provider type.
_instances: dict[LLMProviderName, LLMProvider] = {}


def get_provider(
    name: LLMProviderName | None = None,
    settings: Settings | None = None,
) -> LLMProvider:
    """
    Return a cached LLM provider instance.

    Pass `name` to override the default provider from config.
    Pass `settings` in tests to inject a custom configuration.
    """
    cfg = settings or get_settings()
    provider_name = name or cfg.default_llm_provider

    if provider_name not in _instances:
        provider_class = _registry.get(provider_name)
        if provider_class is None:
            raise LLMProviderNotConfigured(
                message=f"Unknown LLM provider '{provider_name}'.",
                provider=str(provider_name),
            )
        _instances[provider_name] = provider_class(cfg)

    return _instances[provider_name]


def clear_provider_cache() -> None:
    """Clear the instance cache — intended for testing."""
    _instances.clear()
