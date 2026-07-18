from typing import Protocol


class FileStorage(Protocol):
    """Abstraction for persisting and loading document bytes."""

    def save(self, relative_path: str, content: bytes) -> None:
        """Persist content at the given path relative to the storage root."""
        ...

    def load(self, relative_path: str) -> bytes:
        """Load content from the given path relative to the storage root.

        Raises:
            FileNotFoundError: If the path does not exist.
        """
        ...
