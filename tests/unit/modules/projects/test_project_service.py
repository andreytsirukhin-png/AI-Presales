from datetime import UTC, datetime

import pytest

from app.core.exceptions import ProjectNotFoundError
from app.infrastructure.storage.project_storage import ProjectStorage
from app.modules.projects.schemas.project import ProjectCreateRequest
from app.modules.projects.services.project_service import ProjectService


@pytest.fixture
def project_service(tmp_path: pytest.TempPathFactory) -> ProjectService:
    return ProjectService(ProjectStorage(root_dir=tmp_path))


def test_create_and_list_projects(project_service: ProjectService) -> None:
    created = project_service.create(
        ProjectCreateRequest(project_name="Workspace A", description="demo")
    )
    projects = project_service.list_projects()
    assert len(projects) == 1
    assert projects[0].project_id == created.project_id
    assert projects[0].document_count == 0


def test_delete_project(project_service: ProjectService) -> None:
    created = project_service.create(
        ProjectCreateRequest(project_name="Temporary", description="")
    )
    project_service.delete(created.project_id)
    with pytest.raises(ProjectNotFoundError):
        project_service.get(created.project_id)
