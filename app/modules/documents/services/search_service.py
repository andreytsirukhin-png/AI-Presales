from app.infrastructure.embeddings.protocol import EmbeddingProvider
from app.infrastructure.vector_store.protocol import VectorStore
from app.modules.documents.schemas.search import SearchRequest, SearchResponse


class SearchService:
    """Performs semantic search over indexed document chunks."""

    def __init__(
        self,
        provider: EmbeddingProvider,
        vector_store: VectorStore,
    ) -> None:
        self._provider = provider
        self._vector_store = vector_store

    def search(self, document_id: str, request: SearchRequest) -> SearchResponse:
        """Embed a query and search indexed chunks for a document.

        Args:
            document_id: Identifier of the indexed document.
            request: Validated search request parameters.

        Returns:
            Ranked chunk matches for the query.

        Raises:
            DocumentNotFoundError: If the document is not indexed.
            ValueError: If vector dimensions do not match stored embeddings.
        """
        query_vector = self._provider.embed(request.query)
        results = self._vector_store.search(
            document_id=document_id,
            query_vector=query_vector,
            top_k=request.top_k,
        )

        return SearchResponse(
            document_id=document_id,
            query=request.query,
            result_count=len(results),
            results=results,
        )
