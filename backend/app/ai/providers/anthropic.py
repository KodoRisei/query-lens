import anthropic
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.ai.base import LLMResponse, Message
from app.core.config import Settings
from app.core.exceptions import LLMProviderError, LLMProviderNotConfigured
from app.core.logging import get_logger

logger = get_logger(__name__)

_RETRYABLE = (
    anthropic.RateLimitError,
    anthropic.APIConnectionError,
    anthropic.APITimeoutError,
)


class AnthropicProvider:
    provider_name = "anthropic"

    def __init__(self, settings: Settings) -> None:
        if not settings.anthropic_api_key:
            raise LLMProviderNotConfigured(
                message="Anthropic provider requires ANTHROPIC_API_KEY to be set.",
                provider=self.provider_name,
            )
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._model = settings.anthropic_model

    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(_RETRYABLE),
        reraise=True,
    )
    async def complete(
        self,
        messages: list[Message],
        *,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        # Anthropic's API takes the system prompt as a separate top-level parameter.
        system, user_messages = self._split_messages(messages)

        try:
            response = await self._client.messages.create(
                model=self._model,
                system=system,
                messages=[{"role": m.role, "content": m.content} for m in user_messages],
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except anthropic.AuthenticationError as exc:
            raise LLMProviderError(
                message="Anthropic authentication failed — check your API key.",
                provider=self.provider_name,
                status_code=401,
            ) from exc
        except anthropic.BadRequestError as exc:
            raise LLMProviderError(
                message=f"Anthropic rejected the request: {exc}",
                provider=self.provider_name,
                status_code=400,
            ) from exc
        except _RETRYABLE as exc:
            raise LLMProviderError(
                message=f"Anthropic request failed after retries: {exc}",
                provider=self.provider_name,
            ) from exc

        content_block = response.content[0]
        text = content_block.text if hasattr(content_block, "text") else ""
        usage = response.usage

        logger.info(
            "anthropic.complete",
            model=self._model,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
        )

        return LLMResponse(
            content=text,
            provider=self.provider_name,
            model=self._model,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
        )

    def _split_messages(self, messages: list[Message]) -> tuple[str, list[Message]]:
        system = next(
            (m.content for m in messages if m.role == "system"), ""
        )
        non_system = [m for m in messages if m.role != "system"]
        return system, non_system
