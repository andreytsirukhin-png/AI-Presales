import importlib
from io import BytesIO

import pytest
from fastapi.testclient import TestClient

from app.core.dependencies import (
    get_answer_provider,
    get_embedding_provider,
    get_file_storage,
    get_pdf_parser,
    get_text_chunker,
    get_vector_store,
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


def test_shared_vector_store_instance_is_reused() -> None:
    first = get_vector_store()
    second = get_vector_store()

    assert first is second


def test_shared_file_storage_instance_is_reused() -> None:
    first = get_file_storage()
    second = get_file_storage()

    assert first is second


def test_service_dependencies_are_resolvable() -> None:
    storage = get_file_storage()
    vector_store = get_vector_store()
    embedding_provider = get_embedding_provider()
    answer_provider = get_answer_provider()
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
    "provider",
    [get_embedding_provider, get_vector_store, get_file_storage],
)
def test_infrastructure_providers_are_cached_singletons(provider) -> None:
    assert provider() is provider()
