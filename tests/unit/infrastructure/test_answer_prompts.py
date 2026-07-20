from app.infrastructure.answers.prompts import SYSTEM_INSTRUCTION, build_answer_prompt
from app.modules.documents.schemas.search import SearchResult
from app.modules.documents.schemas.source_metadata import SourceMetadata


def test_system_instruction_requires_page_references() -> None:
    assert "page numbers" in SYSTEM_INSTRUCTION.lower()


def test_build_answer_prompt_includes_source_metadata() -> None:
    metadata = SourceMetadata(
        document_id="doc-1",
        document_name="RFP.pdf",
        page_number=5,
        chunk_id="doc-1-chunk-0",
        chunk_index=0,
        embedding_model="mock",
        created_at="2026-01-01T00:00:00+00:00",
    )
    context = [SearchResult(chunk_index=0, text="Requirement text", score=0.9, metadata=metadata)]

    prompt = build_answer_prompt("What is required?", context)

    assert "Document:\nRFP.pdf" in prompt
    assert "Page:\n5" in prompt
    assert "Chunk:\n0" in prompt
    assert "Requirement text" in prompt
