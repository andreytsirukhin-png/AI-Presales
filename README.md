# AI RFP Analyzer

Locally runnable AI presales demo for analyzing RFP PDFs using a FastAPI backend and Streamlit UI.

## Current capabilities

- PDF upload, parsing, chunking, embeddings, and indexing
- Semantic search and question answering over indexed documents
- Mock, OpenAI, and OpenRouter embedding/answer providers
- Streamlit demo UI that calls the backend over HTTP only

## Architecture

```text
Streamlit UI (ui/app.py)
    ↓ HTTP
FastAPI API (app/main.py)
    ↓
Application services
    ↓
Search / Answer providers
```

The backend and UI are independently runnable. Streamlit does not import backend services.

## Prerequisites

- Python 3.12
- A virtual environment

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Configuration

Backend settings use the `AI_PRESALES_` prefix. For the demo UI, set:

```env
AI_PRESALES_API_BASE_URL=http://localhost:8000
```

Mock mode works without an OpenAI key:

```env
AI_PRESALES_EMBEDDING_PROVIDER=mock
AI_PRESALES_ANSWER_PROVIDER=mock
AI_PRESALES_EMBEDDING_DIMENSION=16
```

For OpenAI mode:

```env
AI_PRESALES_EMBEDDING_PROVIDER=openai
AI_PRESALES_ANSWER_PROVIDER=openai
AI_PRESALES_OPENAI_API_KEY=your-key
AI_PRESALES_OPENAI_EMBEDDING_MODEL=text-embedding-3-small
AI_PRESALES_EMBEDDING_DIMENSION=1536
AI_PRESALES_OPENAI_CHAT_MODEL=gpt-4.1-mini
```

For OpenRouter answer generation (embeddings remain independently configurable):

```env
AI_PRESALES_ANSWER_PROVIDER=openrouter
AI_PRESALES_OPENROUTER_API_KEY=your-key
AI_PRESALES_OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
AI_PRESALES_OPENROUTER_CHAT_MODEL=openrouter/free
AI_PRESALES_OPENAI_TEMPERATURE=0.0
AI_PRESALES_OPENAI_MAX_OUTPUT_TOKENS=800
```

Example mixed setup with mock embeddings and OpenRouter answers:

```env
AI_PRESALES_EMBEDDING_PROVIDER=mock
AI_PRESALES_EMBEDDING_DIMENSION=16
AI_PRESALES_ANSWER_PROVIDER=openrouter
AI_PRESALES_OPENROUTER_API_KEY=your-key
AI_PRESALES_OPENROUTER_CHAT_MODEL=openrouter/free
```

## Demo

### Start the application

Terminal 1:

```bash
uvicorn app.main:app --reload
```

Terminal 2:

```bash
streamlit run ui/app.py
```

- API: `http://localhost:8000`
- UI: `http://localhost:8501`
- API docs: `http://localhost:8000/docs`

### Use the demo

1. Open Streamlit at `http://localhost:8501`.
2. Upload an RFP PDF.
3. Click **Process Document** to run upload, parse, chunk, embeddings, and index.
4. Click analysis buttons such as **Executive Summary**, **Requirements**, or **Risks**.
5. Each analysis sends a specialized prompt to the existing `/ask` endpoint.
6. Use **Ask the RFP** for custom questions.
7. Expand source chunks to inspect retrieved evidence.

### Example walkthrough

1. Start backend and Streamlit.
2. Upload an RFP PDF and process it.
3. Run **Executive Summary**.
4. Run **Clarification Questions**.
5. Run **Risks**.
6. Ask “What integrations are required?”
7. Review answer sources.

## Main API endpoints

- `GET /health`
- `POST /api/v1/documents/upload`
- `POST /api/v1/documents/{document_id}/parse`
- `POST /api/v1/documents/{document_id}/chunks`
- `POST /api/v1/documents/{document_id}/embeddings`
- `POST /api/v1/documents/{document_id}/index`
- `POST /api/v1/documents/{document_id}/search`
- `POST /api/v1/documents/{document_id}/ask`
- `POST /api/v1/analysis/demo`

## Testing

```bash
python -m pytest -q
```

## Limitations

- PDF upload only in the demo UI
- In-memory vector store
- No authentication or streaming
- Mock mode returns deterministic summaries rather than full LLM-quality analyses
