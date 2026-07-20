from datetime import UTC, datetime

import pytest

from app.modules.documents.schemas.chunk import TextChunk
from app.modules.documents.schemas.document import DocumentMetadata
from app.modules.documents.schemas.search import SearchResult
from app.modules.documents.services.search_metadata import enrich_search_results


class FakeMetadataService:
    def get(self, document_id: str) -> DocumentMetadata:
        return DocumentMetadata(
            document_id=document_id,
            filename="RFP.pdf",
            content_type="application/pdf",
            size_bytes=100,
            status="uploaded",
            page_count=1,
            characters=100,
            created_at=datetime.now(UTC),
        )


class FakeChunkService:
    def chunk(self, document_id: str) -> object:
        class Response:
            chunks = [
                TextChunk(
                    index=0,
                    text="integration requirements",
                    characters=24,
                    page_number=2,
                )
            ]

        return Response()


def test_enrich_search_results_fills_missing_metadata() -> None:
    results = [
        SearchResult(chunk_index=0, text="integration requirements", score=0.9, metadata=None),
    ]

    enriched = enrich_search_results(
        document_id="doc-1",
        results=results,
        metadata_service=FakeMetadataService(),
        chunk_service=FakeChunkService(),
        embedding_model="mock",
    )

    assert enriched[0].metadata is not None
    assert enriched[0].metadata.document_name == "RFP.pdf"
    assert enriched[0].metadata.page_number == 2
    assert enriched[0].metadata.chunk_index == 0
