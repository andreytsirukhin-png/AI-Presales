from app.infrastructure.answers.mock_provider import FALLBACK_ANSWER, MockAnswerProvider
from app.modules.documents.schemas.search import SearchResult


def test_generate_answer_is_deterministic() -> None:
    provider = MockAnswerProvider()
    context = [
        SearchResult(chunk_index=0, text="ERP integrations are required.", score=0.9),
        SearchResult(chunk_index=1, text="Pricing details follow.", score=0.5),
    ]

    first = provider.generate_answer("What integrations are required?", context)
    second = provider.generate_answer("What integrations are required?", context)

    assert first == second
    assert first == (
        "Based on the indexed document: ERP integrations are required. Pricing details follow."
    )


def test_generate_answer_preserves_context_order() -> None:
    provider = MockAnswerProvider()
    context = [
        SearchResult(chunk_index=2, text="third", score=0.3),
        SearchResult(chunk_index=0, text="first", score=0.9),
        SearchResult(chunk_index=1, text="second", score=0.6),
    ]

    answer = provider.generate_answer("ordered context", context)

    assert answer == "Based on the indexed document: third first second"


def test_generate_answer_ignores_empty_text() -> None:
    provider = MockAnswerProvider()
    context = [
        SearchResult(chunk_index=0, text="   ", score=0.9),
        SearchResult(chunk_index=1, text="usable content", score=0.8),
    ]

    answer = provider.generate_answer("question", context)

    assert answer == "Based on the indexed document: usable content"


def test_generate_answer_returns_fallback_when_context_is_empty() -> None:
    provider = MockAnswerProvider()

    answer = provider.generate_answer("question", [])

    assert answer == FALLBACK_ANSWER


def test_generate_answer_returns_fallback_when_all_chunk_texts_are_empty() -> None:
    provider = MockAnswerProvider()
    context = [
        SearchResult(chunk_index=0, text="   ", score=0.9),
        SearchResult(chunk_index=1, text="", score=0.8),
    ]

    answer = provider.generate_answer("question", context)

    assert answer == FALLBACK_ANSWER
