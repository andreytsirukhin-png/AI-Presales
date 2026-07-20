from datetime import UTC, datetime
from uuid import uuid4

from app.core.exceptions import DocumentNotFoundError, ProjectNotFoundError
from app.infrastructure.storage.project_storage import ProjectStorage
from app.modules.projects.schemas.project import (
    ProjectCreateRequest,
    ProjectMetadata,
    ProjectResponse,
    ProjectStatisticsResponse,
)


class ProjectService:
    """Manages workspace project metadata."""

    def __init__(self, storage: ProjectStorage) -> None:
        self._storage = storage

    def create(self, request: ProjectCreateRequest) -> ProjectResponse:
        """Create a new empty project workspace."""
        project = ProjectMetadata(
            project_id=str(uuid4()),
            project_name=request.project_name.strip(),
            description=request.description.strip(),
            created_at=datetime.now(UTC),
            document_ids=[],
        )
        self._storage.save(project)
        return self._to_response(project)

    def list_projects(self) -> list[ProjectResponse]:
        """Return all projects."""
        return [self._to_response(project) for project in self._storage.list_projects()]

    def get(self, project_id: str) -> ProjectResponse:
        """Return one project by identifier."""
        return self._to_response(self._require_project(project_id))

    def delete(self, project_id: str) -> None:
        """Delete project metadata."""
        self._require_project(project_id)
        self._storage.delete(project_id)

    def require_metadata(self, project_id: str) -> ProjectMetadata:
        """Return raw project metadata or raise."""
        return self._require_project(project_id)

    def attach_document(self, project_id: str, document_id: str) -> ProjectMetadata:
        """Associate a document with a project."""
        project = self._require_project(project_id)
        if document_id not in project.document_ids:
            project = project.model_copy(
                update={"document_ids": [*project.document_ids, document_id]}
            )
            self._storage.save(project)
        return project

    def detach_document(self, project_id: str, document_id: str) -> ProjectMetadata:
        """Remove a document association from a project."""
        project = self._require_project(project_id)
        if document_id in project.document_ids:
            project = project.model_copy(
                update={
                    "document_ids": [
                        current_id
                        for current_id in project.document_ids
                        if current_id != document_id
                    ]
                }
            )
            self._storage.save(project)
        return project

    def mark_indexed(self, project_id: str, indexed_at: datetime) -> None:
        """Update the project's last indexing timestamp."""
        project = self._require_project(project_id)
        self._storage.save(project.model_copy(update={"last_indexed_at": indexed_at}))

    def statistics(
        self,
        project_id: str,
        *,
        indexed_chunks: int,
        embedding_provider: str,
        embedding_model: str,
        vector_store: str,
    ) -> ProjectStatisticsResponse:
        """Build runtime statistics for a project."""
        project = self._require_project(project_id)
        return ProjectStatisticsResponse(
            project_id=project.project_id,
            project_name=project.project_name,
            document_count=len(project.document_ids),
            indexed_chunks=indexed_chunks,
            embedding_provider=embedding_provider,
            embedding_model=embedding_model,
            vector_store=vector_store,
            last_indexed_at=project.last_indexed_at,
        )

    def _require_project(self, project_id: str) -> ProjectMetadata:
        try:
            return self._storage.get(project_id)
        except FileNotFoundError as exc:
            raise ProjectNotFoundError(f"Project not found: {project_id}") from exc

    @staticmethod
    def _to_response(project: ProjectMetadata) -> ProjectResponse:
        return ProjectResponse(
            project_id=project.project_id,
            project_name=project.project_name,
            description=project.description,
            created_at=project.created_at,
            document_count=len(project.document_ids),
            last_indexed_at=project.last_indexed_at,
        )
