from datetime import UTC, datetime

from app.core.exceptions import ProposalNotFoundError
from app.infrastructure.answers.constants import INSUFFICIENT_CONTEXT_ANSWER
from app.infrastructure.answers.protocol import AnswerProvider
from app.infrastructure.proposals.proposal_storage import ProposalStorage
from app.modules.documents.schemas.search import SearchRequest
from app.modules.documents.services.citations import build_answer_sources, build_citations
from app.modules.documents.services.context import has_usable_context
from app.modules.projects.proposal.sections import (
    PROPOSAL_SECTION_DEFINITIONS,
    get_section_definition,
    proposal_section_keys,
)
from app.modules.projects.schemas.proposal import (
    Proposal,
    ProposalSection,
)
from app.modules.projects.services.project_service import ProjectService
from app.modules.projects.services.search_service import ProjectSearchService


class ProposalService:
    """Generates and caches multi-section commercial proposals for projects."""

    def __init__(
        self,
        project_service: ProjectService,
        search_service: ProjectSearchService,
        answer_provider: AnswerProvider,
        storage: ProposalStorage,
    ) -> None:
        self._project_service = project_service
        self._search_service = search_service
        self._answer_provider = answer_provider
        self._storage = storage

    def generate(
        self,
        project_id: str,
        *,
        top_k: int = 8,
        section_keys: list[str] | None = None,
    ) -> Proposal:
        """Generate all or selected proposal sections and merge into the cache."""
        project = self._project_service.require_metadata(project_id)
        keys = section_keys or list(proposal_section_keys())
        self._validate_section_keys(keys)

        existing = self._load_optional(project_id)
        sections_by_key = {section.key: section for section in existing.sections} if existing else {}

        for key in keys:
            sections_by_key[key] = self._generate_section(project_id, key, top_k=top_k)

        proposal = Proposal(
            project_id=project_id,
            project_name=project.project_name,
            generated_at=datetime.now(UTC),
            sections=[
                sections_by_key[definition.key]
                for definition in PROPOSAL_SECTION_DEFINITIONS
                if definition.key in sections_by_key
            ],
        )
        self._storage.save(proposal)
        return proposal

    def regenerate_sections(
        self,
        project_id: str,
        *,
        section_keys: list[str],
        top_k: int = 8,
    ) -> Proposal:
        """Regenerate only the selected sections in the cached proposal."""
        if not self._storage.exists(project_id):
            raise ProposalNotFoundError(f"Proposal not found: {project_id}")
        return self.generate(project_id, top_k=top_k, section_keys=section_keys)

    def get(self, project_id: str) -> Proposal:
        """Return the cached proposal for a project."""
        self._project_service.require_metadata(project_id)
        try:
            return self._storage.get(project_id)
        except FileNotFoundError as exc:
            raise ProposalNotFoundError(f"Proposal not found: {project_id}") from exc

    def delete(self, project_id: str) -> None:
        """Delete the cached proposal for a project."""
        self._project_service.require_metadata(project_id)
        try:
            self._storage.delete(project_id)
        except FileNotFoundError as exc:
            raise ProposalNotFoundError(f"Proposal not found: {project_id}") from exc

    def _generate_section(
        self,
        project_id: str,
        section_key: str,
        *,
        top_k: int,
    ) -> ProposalSection:
        definition = get_section_definition(section_key)
        search_response = self._search_service.search(
            project_id,
            SearchRequest(query=definition.search_query, top_k=top_k),
        )
        generated_at = datetime.now(UTC)
        if not has_usable_context(search_response.results):
            content = INSUFFICIENT_CONTEXT_ANSWER
            status = "insufficient_context"
        else:
            content = self._answer_provider.generate_answer(
                definition.generation_prompt,
                search_response.results,
            )
            status = "generated"

        return ProposalSection(
            key=definition.key,
            title=definition.title,
            content=content,
            citations=build_citations(search_response.results),
            sources=build_answer_sources(search_response.results),
            generated_at=generated_at,
            status=status,
        )

    def _load_optional(self, project_id: str) -> Proposal | None:
        try:
            return self._storage.get(project_id)
        except FileNotFoundError:
            return None

    @staticmethod
    def _validate_section_keys(section_keys: list[str]) -> None:
        valid = set(proposal_section_keys())
        unknown = [key for key in section_keys if key not in valid]
        if unknown:
            raise ValueError(f"Unknown proposal section keys: {', '.join(unknown)}")
