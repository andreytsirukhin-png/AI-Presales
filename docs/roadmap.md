# Roadmap

Implementation status for the AI Presales platform. Updated to reflect the current codebase.

## Delivered

- ✅ Upload (PDF validation, 25 MB limit, local storage)
- ✅ Parsing (pypdf text extraction)
- ✅ Chunking (text chunker with ordered indices)
- ✅ Embeddings abstraction (`EmbeddingProvider` protocol)
- ✅ Mock embedding provider
- ✅ OpenAI embedding provider
- ✅ Vector search (in-memory cosine similarity)
- ✅ Indexing (per-document vector store)
- ✅ RAG ask endpoint (`POST /documents/{id}/ask`)
- ✅ Mock answer provider
- ✅ OpenAI answer provider
- ✅ OpenRouter answer provider
- ✅ Provider dependency injection (`app/core/dependencies.py`)
- ✅ Platform status API (`GET /api/v1/status`)
- ✅ Streamlit demo UI (HTTP-only client)
- ✅ Analysis dashboard (seven preset analyses via `/ask`)
- ✅ Custom Q&A in Streamlit
- ✅ Source chunk display in UI
- ✅ Demo run script (`scripts/run_demo.sh`)
- ✅ Unit and integration tests (250 tests)
- ✅ Test isolation from developer `.env`
- ✅ OpenAPI interactive docs
- ✅ Legacy structured demo endpoint (`POST /api/v1/analysis/demo`)

## Planned

- ⬜ Real embeddings persistence (survive restarts)
- ⬜ Ollama provider
- ⬜ Inline citations with page numbers
- ⬜ Multi-document search
- ⬜ Authentication and authorization
- ⬜ PostgreSQL database
- ⬜ pgvector integration
- ⬜ Docker Compose deployment
- ⬜ CI/CD pipeline
- ⬜ Azure deployment
- ⬜ Evaluation framework (RAG quality metrics)
- ⬜ Response streaming
- ⬜ Dedicated analysis API (structured JSON output)
- ⬜ Word/document formats beyond PDF
- ⬜ Screenshot assets for documentation

## Notes

- **Analysis dashboard** uses preset prompts on the existing `/ask` endpoint rather than a separate analysis service. Structured output remains available only through the legacy `/analysis/demo` stub.
- **Embeddings and answers** are independently configurable. OpenRouter is supported for answers only; use OpenAI or mock for embeddings today.
- **Vector store** is in-memory. Restarting the backend clears indexed embeddings unless the document is reprocessed.

## Related documentation

- [Architecture](architecture.md)
- [Providers](providers.md)
- [Development guide](development.md)
