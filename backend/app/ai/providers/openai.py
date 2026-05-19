import openai
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
    openai.RateLimitError,
    openai.APITimeoutError,
    openai.APIConnectionError,
)


class OpenAIProvider:
    provider_name = "openai"

    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key:
            raise LLMProviderNotConfigured(
                message="OpenAI provider requires OPENAI_API_KEY to be set.",
                provider=self.provider_name,
            )
        self._client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_model

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
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": m.role, "content": m.content} for m in messages],
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
            )
        except openai.AuthenticationError as exc:
            raise LLMProviderError(
                message="OpenAI authentication failed — check your API key.",
                provider=self.provider_name,
                status_code=401,
            ) from exc
        except openai.BadRequestError as exc:
            raise LLMProviderError(
                message=f"OpenAI rejected the request: {exc}",
                provider=self.provider_name,
                status_code=400,
            ) from exc
        except _RETRYABLE as exc:
            raise LLMProviderError(
                message=f"OpenAI request failed after retries: {exc}",
                provider=self.provider_name,
            ) from exc

        choice = response.choices[0]
        usage = response.usage

        logger.info(
            "openai.complete",
            model=self._model,
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
        )

        return LLMResponse(
            content=choice.message.content or "",
            provider=self.provider_name,
            model=self._model,
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
        )
