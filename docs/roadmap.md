# Roadmap

Implementation status for the AI Presales platform. Updated to reflect the current codebase.

## Delivered

- ✅ Upload (PDF validation, 25 MB limit, local storage)
- ✅ Parsing (pypdf text extraction)
- ✅ Chunking (text chunker with ordered indices)
- ✅ Embeddings abstraction (`EmbeddingProvider` protocol)
- ✅ Mock embedding provider
- ✅ OpenAI embedding provider
- ✅ Ollama embedding provider
- ✅ Vector store abstraction (`VectorStore` protocol)
- ✅ In-memory vector store (`inmemory`)
- ✅ ChromaDB persistent vector store (`chroma`)
- ✅ Vector search (cosine similarity)
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
- ✅ Unit and integration tests (278 tests)
- ✅ Test isolation from developer `.env`
- ✅ OpenAPI interactive docs
- ✅ Legacy structured demo endpoint (`POST /api/v1/analysis/demo`)

## Planned

- ⬜ Cross-document search in Chroma
- ⬜ Ollama answer provider
- ✅ Source citations and traceable RAG (US-016)
- ✅ Project workspace and multi-document retrieval (US-017)
- ✅ AI proposal generator with section caching and export (US-018)
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
- **Vector store** supports `inmemory` (default) or persistent `chroma` under `AI_PRESALES_VECTOR_DB_PATH`.

## Related documentation

- [Architecture](architecture.md)
- [Providers](providers.md)
- [Development guide](development.md)
