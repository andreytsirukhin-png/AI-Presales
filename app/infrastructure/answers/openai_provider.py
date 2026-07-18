from typing import Protocol

from openai import OpenAI, OpenAIError

from app.core.exceptions import AnswerConfigurationError, AnswerProviderError
from app.modules.documents.schemas.search import SearchResult

DEFAULT_OPENAI_CHAT_MODEL = "gpt-4.1-mini"

SYSTEM_INSTRUCTION = (
    "You answer questions using only the supplied document context. "
    "Do not use external knowledge. "
    "If the answer cannot be found in the context, clearly state that the document "
    "does not contain enough information. "
    "Do not invent facts."
)


class OpenAIClientProtocol(Protocol):
    """Minimal OpenAI client surface required for answer generation."""

    class Responses:
        def create(
            self,
            *,
            model: str,
            instructions: str,
            input: str,
            temperature: float,
            max_output_tokens: int,
        ) -> object: ...

    responses: Responses


def build_answer_prompt(question: str, context_chunks: list[SearchResult]) -> str:
    """Build a deterministic user prompt from a question and retrieved chunks."""
    context_sections: list[str] = []
    for chunk in context_chunks:
        chunk_text = chunk.text.strip()
        if not chunk_text:
            continue
        context_sections.append(f"[Chunk {chunk.chunk_index}]\n{chunk_text}")

    context_body = "\n\n".join(context_sections)
    return (
        f"Question:\n{question.strip()}\n\n"
        "Document Context:\n"
        f"{context_body}"
    )


class OpenAIAnswerProvider:
    """OpenAI-backed answer provider using the Responses API."""

    def __init__(
        self,
        api_key: str,
        *,
        model: str = DEFAULT_OPENAI_CHAT_MODEL,
        temperature: float = 0.0,
        max_output_tokens: int = 800,
        client: OpenAIClientProtocol | None = None,
    ) -> None:
        """Initialize the OpenAI answer provider.

        Args:
            api_key: OpenAI API key.
            model: Chat model name.
            temperature: Sampling temperature for answer generation.
            max_output_tokens: Maximum tokens allowed in the model response.
            client: Optional injected OpenAI client for testing.

        Raises:
            AnswerConfigurationError: If the API key is missing.
        """
        if not api_key.strip():
            raise AnswerConfigurationError(
                "OpenAI API key is required when answer_provider is 'openai'."
            )

        self._model = model
        self._temperature = temperature
        self._max_output_tokens = max_output_tokens
        self._client = client or OpenAI(api_key=api_key)

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
            AnswerProviderError: If the OpenAI request fails or returns no text.
        """
        user_prompt = build_answer_prompt(question, context_chunks)
        if not user_prompt.split("Document Context:\n", maxsplit=1)[1].strip():
            raise AnswerProviderError(
                "OpenAI answer request requires non-empty document context."
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
                f"OpenAI answer request failed: {exc}"
            ) from exc

        output_text = getattr(response, "output_text", None)
        if not isinstance(output_text, str) or not output_text.strip():
            raise AnswerProviderError(
                "OpenAI answer response did not contain generated text."
            )

        return output_text.strip()
