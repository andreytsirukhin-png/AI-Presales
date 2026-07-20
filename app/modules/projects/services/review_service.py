from datetime import UTC, datetime

from app.core.exceptions import ProposalNotFoundError, ReviewNotFoundError
from app.infrastructure.answers.constants import INSUFFICIENT_CONTEXT_ANSWER
from app.infrastructure.answers.protocol import AnswerProvider
from app.infrastructure.proposals.proposal_storage import ProposalStorage
from app.infrastructure.reviews.review_storage import ReviewStorage
from app.modules.documents.schemas.search import SearchRequest
from app.modules.documents.services.context import has_usable_context
from app.modules.projects.review.sections import (
    REVIEW_CATEGORY_DEFINITIONS,
    get_review_category_definition,
    review_category_keys,
)
from app.modules.projects.schemas.review import ReviewCategoryResult, ReviewReport
from app.modules.projects.services.project_service import ProjectService
from app.modules.projects.services.review_metrics import compute_review_metrics
from app.modules.projects.services.review_parser import parse_category_response
from app.modules.projects.services.search_service import ProjectSearchService


class ReviewService:
    """Generates evidence-based proposal review reports."""

    def __init__(
        self,
        project_service: ProjectService,
        search_service: ProjectSearchService,
        answer_provider: AnswerProvider,
        proposal_storage: ProposalStorage,
        review_storage: ReviewStorage,
    ) -> None:
        self._project_service = project_service
        self._search_service = search_service
        self._answer_provider = answer_provider
        self._proposal_storage = proposal_storage
        self._review_storage = review_storage

    def generate(
        self,
        project_id: str,
        *,
        top_k: int = 8,
        category_keys: list[str] | None = None,
    ) -> ReviewReport:
        """Generate all or selected review categories."""
        project = self._project_service.require_metadata(project_id)
        proposal = self._require_proposal(project_id)
        keys = category_keys or list(review_category_keys())
        self._validate_category_keys(keys)

        existing = self._load_optional(project_id)
        categories_by_key = (
            {category.key: category for category in existing.categories} if existing else {}
        )

        proposal_context = self._format_proposal_context(proposal)
        for key in keys:
            categories_by_key[key] = self._generate_category(
                project_id,
                key,
                top_k=top_k,
                proposal_context=proposal_context,
            )

        categories = [
            categories_by_key[definition.key]
            for definition in REVIEW_CATEGORY_DEFINITIONS
            if definition.key in categories_by_key
        ]
        metrics = compute_review_metrics(categories)
        report = ReviewReport(
            project_id=project_id,
            project_name=project.project_name,
            proposal_generated_at=proposal.generated_at,
            generated_at=datetime.now(UTC),
            metrics=metrics,
            categories=categories,
        )
        self._review_storage.save(report)
        return report

    def regenerate_categories(
        self,
        project_id: str,
        *,
        category_keys: list[str],
        top_k: int = 8,
    ) -> ReviewReport:
        """Regenerate selected review categories in the cache."""
        if not self._review_storage.exists(project_id):
            raise ReviewNotFoundError(f"Review not found: {project_id}")
        return self.generate(project_id, top_k=top_k, category_keys=category_keys)

    def get(self, project_id: str) -> ReviewReport:
        """Return the cached review report."""
        self._project_service.require_metadata(project_id)
        try:
            return self._review_storage.get(project_id)
        except FileNotFoundError as exc:
            raise ReviewNotFoundError(f"Review not found: {project_id}") from exc

    def delete(self, project_id: str) -> None:
        """Delete the cached review report."""
        self._project_service.require_metadata(project_id)
        try:
            self._review_storage.delete(project_id)
        except FileNotFoundError as exc:
            raise ReviewNotFoundError(f"Review not found: {project_id}") from exc

    def _generate_category(
        self,
        project_id: str,
        category_key: str,
        *,
        top_k: int,
        proposal_context: str,
    ) -> ReviewCategoryResult:
        definition = get_review_category_definition(category_key)
        search_response = self._search_service.search(
            project_id,
            SearchRequest(query=definition.search_query, top_k=top_k),
        )
        generated_at = datetime.now(UTC)

        if not has_usable_context(search_response.results):
            return ReviewCategoryResult(
                key=definition.key,
                title=definition.title,
                summary=INSUFFICIENT_CONTEXT_ANSWER,
                findings=[],
                generated_at=generated_at,
                status="insufficient_context",
            )

        prompt = (
            f"{definition.generation_prompt}\n\n"
            f"Proposal excerpt for review:\n{proposal_context}\n\n"
            "Use the document context chunks provided separately."
        )
        raw = self._answer_provider.generate_answer(prompt, search_response.results)
        summary, findings = parse_category_response(
            raw,
            search_results=search_response.results,
        )
        return ReviewCategoryResult(
            key=definition.key,
            title=definition.title,
            summary=summary,
            findings=findings,
            generated_at=generated_at,
            status="generated",
        )

    def _require_proposal(self, project_id: str):
        try:
            return self._proposal_storage.get(project_id)
        except FileNotFoundError as exc:
            raise ProposalNotFoundError(f"Proposal not found: {project_id}") from exc

    @staticmethod
    def _format_proposal_context(proposal) -> str:
        parts: list[str] = []
        for section in proposal.sections:
            parts.append(f"## {section.title}\n{section.content.strip()}")
        return "\n\n".join(parts)[:12000]

    def _load_optional(self, project_id: str) -> ReviewReport | None:
        try:
            return self._review_storage.get(project_id)
        except FileNotFoundError:
            return None

    @staticmethod
    def _validate_category_keys(category_keys: list[str]) -> None:
        valid = set(review_category_keys())
        unknown = [key for key in category_keys if key not in valid]
        if unknown:
            raise ValueError(f"Unknown review category keys: {', '.join(unknown)}")
