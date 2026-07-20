from pathlib import Path

from app.modules.projects.schemas.review import ReviewReport


class ReviewStorage:
    """Persists generated proposal review reports."""

    def __init__(self, root_dir: Path | str = "uploads") -> None:
        self._root_dir = Path(root_dir)
        self._projects_dir = self._root_dir / "projects"

    def save(self, review: ReviewReport) -> None:
        """Write a review cache file for a project."""
        destination = self._review_path(review.project_id)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(review.model_dump_json(), encoding="utf-8")

    def get(self, project_id: str) -> ReviewReport:
        """Load a cached review report."""
        source = self._review_path(project_id)
        if not source.is_file():
            raise FileNotFoundError(project_id)
        return ReviewReport.model_validate_json(source.read_text(encoding="utf-8"))

    def delete(self, project_id: str) -> None:
        """Remove a cached review report."""
        source = self._review_path(project_id)
        if not source.is_file():
            raise FileNotFoundError(project_id)
        source.unlink()

    def exists(self, project_id: str) -> bool:
        """Return whether a review cache exists."""
        return self._review_path(project_id).is_file()

    def _review_path(self, project_id: str) -> Path:
        return self._projects_dir / f"{project_id}.review.json"
