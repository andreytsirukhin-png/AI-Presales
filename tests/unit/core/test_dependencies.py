import importlib
from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.core.dependencies import (
    build_answer_provider,
    build_embedding_provider,
    build_file_storage,
    build_vector_store,
    clear_dependency_caches,
    get_answer_provider,
    get_pdf_parser,
    get_text_chunker,
)
from app.main import app
from app.modules.documents.schemas.search import SearchResult
from app.modules.documents.services.ask_service import AskService
from app.modules.documents.services.chunk_service import ChunkService
from app.modules.documents.services.embedding_service import EmbeddingService
from app.modules.documents.services.index_service import IndexService
from app.modules.documents.services.metadata_service import MetadataService
from app.modules.documents.services.parse_service import ParseService
from app.modules.documents.services.search_service import SearchService
from app.services.upload_service import UploadService
from tests.helpers.pdf import make_text_pdf

client = TestClient(app)


def _current_settings() -> Settings:
    return get_settings()


def test_shared_vector_store_instance_is_reused() -> None:
    settings = _current_settings()
    first = build_vector_store(settings.vector_store_backend)
    second = build_vector_store(settings.vector_store_backend)

    assert first is second


def test_shared_file_storage_instance_is_reused() -> None:
    settings = _current_settings()
    first = build_file_storage(settings.storage_backend, settings.storage_path)
    second = build_file_storage(settings.storage_backend, settings.storage_path)

    assert first is second


def test_storage_path_comes_from_settings() -> None:
    settings = _current_settings()
    storage = build_file_storage(settings.storage_backend, settings.storage_path)

    assert storage._root_dir == Path(settings.storage_path)


def test_embedding_dimension_comes_from_settings() -> None:
    settings = _current_settings()
    provider = build_embedding_provider(
        settings.embedding_provider,
        settings.embedding_dimension,
        settings.openai_api_key,
        settings.openai_embedding_model,
    )

    assert provider.dimension == settings.embedding_dimension


def test_default_vector_store_is_memory() -> None:
    settings = _current_settings()

    assert settings.vector_store_backend == "memory"


def test_default_answer_provider_is_mock() -> None:
    settings = _current_settings()
    provider = build_answer_provider(
        settings.answer_provider,
        settings.openai_api_key,
        settings.openai_chat_model,
        settings.openai_temperature,
        settings.openai_max_output_tokens,
        settings.openrouter_api_key,
        settings.openrouter_base_url,
        settings.openrouter_chat_model,
    )

    assert provider.generate_answer("question", []) is not None


def test_different_storage_path_creates_different_cached_instance() -> None:
    first = build_file_storage("local", "uploads")
    second = build_file_storage("local", "./other-data")

    assert first is not second


def test_cache_reset_provides_isolation() -> None:
    settings = _current_settings()
    first = build_vector_store(settings.vector_store_backend)
    clear_dependency_caches()
    second = build_vector_store(get_settings().vector_store_backend)

    assert first is not second


def test_service_dependencies_are_resolvable() -> None:
    settings = _current_settings()
    storage = build_file_storage(settings.storage_backend, settings.storage_path)
    vector_store = build_vector_store(settings.vector_store_backend)
    embedding_provider = build_embedding_provider(
        settings.embedding_provider,
        settings.embedding_dimension,
        settings.openai_api_key,
        settings.openai_embedding_model,
    )
    answer_provider = build_answer_provider(
        settings.answer_provider,
        settings.openai_api_key,
        settings.openai_chat_model,
        settings.openai_temperature,
        settings.openai_max_output_tokens,
        settings.openrouter_api_key,
        settings.openrouter_base_url,
        settings.openrouter_chat_model,
    )
    parser = get_pdf_parser()
    chunker = get_text_chunker()

    metadata_service = MetadataService(storage)
    parse_service = ParseService(storage, parser=parser)
    chunk_service = ChunkService(storage, parser=parser, chunker=chunker)
    upload_service = UploadService(storage)
    embedding_service = EmbeddingService(
        metadata_service=metadata_service,
        chunk_service=chunk_service,
        provider=embedding_provider,
    )
    index_service = IndexService(
        embedding_service=embedding_service,
        vector_store=vector_store,
    )
    search_service = SearchService(
        provider=embedding_provider,
        vector_store=vector_store,
    )
    ask_service = AskService(
        search_service=search_service,
        answer_provider=answer_provider,
    )

    assert all(
        [
            metadata_service,
            parse_service,
            chunk_service,
            upload_service,
            embedding_service,
            index_service,
            search_service,
            ask_service,
        ]
    )


def test_document_routes_do_not_define_module_level_services() -> None:
    documents_routes = importlib.import_module("app.modules.documents.api.routes")
    api_routes = importlib.import_module("app.api.routes")

    forbidden_document_names = {
        "_storage",
        "_vector_store",
        "parse_service",
        "metadata_service",
        "chunk_service",
        "embedding_service",
        "index_service",
        "search_service",
        "ask_service",
    }
    forbidden_api_names = {"_storage", "upload_service"}

    for name in forbidden_document_names:
        assert name not in vars(documents_routes)

    for name in forbidden_api_names:
        assert name not in vars(api_routes)


