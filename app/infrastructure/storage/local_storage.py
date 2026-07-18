from pathlib import Path


class LocalFileStorage:
    """Stores files on the local filesystem under a configurable root directory."""

    def __init__(self, root_dir: Path | str = "uploads") -> None:
        self._root_dir = Path(root_dir)

    def save(self, relative_path: str, content: bytes) -> None:
        """Write content to disk, creating parent directories as needed."""
        destination = self._root_dir / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)

    def load(self, relative_path: str) -> bytes:
        """Read content from disk.

        Raises:
            FileNotFoundError: If the relative path does not exist.
        """
        source = self._root_dir / relative_path
        if not source.is_file():
            raise FileNotFoundError(relative_path)
        return source.read_bytes()
