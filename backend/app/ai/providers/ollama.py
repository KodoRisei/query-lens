import openai
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.ai.base import LLMResponse, Message
from app.core.config import Settings
from app.core.exceptions import LLMProviderError
from app.core.logging import get_logger

logger = get_logger(__name__)

_RETRYABLE = (
    openai.APITimeoutError,
    openai.APIConnectionError,
)


class OllamaProvider:
    """
    Ollama provider using the OpenAI-compatible REST API that Ollama exposes.

    No API key required. The base URL points at the local Ollama instance.
    We reuse the OpenAI client because Ollama's /v1 endpoint is compatible.
    """

    provider_name = "ollama"

    def __init__(self, settings: Settings) -> None:
        self._client = openai.AsyncOpenAI(
            base_url=f"{settings.ollama_base_url}/v1",
            api_key="ollama",  # Required by the client but not validated by Ollama
        )
        self._model = settings.ollama_model

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=15),
        stop=stop_after_attempt(2),
        retry=retry_if_exception_type(_RETRYABLE),
        reraise=True,
    )
    async def complete(
        self,
        messages: list[Message],
        *,
        temperature: float = 0.3,
        max_tokens: int = 512,
    ) -> LLMResponse:
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": m.role, "content": m.content} for m in messages],  # type: ignore[misc]
                temperature=temperature,
                max_tokens=max_tokens,
                # Ollama's JSON mode support depends on the model; omit response_format
                # and rely on the response parser's fallback handling instead.
            )
        except openai.APIConnectionError as exc:
            raise LLMProviderError(
                message=(
                    "Cannot reach Ollama at the configured URL. "
                    "Ensure Ollama is running and OLLAMA_BASE_URL is correct."
                ),
                provider=self.provider_name,
            ) from exc
        except _RETRYABLE as exc:
            raise LLMProviderError(
                message=f"Ollama request failed after retries: {exc}",
                provider=self.provider_name,
            ) from exc

        choice = response.choices[0]
        usage = response.usage

        logger.info(
            "ollama.complete",
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
