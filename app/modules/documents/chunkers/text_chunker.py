from app.modules.documents.schemas.chunk import TextChunk

DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 150


class TextChunker:
    """Split plain text into overlapping, word-aware chunks."""

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ) -> None:
        """Initialize the chunker with validated sizing parameters.

        Args:
            chunk_size: Maximum number of source characters per chunk window.
            chunk_overlap: Number of source characters repeated between adjacent chunks.

        Raises:
            ValueError: If the sizing parameters are invalid.
        """
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be greater than or equal to 0")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")

        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    @property
    def chunk_size(self) -> int:
        """Return the configured maximum chunk window size."""
        return self._chunk_size

    @property
    def chunk_overlap(self) -> int:
        """Return the configured overlap between adjacent chunks."""
        return self._chunk_overlap

    def chunk(self, text: str) -> list[TextChunk]:
        """Split text into ordered, non-empty chunks.

        Args:
            text: Source text to split.

        Returns:
            Deterministic chunk list preserving source order.
        """
        if not text:
            return []

        chunks: list[TextChunk] = []
        start = 0
        text_length = len(text)

        while start < text_length:
            window_end = min(start + self._chunk_size, text_length)

            if window_end < text_length:
                split_end = window_end
                for index in range(window_end - 1, start, -1):
                    if text[index].isspace():
                        split_end = index
                        break
                end = split_end
            else:
                end = window_end

            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append(
                    TextChunk(
                        index=len(chunks),
                        text=chunk_text,
                        characters=len(chunk_text),
                    )
                )

            if end >= text_length:
                break

            if chunk_text:
                next_start = max(start + 1, end - self._chunk_overlap)
            else:
                next_start = end if end > start else start + 1

            start = next_start

        return chunks
