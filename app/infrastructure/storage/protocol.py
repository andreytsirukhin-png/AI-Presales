from typing import Protocol


class FileStorage(Protocol):
    """Abstraction for persisting uploaded document bytes."""

    def save(self, relative_path: str, content: bytes) -> None:
        """Persist content at the given path relative to the storage root."""
        ...
