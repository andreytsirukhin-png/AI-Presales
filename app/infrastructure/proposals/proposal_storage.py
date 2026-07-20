from pathlib import Path

from app.modules.projects.schemas.proposal import Proposal


class ProposalStorage:
    """Persists generated proposals alongside project workspace metadata."""

    def __init__(self, root_dir: Path | str = "uploads") -> None:
        self._root_dir = Path(root_dir)
        self._projects_dir = self._root_dir / "projects"

    def save(self, proposal: Proposal) -> None:
        """Write a proposal cache file for a project."""
        destination = self._proposal_path(proposal.project_id)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(proposal.model_dump_json(), encoding="utf-8")

    def get(self, project_id: str) -> Proposal:
        """Load a cached proposal.

        Raises:
            FileNotFoundError: If no proposal exists for the project.
        """
        source = self._proposal_path(project_id)
        if not source.is_file():
            raise FileNotFoundError(project_id)
        return Proposal.model_validate_json(source.read_text(encoding="utf-8"))

    def delete(self, project_id: str) -> None:
        """Remove a cached proposal.

        Raises:
            FileNotFoundError: If no proposal exists for the project.
        """
        source = self._proposal_path(project_id)
        if not source.is_file():
            raise FileNotFoundError(project_id)
        source.unlink()

    def exists(self, project_id: str) -> bool:
        """Return whether a proposal cache file exists."""
        return self._proposal_path(project_id).is_file()

    def _proposal_path(self, project_id: str) -> Path:
        return self._projects_dir / f"{project_id}.proposal.json"
