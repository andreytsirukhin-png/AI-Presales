import pytest

from app.modules.documents.chunkers.text_chunker import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    TextChunker,
)


def test_default_configuration() -> None:
    chunker = TextChunker()

    assert chunker.chunk_size == DEFAULT_CHUNK_SIZE
    assert chunker.chunk_overlap == DEFAULT_CHUNK_OVERLAP


def test_short_text_returns_one_chunk() -> None:
    chunker = TextChunker(chunk_size=100, chunk_overlap=10)

    chunks = chunker.chunk("Short document text.")

    assert len(chunks) == 1
    assert chunks[0].index == 0
    assert chunks[0].text == "Short document text."


def test_long_text_returns_multiple_chunks() -> None:
    chunker = TextChunker(chunk_size=50, chunk_overlap=10)
    text = " ".join(f"word{i}" for i in range(100))

    chunks = chunker.chunk(text)

    assert len(chunks) > 1
    assert chunks[0].index == 0
    assert chunks[-1].index == len(chunks) - 1


def test_overlap_is_present_between_adjacent_chunks() -> None:
    chunker = TextChunker(chunk_size=40, chunk_overlap=10)
    text = "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu"

    chunks = chunker.chunk(text)

    assert len(chunks) >= 2
    assert chunks[0].text[-10:] in chunks[1].text or chunks[0].text.split()[-1] in chunks[1].text


def test_indices_are_sequential() -> None:
    chunker = TextChunker(chunk_size=30, chunk_overlap=5)
    text = " ".join(["chunkable"] * 20)

    chunks = chunker.chunk(text)

    assert [chunk.index for chunk in chunks] == list(range(len(chunks)))


def test_characters_equals_len_text() -> None:
    chunker = TextChunker(chunk_size=25, chunk_overlap=5)
    text = "word " * 30

    chunks = chunker.chunk(text)

    for chunk in chunks:
        assert chunk.characters == len(chunk.text)


def test_no_empty_chunks() -> None:
    chunker = TextChunker(chunk_size=20, chunk_overlap=5)
    text = "   leading   and trailing   spaces   " + ("content " * 15)

    chunks = chunker.chunk(text)

    assert chunks
    assert all(chunk.text for chunk in chunks)


def test_whitespace_only_input_returns_no_chunks() -> None:
    chunker = TextChunker()

    assert chunker.chunk("   \n\t  ") == []


def test_exact_chunk_size_input_returns_one_chunk() -> None:
    chunker = TextChunker(chunk_size=100, chunk_overlap=10)
    text = "a" * 100

    chunks = chunker.chunk(text)

    assert len(chunks) == 1
    assert chunks[0].text == text
    assert chunks[0].characters == 100


@pytest.mark.parametrize(
    ("chunk_size", "chunk_overlap"),
    [
        (0, 0),
        (-1, 0),
        (100, -1),
        (100, 100),
        (100, 150),
    ],
)
def test_invalid_configuration_raises_value_error(
    chunk_size: int,
    chunk_overlap: int,
) -> None:
    with pytest.raises(ValueError):
        TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)


def test_long_word_without_whitespace_is_split() -> None:
    chunker = TextChunker(chunk_size=50, chunk_overlap=10)
    text = "x" * 120

    chunks = chunker.chunk(text)

    assert len(chunks) >= 2
    assert sum(chunk.characters for chunk in chunks) >= len(text) - chunker.chunk_overlap


def test_algorithm_always_makes_forward_progress() -> None:
    chunker = TextChunker(chunk_size=10, chunk_overlap=9)
    pathological_inputs = [
        " " * 500,
        (" " * 20 + "a" + " " * 20 + "b") * 10,
        "\n\t\r" * 200,
        "word " * 200,
    ]

    for text in pathological_inputs:
        chunks = chunker.chunk(text)
        assert all(chunk.text for chunk in chunks)
        assert len(chunks) <= len(text)


def test_chunking_is_deterministic() -> None:
    chunker = TextChunker(chunk_size=60, chunk_overlap=15)
    text = "deterministic chunking " * 25

    first = chunker.chunk(text)
    second = chunker.chunk(text)

    assert first == second


def test_chunks_preserve_source_order() -> None:
    chunker = TextChunker(chunk_size=20, chunk_overlap=5)
    text = "first second third fourth fifth sixth seventh"

    chunks = chunker.chunk(text)
    combined = " ".join(chunk.text for chunk in chunks)

    assert combined.index("first") < combined.index("third") < combined.index("seventh")
