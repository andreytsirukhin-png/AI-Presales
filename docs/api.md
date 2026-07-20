# API Reference

Base URL: `http://localhost:8000`

Interactive documentation: http://localhost:8000/docs

All document endpoints are prefixed with `/api/v1`.

---

## GET /health

**Purpose:** Liveness check for load balancers and the Streamlit sidebar.

**Request:** No body.

**Response:** `200 OK`

```json
{
  "status": "ok"
}
```

**Example:**

```bash
curl -s http://localhost:8000/health
```

**Errors:** None expected for a running server.

---

## GET /api/v1/status

**Purpose:** Return runtime provider configuration for clients and the demo UI.

**Request:** No body.

**Response:** `200 OK` — `PlatformStatusResponse`

| Field | Type | Description |
| --- | --- | --- |
| `status` | string | Always `"ok"` when the endpoint succeeds |
| `embedding_provider` | string | Active embedding provider (`mock`, `openai`, `ollama`) |
| `answer_provider` | string | Active answer provider (`mock`, `openai`, `openrouter`) |
| `answer_model` | string | Model id for the active answer provider |
| `vector_store` | string | Active vector store (`inmemory`, `chroma`) |
| `app_environment` | string | Value of `AI_PRESALES_APP_ENVIRONMENT` |

**Example:**

```bash
curl -s http://localhost:8000/api/v1/status
```

```json
{
  "status": "ok",
  "embedding_provider": "mock",
  "answer_provider": "openrouter",
  "answer_model": "openrouter/free",
  "vector_store": "inmemory",
  "app_environment": "development"
}
```

**Errors:** None expected for a running server.

---

## POST /api/v1/documents/upload

**Purpose:** Upload a PDF document and receive a document identifier for subsequent pipeline steps.

**Request:** `multipart/form-data`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `file` | file | Yes | PDF file (max 25 MB) |

**Response:** `200 OK` — `UploadResponse`

| Field | Type | Description |
| --- | --- | --- |
| `document_id` | string | UUID for the uploaded document |
| `filename` | string | Original filename |
| `status` | string | `"uploaded"` |

**Example:**

```bash
curl -s -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@sample-rfp.pdf"
```

```json
{
  "document_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "filename": "sample-rfp.pdf",
  "status": "uploaded"
}
```

**Errors:**

| Status | Condition |
| --- | --- |
| `415` | Not a PDF (wrong extension or missing `%PDF` magic bytes) |
| `413` | File exceeds 25 MB |

---

## GET /api/v1/documents/{document_id}

**Purpose:** Retrieve stored metadata for a previously uploaded document.

**Request:** Path parameter `document_id`.

**Response:** `200 OK` — `DocumentMetadata`

| Field | Type | Description |
| --- | --- | --- |
| `document_id` | string | Document identifier |
| `filename` | string | Original filename |
| `content_type` | string | MIME type from upload |
| `size_bytes` | integer | File size in bytes |
| `status` | string | `uploaded`, `parsed`, or `failed` |
| `page_count` | integer \| null | Pages after parsing |
| `characters` | integer \| null | Extracted character count |
| `created_at` | datetime | UTC upload timestamp |

**Example:**

