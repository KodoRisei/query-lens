from dataclasses import dataclass
from typing import Literal, Protocol, runtime_checkable


@dataclass(frozen=True)
class Message:
    role: Literal["system", "user", "assistant"]
    content: str


@dataclass(frozen=True)
class LLMResponse:
    content: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int


@runtime_checkable
class LLMProvider(Protocol):
    """
    Structural interface for all LLM providers.

    Implementing this Protocol requires no inheritance — any class with a
    matching `complete` method and `provider_name` property satisfies it.
    The domain layer depends only on this interface, never on SDK-specific types.
    """

    @property
    def provider_name(self) -> str: ...

    async def complete(
        self,
        messages: list[Message],
        *,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> LLMResponse: ...
