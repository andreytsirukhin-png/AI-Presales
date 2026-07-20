from app.infrastructure.embeddings.protocol import EmbeddingProvider
from app.infrastructure.vector_store.protocol import VectorStore
from app.modules.documents.schemas.search import SearchRequest, SearchResponse
from app.modules.documents.services.chunk_service import ChunkService
from app.modules.documents.services.metadata_service import MetadataService
from app.modules.documents.services.search_metadata import enrich_search_results


class SearchService:
    """Performs semantic search over indexed document chunks."""

    def __init__(
        self,
        provider: EmbeddingProvider,
        vector_store: VectorStore,
        metadata_service: MetadataService,
        chunk_service: ChunkService,
        *,
        embedding_model: str,
    ) -> None:
        self._provider = provider
        self._vector_store = vector_store
        self._metadata_service = metadata_service
        self._chunk_service = chunk_service
        self._embedding_model = embedding_model

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
        results = enrich_search_results(
            document_id=document_id,
            results=results,
            metadata_service=self._metadata_service,
            chunk_service=self._chunk_service,
            embedding_model=self._embedding_model,
        )

        return SearchResponse(
            document_id=document_id,
            query=request.query,
            result_count=len(results),
            results=results,
        )
