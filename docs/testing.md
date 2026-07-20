# Testing

The project uses **pytest** with **278 tests** covering unit and integration layers.

## Quick start

From the repository root:

```bash
python -m pytest -q
```

Explicit module path (equivalent when run from root):

```bash
PYTHONPATH=. python -m pytest -q
```

Verbose output with test names:

```bash
python -m pytest -v
```

Run a single file:

```bash
python -m pytest tests/integration/api/test_ask_api.py -v
```

Run tests matching a keyword:

```bash
python -m pytest -k "openrouter" -v
```

## Test layout

```text
tests/
├── conftest.py                 # Global fixtures (env isolation)
├── helpers/                    # Shared test utilities (PDF helpers)
├── unit/
│   ├── core/                   # Config, DI, status
│   ├── infrastructure/         # Providers, vector store, storage
│   ├── modules/documents/      # Services, parsers, chunkers
│   └── ui/                     # Streamlit client, prompts, handlers
├── integration/
│   └── api/                    # HTTP API tests via TestClient
├── test_demo.py
├── test_upload_api.py
└── test_upload_service.py
```

## Unit tests

Unit tests exercise services, providers, and UI helpers in isolation.

| Area | Examples |
| --- | --- |
| Config | `tests/unit/core/test_config.py` |
| DI wiring | `tests/unit/core/test_answer_dependencies.py` |
| Mock/OpenAI/OpenRouter providers | `tests/unit/infrastructure/test_*_provider.py` |
| Document services | `tests/unit/modules/documents/test_ask_service.py`, `test_citations.py`, `test_text_chunker_pages.py` |
| Answer prompts / citations | `tests/unit/infrastructure/test_answer_prompts.py`, `test_chroma_metadata.py`, `test_chroma_metadata_persistence.py` |
| UI client | `tests/unit/ui/test_api_client.py` |
| Analysis handlers | `tests/unit/ui/test_analysis_handlers.py` |

Providers accept injected clients in tests to avoid network calls.

## Integration tests

Integration tests use FastAPI's `TestClient` with overridden dependencies where needed.

| Endpoint area | Test file |
| --- | --- |
| Upload | `tests/test_upload_api.py` |
| Parse | `tests/integration/api/test_parse_api.py` |
| Chunks | `tests/integration/api/test_chunks_api.py` |
| Embeddings | `tests/integration/api/test_embeddings_api.py` |
| Index | `tests/integration/api/test_index_api.py` |
| Search | `tests/integration/api/test_search_api.py` |
| Projects / proposal / review | `tests/integration/api/test_projects_api.py`, `test_proposal_api.py`, `test_review_api.py` |
| Proposal / review unit | `tests/unit/modules/projects/test_proposal_service.py`, `test_proposal_export.py`, `test_review_parser.py`, `test_review_metrics.py`, `test_review_export.py` |
| Ask / RAG | `tests/integration/api/test_ask_api.py` |
| Status | `tests/integration/api/test_status_api.py` |
| OpenAI providers | `tests/integration/api/test_openai_*_api.py` |

Typical pattern: upload a test PDF, run the pipeline, assert on response schemas and status codes.

## Environment isolation

`tests/conftest.py` applies an autouse fixture that:

1. Removes all `AI_PRESALES_*` environment variables before each test.
2. Sets `Settings.model_config` to `env_file=None` so repo `.env` is not loaded.
3. Clears settings and dependency caches before and after each test.

This ensures tests pass regardless of developer `.env` settings (for example `AI_PRESALES_ANSWER_PROVIDER=openrouter` or custom storage paths).

Tests that need specific env values should set them explicitly with `monkeypatch.setenv()` or construct `Settings(_env_file=...)` directly.

## Current coverage

The suite covers:

- Full document pipeline (upload through index)
- Semantic search and ask/RAG flows (including `metadata` on search results and `citations` on ask responses)
- All three answer providers (mock, OpenAI, OpenRouter)
- Vector store backends (in-memory and ChromaDB)
- Platform status API
- Streamlit HTTP client and analysis handlers
- Upload validation (type, size, magic bytes)

Coverage is measured by breadth of behavioral tests rather than a enforced percentage gate. Run with coverage plugin if installed:

```bash
python -m pytest --cov=app --cov=ui --cov-report=term-missing
```

*(pytest-cov is not listed in `requirements.txt`; install separately if needed.)*

## Writing new tests

1. Place unit tests under `tests/unit/` mirroring the source module path.
2. Place API tests under `tests/integration/api/`.
3. Use `tests/helpers/pdf.py` for minimal valid PDF fixtures.
4. Do not rely on repo `.env` — set env vars in the test or use dependency overrides.
5. Call `clear_dependency_caches()` when mutating settings mid-test (handled by conftest for most cases).

## CI note

Automated CI/CD is not yet configured. Run tests locally before opening pull requests.

## Related documentation

- [Development guide](development.md)
- [Providers — testing section](providers.md#testing-providers)