def test_dependency_override_works_for_answer_provider() -> None:
    class OverrideAnswerProvider:
        def generate_answer(
            self,
            question: str,
            context_chunks: list[SearchResult],
        ) -> str:
            return "override answer"

    app.dependency_overrides[get_answer_provider] = lambda: OverrideAnswerProvider()
    try:
        upload_response = client.post(
            "/api/v1/documents/upload",
            files={
                "file": (
                    "rfp.pdf",
                    BytesIO(make_text_pdf("Dependency override integration test")),
                    "application/pdf",
                )
            },
        )
        assert upload_response.status_code == 200
        document_id = upload_response.json()["document_id"]

        index_response = client.post(f"/api/v1/documents/{document_id}/index")
        assert index_response.status_code == 200

        ask_response = client.post(
            f"/api/v1/documents/{document_id}/ask",
            json={"question": "What is tested?", "top_k": 5},
        )
        assert ask_response.status_code == 200
        assert ask_response.json()["answer"] == "override answer"
    finally:
        app.dependency_overrides.clear()


def test_dependency_override_works_for_settings(tmp_path: Path) -> None:
    override_settings = Settings(storage_path=str(tmp_path / "override-storage"))

    app.dependency_overrides[get_settings] = lambda: override_settings
    try:
        upload_response = client.post(
            "/api/v1/documents/upload",
            files={
                "file": (
                    "rfp.pdf",
                    BytesIO(make_text_pdf("Settings override upload")),
                    "application/pdf",
                )
            },
        )
        assert upload_response.status_code == 200
        document_id = upload_response.json()["document_id"]
        assert (tmp_path / "override-storage" / f"{document_id}.pdf").is_file()
    finally:
        app.dependency_overrides.clear()


def test_upload_index_search_works_through_injected_dependencies() -> None:
    upload_response = client.post(
        "/api/v1/documents/upload",
        files={
            "file": (
                "rfp.pdf",
                BytesIO(make_text_pdf("Injected dependency search flow")),
                "application/pdf",
            )
        },
    )
    assert upload_response.status_code == 200
    document_id = upload_response.json()["document_id"]

    index_response = client.post(f"/api/v1/documents/{document_id}/index")
    assert index_response.status_code == 200

    search_response = client.post(
        f"/api/v1/documents/{document_id}/search",
        json={"query": "Injected dependency search flow", "top_k": 5},
    )

    assert search_response.status_code == 200
    assert search_response.json()["result_count"] >= 1


def test_upload_index_ask_works_through_injected_dependencies() -> None:
    upload_response = client.post(
        "/api/v1/documents/upload",
        files={
            "file": (
                "rfp.pdf",
                BytesIO(make_text_pdf("Injected dependency ask flow")),
                "application/pdf",
            )
        },
    )
    assert upload_response.status_code == 200
    document_id = upload_response.json()["document_id"]

    index_response = client.post(f"/api/v1/documents/{document_id}/index")
    assert index_response.status_code == 200

    ask_response = client.post(
        f"/api/v1/documents/{document_id}/ask",
        json={"question": "What is the ask flow?", "top_k": 5},
    )

    assert ask_response.status_code == 200
    assert ask_response.json()["status"] == "answered"


def test_shared_metadata_state_survives_across_requests() -> None:
    upload_response = client.post(
        "/api/v1/documents/upload",
        files={
            "file": (
                "rfp.pdf",
                BytesIO(make_text_pdf("Shared metadata state validation")),
                "application/pdf",
            )
        },
    )
    assert upload_response.status_code == 200
    document_id = upload_response.json()["document_id"]

    metadata_response = client.get(f"/api/v1/documents/{document_id}")

    assert metadata_response.status_code == 200
    assert metadata_response.json()["document_id"] == document_id
    assert metadata_response.json()["status"] == "uploaded"


@pytest.mark.parametrize(
    "builder",
    [
        lambda settings: build_file_storage(settings.storage_backend, settings.storage_path),
        lambda settings: build_embedding_provider(
            settings.embedding_provider,
            settings.embedding_dimension,
            settings.openai_api_key,
            settings.openai_embedding_model,
        ),
        lambda settings: build_vector_store(settings.vector_store_backend),
        lambda settings: build_answer_provider(
            settings.answer_provider,
            settings.openai_api_key,
            settings.openai_chat_model,
            settings.openai_temperature,
            settings.openai_max_output_tokens,
            settings.openrouter_api_key,
            settings.openrouter_base_url,
            settings.openrouter_chat_model,
        ),
    ],
)
def test_infrastructure_builders_are_cached_singletons(builder) -> None:
    settings = _current_settings()
    assert builder(settings) is builder(settings)
