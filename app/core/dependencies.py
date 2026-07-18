from functools import lru_cache

from fastapi import Depends

from app.infrastructure.answers import MockAnswerProvider
from app.infrastructure.answers.protocol import AnswerProvider
from app.infrastructure.embeddings import MockEmbeddingProvider
from app.infrastructure.embeddings.protocol import EmbeddingProvider
from app.infrastructure.storage import LocalFileStorage
from app.infrastructure.storage.protocol import FileStorage
from app.infrastructure.vector_store import InMemoryVectorStore
from app.infrastructure.vector_store.protocol import VectorStore
from app.modules.documents.chunkers.text_chunker import TextChunker
from app.modules.documents.parsers.pdf_parser import PDFParser
from app.modules.documents.services.ask_service import AskService
from app.modules.documents.services.chunk_service import ChunkService
from app.modules.documents.services.embedding_service import EmbeddingService
from app.modules.documents.services.index_service import IndexService
from app.modules.documents.services.metadata_service import MetadataService
from app.modules.documents.services.parse_service import ParseService
from app.modules.documents.services.search_service import SearchService
from app.services.upload_service import UploadService


@lru_cache
def get_file_storage() -> FileStorage:
    """Return the shared file storage instance."""
    return LocalFileStorage()


@lru_cache
def get_pdf_parser() -> PDFParser:
    """Return the shared PDF parser instance."""
    return PDFParser()


@lru_cache
def get_text_chunker() -> TextChunker:
    """Return the shared text chunker instance."""
    return TextChunker()


@lru_cache
def get_embedding_provider() -> EmbeddingProvider:
    """Return the shared embedding provider instance."""
    return MockEmbeddingProvider()


@lru_cache
def get_vector_store() -> VectorStore:
    """Return the shared vector store instance."""
    return InMemoryVectorStore()


@lru_cache
def get_answer_provider() -> AnswerProvider:
    """Return the shared answer provider instance."""
    return MockAnswerProvider()


def get_metadata_service(
    storage: FileStorage = Depends(get_file_storage),
) -> MetadataService:
    """Build the metadata service for the current request."""
    return MetadataService(storage)


def get_parse_service(
    storage: FileStorage = Depends(get_file_storage),
    parser: PDFParser = Depends(get_pdf_parser),
) -> ParseService:
    """Build the parse service for the current request."""
    return ParseService(storage, parser=parser)


def get_chunk_service(
    storage: FileStorage = Depends(get_file_storage),
    parser: PDFParser = Depends(get_pdf_parser),
    chunker: TextChunker = Depends(get_text_chunker),
) -> ChunkService:
    """Build the chunk service for the current request."""
    return ChunkService(storage, parser=parser, chunker=chunker)


def get_upload_service(
    storage: FileStorage = Depends(get_file_storage),
) -> UploadService:
    """Build the upload service for the current request."""
    return UploadService(storage)


def get_embedding_service(
    metadata_service: MetadataService = Depends(get_metadata_service),
    chunk_service: ChunkService = Depends(get_chunk_service),
    provider: EmbeddingProvider = Depends(get_embedding_provider),
) -> EmbeddingService:
    """Build the embedding service for the current request."""
    return EmbeddingService(
        metadata_service=metadata_service,
        chunk_service=chunk_service,
        provider=provider,
    )


def get_index_service(
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    vector_store: VectorStore = Depends(get_vector_store),
) -> IndexService:
    """Build the index service for the current request."""
    return IndexService(
        embedding_service=embedding_service,
        vector_store=vector_store,
    )


def get_search_service(
    provider: EmbeddingProvider = Depends(get_embedding_provider),
    vector_store: VectorStore = Depends(get_vector_store),
) -> SearchService:
    """Build the search service for the current request."""
    return SearchService(provider=provider, vector_store=vector_store)


def get_ask_service(
    search_service: SearchService = Depends(get_search_service),
    answer_provider: AnswerProvider = Depends(get_answer_provider),
) -> AskService:
    """Build the ask service for the current request."""
    return AskService(
        search_service=search_service,
        answer_provider=answer_provider,
    )
