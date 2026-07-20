from datetime import UTC, datetime

import pytest

from app.infrastructure.proposals.proposal_storage import ProposalStorage
from app.modules.documents.schemas.ask import AnswerCitation
from app.modules.documents.schemas.search import SearchResponse, SearchResult
from app.modules.documents.schemas.source_metadata import SourceMetadata
from app.modules.projects.proposal.sections import proposal_section_keys
from app.modules.projects.schemas.project import ProjectMetadata
from app.modules.projects.schemas.proposal import Proposal, ProposalSection
from app.modules.projects.services.proposal_service import ProposalService


class FakeProjectService:
    def require_metadata(self, project_id: str) -> ProjectMetadata:
        return ProjectMetadata(
            project_id=project_id,
            project_name="Demo Project",
            description="",
            created_at=datetime.now(UTC),
            document_ids=["doc-1"],
        )


class FakeSearchService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def search(self, project_id: str, request: object) -> SearchResponse:
        query = getattr(request, "query")
        self.calls.append((project_id, query))
        metadata = SourceMetadata(
            document_id="doc-1",
            document_name="RFP.pdf",
            page_number=1,
            chunk_id="doc-1-chunk-0",
            chunk_index=0,
            embedding_model="mock",
            created_at="2026-01-01T00:00:00+00:00",
            project_id=project_id,
            project_name="Demo Project",
        )
        return SearchResponse(
            document_id=project_id,
            query=query,
            result_count=1,
            results=[
                SearchResult(
                    chunk_index=0,
                    text="Sample retrieved context.",
                    score=0.91,
                    metadata=metadata,
                )
            ],
        )


class FakeAnswerProvider:
    def generate_answer(self, question: str, context_chunks: list[SearchResult]) -> str:
        return f"Answer for: {question[:40]}"


@pytest.fixture
def proposal_service(tmp_path: pytest.TempPathFactory) -> ProposalService:
    return ProposalService(
        project_service=FakeProjectService(),
        search_service=FakeSearchService(),
        answer_provider=FakeAnswerProvider(),
        storage=ProposalStorage(root_dir=tmp_path),
    )


def test_generate_proposal_creates_all_sections(proposal_service: ProposalService) -> None:
    proposal = proposal_service.generate("project-1", top_k=5)

    assert len(proposal.sections) == len(proposal_section_keys())
    assert all(section.citations for section in proposal.sections)
    assert proposal_service.get("project-1").project_id == "project-1"


def test_regenerate_updates_only_selected_section(proposal_service: ProposalService) -> None:
    search_service = proposal_service._search_service
    assert isinstance(search_service, FakeSearchService)
    proposal_service.generate("project-1", top_k=5)
    calls_before = len(search_service.calls)

    proposal_service.regenerate_sections(
        "project-1",
        section_keys=["executive_summary"],
        top_k=5,
    )
    assert len(search_service.calls) == calls_before + 1
    assert len(proposal_service.get("project-1").sections) == len(proposal_section_keys())
