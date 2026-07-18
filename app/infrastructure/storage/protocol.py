from typing import Protocol


class FileStorage(Protocol):
    """Abstraction for persisting uploaded document bytes."""

    def save(self, relative_path: str, content: bytes) -> None:
        """Persist content at the given path relative to the storage root."""
        ...

    def read(self, relative_path: str) -> bytes:
        """Read content from the given path relative to the storage root.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        ...
