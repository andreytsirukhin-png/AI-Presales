# AI Providers

The platform isolates AI integrations behind small protocols. API routes and services never call OpenAI or OpenRouter directly.

## Provider types

| Type | Protocol | Implementations |
| --- | --- | --- |
| Embeddings | `EmbeddingProvider` | `mock`, `openai`, `ollama` |
| Answers | `AnswerProvider` | `mock`, `openai`, `openrouter` |
| Vector store | `VectorStore` | `inmemory`, `chroma` |

Protocols live in:

- `app/infrastructure/embeddings/protocol.py`
- `app/infrastructure/answers/protocol.py`
- `app/infrastructure/vector_store/protocol.py`

## In-memory vector store

**Module:** `app/infrastructure/vector_store/in_memory_store.py`

**Configuration:**

```env
AI_PRESALES_VECTOR_STORE=inmemory
```

**Behavior:**

- Stores embeddings in process memory only.
- Data is lost when the backend restarts.
- Default backend for tests and local development.

## ChromaDB vector store

**Module:** `app/infrastructure/vector_store/chroma_store.py`

**Configuration:**

```env
AI_PRESALES_VECTOR_STORE=chroma
AI_PRESALES_VECTOR_DB_PATH=./vector_store
```

**Behavior:**

- Persists embeddings under `AI_PRESALES_VECTOR_DB_PATH`.
- Uses collection name `ai-presales` with cosine similarity.
- Supports `create_collection`, `add_documents`, `search`, `delete_document`, `clear`, and `count`.
- Persists `SourceMetadata` fields on each chunk (see [architecture.md — Traceable RAG](architecture.md#traceable-rag-and-source-metadata)).
- Indexed documents remain searchable after backend restart.

Legacy env var `AI_PRESALES_VECTOR_STORE_BACKEND=memory` maps to `inmemory`.

## Mock answer provider

**Module:** `app/infrastructure/answers/mock_provider.py`

**Configuration:**

```env
AI_PRESALES_ANSWER_PROVIDER=mock
```

**Behavior:**

- Concatenates retrieved chunk text into a deterministic answer prefixed with `"Based on the indexed document:"`.
- Returns `INSUFFICIENT_CONTEXT_ANSWER` when no usable chunks are retrieved.
- Does not call external APIs.
- Ideal for local development, CI, and tests.

**Answer model reported in status API:** `"mock"`

## OpenAI answer provider

**Module:** `app/infrastructure/answers/openai_provider.py`

**Configuration:**

```env
AI_PRESALES_ANSWER_PROVIDER=openai
AI_PRESALES_OPENAI_API_KEY=your-key
AI_PRESALES_OPENAI_CHAT_MODEL=gpt-4.1-mini
AI_PRESALES_OPENAI_TEMPERATURE=0.0
AI_PRESALES_OPENAI_MAX_OUTPUT_TOKENS=800
```

**Behavior:**

- Uses the OpenAI Responses API via the official `openai` SDK.
- Builds a context-only prompt from ranked search results.
- Raises `AnswerConfigurationError` if the API key is missing at startup.
- Raises `AnswerProviderError` on API failures.

## OpenRouter answer provider

**Module:** `app/infrastructure/answers/openrouter_provider.py`

**Configuration:**

```env
AI_PRESALES_ANSWER_PROVIDER=openrouter
AI_PRESALES_OPENROUTER_API_KEY=your-key
AI_PRESALES_OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
AI_PRESALES_OPENROUTER_CHAT_MODEL=openrouter/free
AI_PRESALES_OPENAI_TEMPERATURE=0.0
AI_PRESALES_OPENAI_MAX_OUTPUT_TOKENS=800
```

**Behavior:**

- Uses the OpenAI-compatible client pointed at OpenRouter's base URL.
- Reuses OpenAI prompt construction and system instructions from `openai_provider.py`.
- Temperature and max output tokens are shared with OpenAI settings (`openai_temperature`, `openai_max_output_tokens`).
- Embeddings remain independently configurable (commonly `mock` for cost-free local demos).

## Mock embedding provider

**Module:** `app/infrastructure/embeddings/mock_provider.py`

**Configuration:**

```env
AI_PRESALES_EMBEDDING_PROVIDER=mock
AI_PRESALES_EMBEDDING_DIMENSION=16
```

**Behavior:**

- Produces deterministic pseudo-vectors from chunk text hashes.
- Default dimension is 16; must match across embed, index, and search for a document.

## OpenAI embedding provider

**Module:** `app/infrastructure/embeddings/openai_provider.py`

**Configuration:**

```env
AI_PRESALES_EMBEDDING_PROVIDER=openai
AI_PRESALES_OPENAI_API_KEY=your-key
AI_PRESALES_OPENAI_EMBEDDING_MODEL=text-embedding-3-small
AI_PRESALES_EMBEDDING_DIMENSION=1536
```

**Behavior:**

- Calls OpenAI embedding API for each chunk and search query.
- Requires a valid API key and matching embedding dimension.

## Ollama embedding provider

**Module:** `app/infrastructure/embeddings/ollama_provider.py`

**Configuration:**

```env
AI_PRESALES_EMBEDDING_PROVIDER=ollama
AI_PRESALES_EMBEDDING_DIMENSION=768
AI_PRESALES_OLLAMA_BASE_URL=http://localhost:11434
AI_PRESALES_OLLAMA_EMBEDDING_MODEL=nomic-embed-text
AI_PRESALES_OLLAMA_TIMEOUT_SECONDS=30
```

**Behavior:**

- Calls `POST /api/embed` on a local or remote Ollama server via `httpx`.
- Supports single-string and batched `input` payloads in one request.
- Skips blank texts and returns zero vectors for empty inputs (same pattern as OpenAI provider).
- Raises `EmbeddingProviderError` on HTTP or response format failures.
- Raises `InvalidEmbeddingDimensionError` when vector size does not match `AI_PRESALES_EMBEDDING_DIMENSION`.
- Set `AI_PRESALES_EMBEDDING_DIMENSION` to match your Ollama model (768 for `nomic-embed-text`).

## Dependency injection

Provider selection is centralized in `app/core/dependencies.py`.

```text
Settings (env vars)
    ↓
build_embedding_provider() / build_answer_provider()
    ↓
@lru_cache cached instances
    ↓
get_embedding_provider() / get_answer_provider()
    ↓
EmbeddingService / AskService
```

Factory functions:

| Function | Selects |
| --- | --- |
| `build_embedding_provider()` | `MockEmbeddingProvider`, `OpenAIEmbeddingProvider`, or `OllamaEmbeddingProvider` |
| `build_vector_store()` | `InMemoryVectorStore` or `ChromaVectorStore` |
| `build_answer_provider()` | `MockAnswerProvider`, `OpenAIAnswerProvider`, or `OpenRouterAnswerProvider` |

FastAPI injects providers into services through `Depends(get_embedding_provider)` and `Depends(get_answer_provider)`.

**Important:** Cached providers are created at first use. Restart Uvicorn after changing provider environment variables.

## Configuration reference

All variables below are backend settings in `app/core/config.py` (prefix `AI_PRESALES_`).

| Variable | Used by |
| --- | --- |
| `AI_PRESALES_EMBEDDING_PROVIDER` | Embedding factory |
| `AI_PRESALES_EMBEDDING_DIMENSION` | Mock/OpenAI embedding dimension |
| `AI_PRESALES_OPENAI_API_KEY` | OpenAI embeddings and answers |
| `AI_PRESALES_OPENAI_EMBEDDING_MODEL` | OpenAI embeddings |
| `AI_PRESALES_OLLAMA_BASE_URL` | Ollama embeddings |
| `AI_PRESALES_OLLAMA_EMBEDDING_MODEL` | Ollama embeddings |
| `AI_PRESALES_OLLAMA_TIMEOUT_SECONDS` | Ollama embeddings |
| `AI_PRESALES_VECTOR_STORE` | Vector store factory |
| `AI_PRESALES_VECTOR_DB_PATH` | Chroma persistence path |
| `AI_PRESALES_ANSWER_PROVIDER` | Answer factory |
| `AI_PRESALES_OPENAI_CHAT_MODEL` | OpenAI answers; status API |
| `AI_PRESALES_OPENAI_TEMPERATURE` | OpenAI and OpenRouter answers |
| `AI_PRESALES_OPENAI_MAX_OUTPUT_TOKENS` | OpenAI and OpenRouter answers |
| `AI_PRESALES_OPENROUTER_API_KEY` | OpenRouter answers |
| `AI_PRESALES_OPENROUTER_BASE_URL` | OpenRouter client base URL |
| `AI_PRESALES_OPENROUTER_CHAT_MODEL` | OpenRouter answers; status API |

The status API resolves `answer_model` from the active answer provider via `app/schemas/status.py`.

## How to add a new answer provider

1. **Implement the protocol** — Create `app/infrastructure/answers/my_provider.py` with a class implementing `generate_answer(question, context_chunks) -> str`.

2. **Export it** — Add the class to `app/infrastructure/answers/__init__.py`.

3. **Extend settings** — Add the provider name to `AnswerProviderName` in `app/core/config.py` and any new env vars.

4. **Wire DI** — Add a branch in `build_answer_provider()` in `app/core/dependencies.py`.

5. **Update status resolution** — Extend `resolve_answer_model()` in `app/schemas/status.py` if the provider has a model id.

6. **Add tests** — Unit tests for the provider and dependency wiring; integration test for `/ask` if applicable.

7. **Document** — Update this file, `.env.example`, and `README.md`.

Example protocol:

```python
class AnswerProvider(Protocol):
    def generate_answer(
        self,
        question: str,
        context_chunks: list[SearchResult],
    ) -> str: ...
```

Inject a fake client in tests the same way `OpenRouterAnswerProvider` accepts an optional `client` parameter.

## How to add a new embedding provider

Follow the same pattern using `EmbeddingProvider` in `app/infrastructure/embeddings/protocol.py` and `build_embedding_provider()`.

## Testing providers

| Test area | Location |
| --- | --- |
| Mock answer | `tests/unit/infrastructure/test_mock_answer_provider.py` |
| OpenAI answer | `tests/unit/infrastructure/test_openai_answer_provider.py` |
| OpenRouter answer | `tests/unit/infrastructure/test_openrouter_answer_provider.py` |
| Mock embedding | `tests/unit/infrastructure/test_mock_embedding_provider.py` |
| OpenAI embedding | `tests/unit/infrastructure/test_openai_embedding_provider.py` |
| Ollama embedding | `tests/unit/infrastructure/test_ollama_embedding_provider.py` |
| In-memory vector store | `tests/unit/infrastructure/test_in_memory_vector_store.py` |
| Chroma vector store | `tests/unit/infrastructure/test_chroma_vector_store.py` |
| Vector store DI | `tests/unit/core/test_vector_store_dependencies.py` |
| DI wiring | `tests/unit/core/test_answer_dependencies.py` |
| Chroma persistence | `tests/integration/infrastructure/test_chroma_persistence.py` |

Tests isolate environment variables through `tests/conftest.py` (see [testing.md](testing.md)).

## Related documentation

- [Architecture](architecture.md)
- [API — status endpoint](api.md#get-apiv1status)
- [Development guide](development.md)
