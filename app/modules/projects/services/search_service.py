from app.infrastructure.answers.constants import INSUFFICIENT_CONTEXT_ANSWER
from app.infrastructure.answers.protocol import AnswerProvider
from app.infrastructure.embeddings.protocol import EmbeddingProvider
from app.infrastructure.vector_store.protocol import VectorStore
from app.modules.documents.schemas.search import SearchRequest
from app.modules.documents.services.citations import build_answer_sources, build_citations
from app.modules.documents.services.context import has_usable_context
from app.modules.documents.services.search_metadata import enrich_project_search_results
from app.modules.projects.schemas.search import (
    ProjectAskRequest,
    ProjectAskResponse,
    ProjectSearchResponse,
)
from app.modules.projects.services.project_service import ProjectService


class ProjectSearchService:
    """Semantic search across all indexed documents in a project."""

    def __init__(
        self,
        project_service: ProjectService,
        provider: EmbeddingProvider,
        vector_store: VectorStore,
        *,
        embedding_model: str,
    ) -> None:
        self._project_service = project_service
        self._provider = provider
        self._vector_store = vector_store
        self._embedding_model = embedding_model

    def search(self, project_id: str, request: SearchRequest) -> ProjectSearchResponse:
        """Search indexed chunks across every document in the project."""
        project = self._project_service.require_metadata(project_id)
        query_vector = self._provider.embed(request.query)
        results = self._vector_store.search_documents(
            project.document_ids,
            query_vector,
            request.top_k,
        )
        results = enrich_project_search_results(
            project=project,
            results=results,
            embedding_model=self._embedding_model,
        )
        return ProjectSearchResponse(
            project_id=project_id,
            query=request.query,
            result_count=len(results),
            results=results,
        )


class ProjectAskService:
    """Answers questions using project-wide semantic search."""

    def __init__(
        self,
        search_service: ProjectSearchService,
        answer_provider: AnswerProvider,
    ) -> None:
        self._search_service = search_service
        self._answer_provider = answer_provider

    def ask(self, project_id: str, request: ProjectAskRequest) -> ProjectAskResponse:
        """Retrieve cross-document context and generate a grounded answer."""
        search_response = self._search_service.search(
            project_id,
            SearchRequest(query=request.question, top_k=request.top_k),
        )
        if not has_usable_context(search_response.results):
            answer = INSUFFICIENT_CONTEXT_ANSWER
        else:
            answer = self._answer_provider.generate_answer(
                request.question,
                search_response.results,
            )
        sources = build_answer_sources(search_response.results)
        citations = build_citations(search_response.results)
        return ProjectAskResponse(
            project_id=project_id,
            question=request.question,
            answer=answer,
            sources=sources,
            citations=citations,
            status="answered",
        )
