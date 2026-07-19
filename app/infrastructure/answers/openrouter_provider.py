from openai import OpenAI, OpenAIError

from app.core.exceptions import AnswerConfigurationError, AnswerProviderError
from app.infrastructure.answers.openai_provider import (
    OpenAIClientProtocol,
    SYSTEM_INSTRUCTION,
    build_answer_prompt,
)
from app.modules.documents.schemas.search import SearchResult

DEFAULT_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_OPENROUTER_CHAT_MODEL = "openrouter/free"


class OpenRouterAnswerProvider:
    """OpenRouter-backed answer provider using the OpenAI-compatible Responses API."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_OPENROUTER_BASE_URL,
        model: str = DEFAULT_OPENROUTER_CHAT_MODEL,
        temperature: float = 0.0,
        max_output_tokens: int = 800,
        client: OpenAIClientProtocol | None = None,
    ) -> None:
        """Initialize the OpenRouter answer provider.

        Args:
            api_key: OpenRouter API key.
            base_url: OpenRouter OpenAI-compatible API base URL.
            model: Chat model name.
            temperature: Sampling temperature for answer generation.
            max_output_tokens: Maximum tokens allowed in the model response.
            client: Optional injected OpenAI client for testing.

        Raises:
            AnswerConfigurationError: If the API key is missing.
        """
        if not api_key.strip():
            raise AnswerConfigurationError(
                "OpenRouter API key is required when answer_provider is 'openrouter'."
            )

        self._model = model
        self._temperature = temperature
        self._max_output_tokens = max_output_tokens
        self._client = client or OpenAI(api_key=api_key, base_url=base_url)

    def generate_answer(
        self,
        question: str,
        context_chunks: list[SearchResult],
    ) -> str:
        """Generate an answer using only the supplied context chunks.

        Args:
            question: User question to answer.
            context_chunks: Ordered search results used as answer context.

        Returns:
            Generated answer grounded in the supplied context.

        Raises:
            AnswerProviderError: If the OpenRouter request fails or returns no text.
        """
        user_prompt = build_answer_prompt(question, context_chunks)
        if not user_prompt.split("Document Context:\n", maxsplit=1)[1].strip():
            raise AnswerProviderError(
                "OpenRouter answer request requires non-empty document context."
            )

        try:
            response = self._client.responses.create(
                model=self._model,
                instructions=SYSTEM_INSTRUCTION,
                input=user_prompt,
                temperature=self._temperature,
                max_output_tokens=self._max_output_tokens,
            )
        except OpenAIError as exc:
            raise AnswerProviderError(
                f"OpenRouter answer request failed: {exc}"
            ) from exc

        output_text = getattr(response, "output_text", None)
        if not isinstance(output_text, str) or not output_text.strip():
            raise AnswerProviderError(
                "OpenRouter answer response did not contain generated text."
            )

        return output_text.strip()
