# Development Guide

Guide for extending and running the AI Presales platform locally.

## Prerequisites

- Python 3.12
- Virtual environment
- Dependencies from `requirements.txt`

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Local development workflow

### Start the backend

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open http://localhost:8000/docs for interactive API testing.

### Start Streamlit

In a second terminal:

```bash
streamlit run ui/app.py
```

### Start both (demo script)

```bash
./scripts/run_demo.sh
```

Optional script environment variables (read by `scripts/run_demo.sh` only, not `app/core/config.py`):

| Variable | Default | Description |
| --- | --- | --- |
| `AI_PRESALES_DEMO_API_HOST` | `127.0.0.1` | Uvicorn bind host |
| `AI_PRESALES_DEMO_API_PORT` | `8000` | API port |
| `AI_PRESALES_DEMO_UI_PORT` | `8501` | Streamlit port |

## Project conventions

From `AGENTS.md`:

- Type hints on all public functions
- Pydantic models for API schemas
- Business logic in services, not routes
- AI providers behind protocols — never call OpenAI from routes
- Every feature includes tests
- Minimize scope; match existing patterns

## Configuration

Backend settings are loaded by `app/core/config.py` using Pydantic Settings:

- Prefix: `AI_PRESALES_`
- Source: environment variables and optional `.env` file
- Cached via `get_settings()` with `@lru_cache`

Streamlit UI settings (`AI_PRESALES_API_BASE_URL`, `AI_PRESALES_UI_REQUEST_TIMEOUT`) are read separately in `ui/config.py`. Demo script variables (`AI_PRESALES_DEMO_*`) are documented above under **Start both**.

After changing provider or storage settings, restart the server. Cached DI instances in `app/core/dependencies.py` also require a restart.

Tests override this behavior — see [testing.md](testing.md).

## Add a new analysis type

Analysis types in the Streamlit UI are preset prompts sent to `/ask`. No backend endpoint is required.

1. **Add a label and prompt** in `ui/prompts.py`:

```python
ANALYSIS_LABELS: tuple[str, ...] = (
    # ... existing labels ...
    "Compliance Gaps",
)

ANALYSIS_PROMPTS: dict[str, str] = {
    # ... existing prompts ...
    "Compliance Gaps": "Identify compliance gaps and missing certifications in this RFP.",
}
```

2. **Update tests** in `tests/unit/ui/test_prompts.py` for the new label and prompt.

3. **Optional:** Adjust layout in `ui/app.py` — buttons are rendered in a 3-column grid from `ANALYSIS_LABELS`.

4. **No backend changes** unless you need custom retrieval logic (then extend `AskService` or add service parameters).

The button key is generated automatically by `analysis_button_key()` in `ui/analysis_handlers.py`.

## Add a new provider

See [providers.md](providers.md) for the full checklist. Summary:

1. Implement `EmbeddingProvider` or `AnswerProvider` protocol.
2. Extend `Settings` and `AnswerProviderName` / `EmbeddingProviderName`.
3. Wire `build_*_provider()` in `app/core/dependencies.py`.
4. Update status resolution if needed (`app/schemas/status.py`).
5. Add unit and integration tests.
6. Update `.env.example` and documentation.

## Add a new API endpoint

1. Define Pydantic request/response schemas under `app/modules/documents/schemas/` or `app/schemas/`.
2. Implement business logic in a service under `app/modules/documents/services/` or `app/services/`.
3. Add a route in `app/modules/documents/api/routes.py` or `app/api/routes.py`.
4. Register DI factory in `app/core/dependencies.py` if new dependencies are needed.
5. Add integration tests under `tests/integration/api/`.
6. Document the endpoint in [api.md](api.md).

## Code layout

| Path | Responsibility |
| --- | --- |
| `app/api/routes.py` | Upload, status, demo analysis, router aggregation |
| `app/modules/documents/api/routes.py` | Document pipeline and RAG endpoints |
| `app/modules/documents/services/` | Business logic |
| `app/infrastructure/` | External integrations (storage, AI, vector store) |
| `app/core/dependencies.py` | Dependency injection |
| `ui/` | Streamlit demo (HTTP only) |

## Debugging tips

- Use `/docs` to exercise endpoints without the UI.
- Set `AI_PRESALES_DEBUG=true` for FastAPI debug output.
- Use mock providers to avoid API costs during development.
- Check `GET /api/v1/status` to confirm active providers.
- Uploaded files and metadata live under `AI_PRESALES_STORAGE_PATH` (default `uploads`).

## Related documentation

- [Architecture](architecture.md)
- [Providers](providers.md)
- [Testing](testing.md)
- [API reference](api.md)