```bash
curl -s http://localhost:8000/api/v1/documents/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**Errors:**

| Status | Condition |
| --- | --- |
| `404` | Document not found |

---

## POST /api/v1/documents/{document_id}/parse

**Purpose:** Extract plain text from an uploaded PDF.

**Request:** Path parameter `document_id`. No body.

**Response:** `200 OK` — `ParseResponse`

| Field | Type | Description |
| --- | --- | --- |
| `document_id` | string | Document identifier |
| `page_count` | integer | Number of PDF pages |
| `pages` | integer | Alias for `page_count` |
| `characters` | integer | Length of extracted text |
| `text` | string | Full extracted plain text |
| `status` | string | Parse lifecycle status |

**Example:**

```bash
curl -s -X POST http://localhost:8000/api/v1/documents/{document_id}/parse
```

**Errors:**

| Status | Condition |
| --- | --- |
| `404` | Document not found |
| `422` | Invalid or empty PDF |

---

## POST /api/v1/documents/{document_id}/chunks

**Purpose:** Split parsed text into ordered chunks for embedding.

**Request:** Path parameter `document_id`. No body.

**Response:** `200 OK` — `ChunkResponse`

| Field | Type | Description |
| --- | --- | --- |
| `document_id` | string | Document identifier |
| `chunk_count` | integer | Number of chunks |
| `chunks` | array | List of `{ index, text, characters }` |

**Example:**

```bash
curl -s -X POST http://localhost:8000/api/v1/documents/{document_id}/chunks
```

**Errors:**

| Status | Condition |
| --- | --- |
| `404` | Document not found |
| `422` | Invalid or empty PDF |

---

## POST /api/v1/documents/{document_id}/embeddings

**Purpose:** Generate embedding vectors for all document chunks.

**Request:** Path parameter `document_id`. No body.

**Response:** `200 OK` — `EmbeddingResponse`

| Field | Type | Description |
| --- | --- | --- |
| `document_id` | string | Document identifier |
| `chunk_count` | integer | Number of embedded chunks |
| `embedding_dimension` | integer | Vector size |
| `status` | string | Embedding lifecycle status |

**Example:**

```bash
curl -s -X POST http://localhost:8000/api/v1/documents/{document_id}/embeddings
```

**Errors:**

| Status | Condition |
| --- | --- |
| `404` | Document not found |
| `422` | Invalid PDF, empty content, or embedding provider failure |

---

## POST /api/v1/documents/{document_id}/index

**Purpose:** Store chunk embeddings in the vector store for semantic search.

**Request:** Path parameter `document_id`. No body.

**Response:** `200 OK` — `IndexResponse`

| Field | Type | Description |
| --- | --- | --- |
| `document_id` | string | Document identifier |
| `chunks_indexed` | integer | Chunks stored in the vector store |
| `status` | string | Indexing lifecycle status |

**Example:**

```bash
curl -s -X POST http://localhost:8000/api/v1/documents/{document_id}/index
```

**Errors:**

| Status | Condition |
| --- | --- |
| `404` | Document not found |
| `422` | Invalid PDF, empty content, or embedding error |

---

## POST /api/v1/documents/{document_id}/search

**Purpose:** Run semantic search over indexed chunks within one document.

**Request:** JSON body — `SearchRequest`

| Field | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `query` | string | Yes | — | Natural-language search query (min length 1) |
| `top_k` | integer | No | `5` | Max results (1–50) |

**Response:** `200 OK` — `SearchResponse`

| Field | Type | Description |
| --- | --- | --- |
| `document_id` | string | Document identifier |
| `query` | string | Submitted query |
| `result_count` | integer | Number of results returned |
| `results` | array | `{ chunk_index, text, score, metadata? }` ranked by similarity |

Each result may include `metadata` (`SourceMetadata`): `document_id`, `document_name`, `page_number`, `chunk_id`, `chunk_index`, `embedding_model`, `created_at`, and optional `section` / `heading`.

**Example:**

```bash
curl -s -X POST http://localhost:8000/api/v1/documents/{document_id}/search \
  -H "Content-Type: application/json" \
  -d '{"query": "integration requirements", "top_k": 5}'
```

**Errors:**

| Status | Condition |
| --- | --- |
| `404` | Document not indexed |
| `422` | Validation error, dimension mismatch, or embedding failure |

---

## POST /api/v1/documents/{document_id}/ask

**Purpose:** Answer a natural-language question using RAG over indexed chunks. Also used by the Streamlit analysis dashboard with preset prompts.

**Request:** JSON body — `AskRequest`

| Field | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `question` | string | Yes | — | Question or analysis prompt (min length 1) |
| `top_k` | integer | No | `5` | Context chunks to retrieve (1–50) |

**Response:** `200 OK` — `AskResponse`

| Field | Type | Description |
| --- | --- | --- |
| `document_id` | string | Document identifier |
| `question` | string | Submitted question |
| `answer` | string | Generated answer |
| `sources` | array | `{ chunk_index, text, score, metadata? }` supporting chunks |
| `citations` | array | `{ document, page, score, chunk_index?, chunk_id? }` compact references |
| `status` | string | `"answered"` |

Existing clients can keep using `chunk_index`, `text`, and `score` on `sources`. New clients should prefer `citations` for UI source lists and `metadata` on search/ask sources for traceability.

**Example:**

```bash
curl -s -X POST http://localhost:8000/api/v1/documents/{document_id}/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the main delivery risks?", "top_k": 10}'
```

**Errors:**

| Status | Condition |
| --- | --- |
| `404` | Document not indexed |
| `422` | Validation error, embedding failure, or answer provider error |

---

## POST /api/v1/analysis/demo

**Purpose:** Return a static structured analysis payload for early API demos. This endpoint does **not** run the RAG pipeline and is not used by the Streamlit UI.

**Request:** No body.

**Response:** `200 OK` — `AnalysisResult`

Structured fields include `document_summary`, `requirements`, `clarification_questions`, `risks`, `assumptions`, and `confidence`.

**Example:**

```bash
curl -s -X POST http://localhost:8000/api/v1/analysis/demo
```

**Errors:** None expected for a running server.

---

## Error response format

FastAPI returns errors as:

```json
{
  "detail": "Human-readable error message"
}
```

Validation errors may return a list of objects with `loc`, `msg`, and `type` fields.

## Endpoint summary

| Method | Path | Tag |
| --- | --- | --- |
| GET | `/health` | system |
| GET | `/api/v1/status` | system |
| POST | `/api/v1/documents/upload` | documents |
| GET | `/api/v1/documents/{document_id}` | documents |
| POST | `/api/v1/documents/{document_id}/parse` | documents |
| POST | `/api/v1/documents/{document_id}/chunks` | documents |
| POST | `/api/v1/documents/{document_id}/embeddings` | documents |
| POST | `/api/v1/documents/{document_id}/index` | documents |
| POST | `/api/v1/documents/{document_id}/search` | documents |
| POST | `/api/v1/documents/{document_id}/ask` | documents |
| POST | `/api/v1/analysis/demo` | analysis |
