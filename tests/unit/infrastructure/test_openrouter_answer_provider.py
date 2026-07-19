from types import SimpleNamespace
from unittest.mock import patch

import pytest
from openai import OpenAIError

from app.core.exceptions import AnswerConfigurationError, AnswerProviderError
from app.infrastructure.answers.openai_provider import SYSTEM_INSTRUCTION
from app.infrastructure.answers.openrouter_provider import (
    DEFAULT_OPENROUTER_BASE_URL,
    DEFAULT_OPENROUTER_CHAT_MODEL,
    OpenRouterAnswerProvider,
)
from app.modules.documents.schemas.search import SearchResult


class FakeResponsesAPI:
    """Test double for the OpenAI-compatible Responses API."""

    def __init__(
        self,
        *,
        output_text: str = "Generated answer.",
        error: Exception | None = None,
    ) -> None:
        self.output_text = output_text
        self.error = error
        self.calls: list[dict[str, object]] = []

    def create(
        self,
        *,
        model: str,
        instructions: str,
        input: str,
        temperature: float,
        max_output_tokens: int,
    ) -> SimpleNamespace:
        self.calls.append(
            {
                "model": model,
                "instructions": instructions,
                "input": input,
                "temperature": temperature,
                "max_output_tokens": max_output_tokens,
            }
        )
        if self.error is not None:
            raise self.error
        return SimpleNamespace(output_text=self.output_text)


class FakeOpenAIClient:
    """Test double for an OpenAI-compatible client."""

    def __init__(self, responses_api: FakeResponsesAPI) -> None:
        self.responses = responses_api


@pytest.fixture
def context_chunks() -> list[SearchResult]:
    return [
        SearchResult(chunk_index=0, text="ERP integrations are required.", score=0.9),
        SearchResult(chunk_index=1, text="Pricing details follow.", score=0.5),
    ]


@pytest.fixture
def provider() -> OpenRouterAnswerProvider:
    responses_api = FakeResponsesAPI(output_text="OpenRouter generated answer.")
    client = FakeOpenAIClient(responses_api)
    return OpenRouterAnswerProvider(
        api_key="test-key",
        base_url=DEFAULT_OPENROUTER_BASE_URL,
        model=DEFAULT_OPENROUTER_CHAT_MODEL,
        temperature=0.0,
        max_output_tokens=800,
        client=client,
    )


def test_generate_answer_returns_model_output(
    provider: OpenRouterAnswerProvider,
    context_chunks: list[SearchResult],
) -> None:
    answer = provider.generate_answer("What integrations are required?", context_chunks)

    assert answer == "OpenRouter generated answer."


def test_openrouter_client_is_configured_with_base_url_and_api_key() -> None:
    with patch("app.infrastructure.answers.openrouter_provider.OpenAI") as openai_cls:
        openai_cls.return_value = FakeOpenAIClient(FakeResponsesAPI())

        OpenRouterAnswerProvider(
            api_key="router-key",
            base_url="https://openrouter.ai/api/v1",
            model="openrouter/free",
        )

    openai_cls.assert_called_once_with(
        api_key="router-key",
        base_url="https://openrouter.ai/api/v1",
    )


def test_generate_answer_uses_shared_prompt_and_context_handling(
    provider: OpenRouterAnswerProvider,
    context_chunks: list[SearchResult],
) -> None:
    question = "What integrations are required?"
    provider.generate_answer(question, context_chunks)

    call = provider._client.responses.calls[0]
    assert call["instructions"] == SYSTEM_INSTRUCTION
    assert question in call["input"]
    assert "[Chunk 0]" in call["input"]
    assert "ERP integrations are required." in call["input"]


def test_missing_api_key_raises_configuration_error() -> None:
    with pytest.raises(AnswerConfigurationError, match="OpenRouter API key is required"):
        OpenRouterAnswerProvider(api_key="")


def test_api_error_is_translated_to_answer_provider_error(
    context_chunks: list[SearchResult],
) -> None:
    responses_api = FakeResponsesAPI(error=OpenAIError("upstream failure"))
    provider = OpenRouterAnswerProvider(
        api_key="test-key",
        client=FakeOpenAIClient(responses_api),
    )

    with pytest.raises(AnswerProviderError, match="OpenRouter answer request failed"):
        provider.generate_answer("question", context_chunks)

    assert "test-key" not in str(responses_api.calls)


def test_configured_temperature_and_max_output_tokens_are_used(
    context_chunks: list[SearchResult],
) -> None:
    responses_api = FakeResponsesAPI()
    provider = OpenRouterAnswerProvider(
        api_key="test-key",
        temperature=0.4,
        max_output_tokens=512,
        client=FakeOpenAIClient(responses_api),
    )

    provider.generate_answer("question", context_chunks)

    assert responses_api.calls[0]["temperature"] == 0.4
    assert responses_api.calls[0]["max_output_tokens"] == 512
