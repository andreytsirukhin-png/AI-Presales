from types import SimpleNamespace

import pytest
from openai import OpenAIError

from app.core.exceptions import AnswerConfigurationError, AnswerProviderError
from app.infrastructure.answers.openai_provider import (
    DEFAULT_OPENAI_CHAT_MODEL,
    SYSTEM_INSTRUCTION,
    OpenAIAnswerProvider,
    build_answer_prompt,
)
from app.modules.documents.schemas.search import SearchResult


class FakeResponsesAPI:
    """Test double for the OpenAI Responses API."""

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
    """Test double for an OpenAI client."""

    def __init__(self, responses_api: FakeResponsesAPI) -> None:
        self.responses = responses_api


@pytest.fixture
def context_chunks() -> list[SearchResult]:
    return [
        SearchResult(chunk_index=0, text="ERP integrations are required.", score=0.9),
        SearchResult(chunk_index=1, text="Pricing details follow.", score=0.5),
    ]


@pytest.fixture
def provider() -> OpenAIAnswerProvider:
    responses_api = FakeResponsesAPI(output_text="OpenAI generated answer.")
    client = FakeOpenAIClient(responses_api)
    return OpenAIAnswerProvider(
        api_key="test-key",
        model="gpt-4.1-mini",
        temperature=0.0,
        max_output_tokens=800,
        client=client,
    )


def test_generate_answer_returns_model_output(
    provider: OpenAIAnswerProvider,
    context_chunks: list[SearchResult],
) -> None:
    answer = provider.generate_answer("What integrations are required?", context_chunks)

    assert answer == "OpenAI generated answer."


def test_generate_answer_includes_question_and_context_in_request(
    provider: OpenAIAnswerProvider,
    context_chunks: list[SearchResult],
) -> None:
    question = "What integrations are required?"
    provider.generate_answer(question, context_chunks)

    call = provider._client.responses.calls[0]
    assert call["instructions"] == SYSTEM_INSTRUCTION
    assert question in call["input"]
    assert "[Chunk 0]" in call["input"]
    assert "ERP integrations are required." in call["input"]
    assert "[Chunk 1]" in call["input"]
    assert "Pricing details follow." in call["input"]


def test_generate_answer_preserves_chunk_order(
    provider: OpenAIAnswerProvider,
) -> None:
    context = [
        SearchResult(chunk_index=2, text="third", score=0.3),
        SearchResult(chunk_index=0, text="first", score=0.9),
        SearchResult(chunk_index=1, text="second", score=0.6),
    ]

    provider.generate_answer("ordered context", context)

    prompt = provider._client.responses.calls[0]["input"]
    assert prompt.index("[Chunk 2]") < prompt.index("[Chunk 0]")
    assert prompt.index("[Chunk 0]") < prompt.index("[Chunk 1]")


def test_build_answer_prompt_is_deterministic() -> None:
    context = [
        SearchResult(chunk_index=0, text="alpha", score=0.9),
        SearchResult(chunk_index=1, text="beta", score=0.8),
    ]

    first = build_answer_prompt("question", context)
    second = build_answer_prompt("question", context)

    assert first == second
    assert first == (
        "Question:\nquestion\n\n"
        "Document Context:\n"
        "[Chunk 0]\nalpha\n\n"
        "[Chunk 1]\nbeta"
    )


def test_missing_api_key_raises_configuration_error() -> None:
    with pytest.raises(AnswerConfigurationError):
        OpenAIAnswerProvider(api_key="")


def test_api_error_is_translated_to_answer_provider_error(
    context_chunks: list[SearchResult],
) -> None:
    responses_api = FakeResponsesAPI(error=OpenAIError("boom"))
    provider = OpenAIAnswerProvider(
        api_key="test-key",
        client=FakeOpenAIClient(responses_api),
    )

    with pytest.raises(AnswerProviderError, match="OpenAI answer request failed"):
        provider.generate_answer("question", context_chunks)


def test_empty_sdk_response_raises_answer_provider_error(
    context_chunks: list[SearchResult],
) -> None:
    responses_api = FakeResponsesAPI(output_text="   ")
    provider = OpenAIAnswerProvider(
        api_key="test-key",
        client=FakeOpenAIClient(responses_api),
    )

    with pytest.raises(
        AnswerProviderError,
        match="OpenAI answer response did not contain generated text",
    ):
        provider.generate_answer("question", context_chunks)


def test_invalid_sdk_response_type_raises_answer_provider_error(
    context_chunks: list[SearchResult],
) -> None:
    class EmptyOutputResponsesAPI(FakeResponsesAPI):
        def create(self, **kwargs: object) -> SimpleNamespace:
            self.calls.append(kwargs)
            return SimpleNamespace(output_text=None)

    provider = OpenAIAnswerProvider(
        api_key="test-key",
        client=FakeOpenAIClient(EmptyOutputResponsesAPI()),
    )

    with pytest.raises(
        AnswerProviderError,
        match="OpenAI answer response did not contain generated text",
    ):
        provider.generate_answer("question", context_chunks)


def test_configured_model_is_used(context_chunks: list[SearchResult]) -> None:
    responses_api = FakeResponsesAPI()
    provider = OpenAIAnswerProvider(
        api_key="test-key",
        model="custom-model",
        client=FakeOpenAIClient(responses_api),
    )

    provider.generate_answer("question", context_chunks)

    assert responses_api.calls[0]["model"] == "custom-model"


def test_configured_temperature_is_used(context_chunks: list[SearchResult]) -> None:
    responses_api = FakeResponsesAPI()
    provider = OpenAIAnswerProvider(
        api_key="test-key",
        temperature=0.7,
        client=FakeOpenAIClient(responses_api),
    )

    provider.generate_answer("question", context_chunks)

    assert responses_api.calls[0]["temperature"] == 0.7


def test_configured_max_output_tokens_is_used(
    context_chunks: list[SearchResult],
) -> None:
    responses_api = FakeResponsesAPI()
    provider = OpenAIAnswerProvider(
        api_key="test-key",
        max_output_tokens=512,
        client=FakeOpenAIClient(responses_api),
    )

    provider.generate_answer("question", context_chunks)

    assert responses_api.calls[0]["max_output_tokens"] == 512


def test_default_model_constant() -> None:
    assert DEFAULT_OPENAI_CHAT_MODEL == "gpt-4.1-mini"
