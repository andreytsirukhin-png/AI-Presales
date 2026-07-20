from pathlib import Path

from app.modules.projects.schemas.project import ProjectMetadata


class ProjectStorage:
    """Persists project workspace metadata on the local filesystem."""

    def __init__(self, root_dir: Path | str = "uploads") -> None:
        self._root_dir = Path(root_dir)
        self._projects_dir = self._root_dir / "projects"

    def save(self, project: ProjectMetadata) -> None:
        """Write project metadata to disk."""
        destination = self._project_path(project.project_id)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(project.model_dump_json(), encoding="utf-8")

    def get(self, project_id: str) -> ProjectMetadata:
        """Load project metadata.

        Raises:
            FileNotFoundError: If the project does not exist.
        """
        source = self._project_path(project_id)
        if not source.is_file():
            raise FileNotFoundError(project_id)
        return ProjectMetadata.model_validate_json(source.read_text(encoding="utf-8"))

    def list_projects(self) -> list[ProjectMetadata]:
        """Return all persisted projects sorted by creation time."""
        if not self._projects_dir.is_dir():
            return []
        projects: list[ProjectMetadata] = []
        for path in self._projects_dir.glob("*.project.json"):
            projects.append(
                ProjectMetadata.model_validate_json(path.read_text(encoding="utf-8"))
            )
        return sorted(projects, key=lambda project: project.created_at)

    def delete(self, project_id: str) -> None:
        """Remove project metadata from disk.

        Raises:
            FileNotFoundError: If the project does not exist.
        """
        source = self._project_path(project_id)
        if not source.is_file():
            raise FileNotFoundError(project_id)
        source.unlink()

    def _project_path(self, project_id: str) -> Path:
        return self._projects_dir / f"{project_id}.project.json"
