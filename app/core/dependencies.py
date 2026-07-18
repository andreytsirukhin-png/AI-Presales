from functools import lru_cache

from fastapi import Depends

from app.core.config import Settings, get_settings
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
def build_file_storage(storage_backend: str, storage_path: str) -> FileStorage:
    """Build a cached file storage instance for the given configuration."""
    if storage_backend != "local":
        raise ValueError(f"Unsupported storage backend: {storage_backend}")
    return LocalFileStorage(root_dir=storage_path)


@lru_cache
def build_embedding_provider(provider_name: str, dimension: int) -> EmbeddingProvider:
    """Build a cached embedding provider for the given configuration."""
    if provider_name != "mock":
        raise ValueError(f"Unsupported embedding provider: {provider_name}")
    return MockEmbeddingProvider(dimension=dimension)


@lru_cache
def build_vector_store(backend: str) -> VectorStore:
    """Build a cached vector store for the given configuration."""
    if backend != "memory":
        raise ValueError(f"Unsupported vector store backend: {backend}")
    return InMemoryVectorStore()


@lru_cache
def build_answer_provider(provider_name: str) -> AnswerProvider:
    """Build a cached answer provider for the given configuration."""
    if provider_name != "mock":
        raise ValueError(f"Unsupported answer provider: {provider_name}")
    return MockAnswerProvider()


@lru_cache
def get_pdf_parser() -> PDFParser:
    """Return the shared PDF parser instance."""
    return PDFParser()


@lru_cache
def get_text_chunker() -> TextChunker:
    """Return the shared text chunker instance."""
    return TextChunker()


def get_file_storage(
    settings: Settings = Depends(get_settings),
) -> FileStorage:
    """Return the shared file storage instance."""
    return build_file_storage(settings.storage_backend, settings.storage_path)


def get_embedding_provider(
    settings: Settings = Depends(get_settings),
) -> EmbeddingProvider:
    """Return the shared embedding provider instance."""
    return build_embedding_provider(
        settings.embedding_provider,
        settings.embedding_dimension,
    )


def get_vector_store(
    settings: Settings = Depends(get_settings),
) -> VectorStore:
    """Return the shared vector store instance."""
    return build_vector_store(settings.vector_store_backend)


def get_answer_provider(
    settings: Settings = Depends(get_settings),
) -> AnswerProvider:
    """Return the shared answer provider instance."""
    return build_answer_provider(settings.answer_provider)


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


def clear_dependency_caches() -> None:
    """Clear cached settings and infrastructure instances for test isolation."""
    from app.core.config import clear_settings_cache

    clear_settings_cache()
    build_file_storage.cache_clear()
    build_embedding_provider.cache_clear()
    build_vector_store.cache_clear()
    build_answer_provider.cache_clear()
    get_pdf_parser.cache_clear()
    get_text_chunker.cache_clear()
