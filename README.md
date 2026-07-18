# AI RFP Analyzer

Enterprise-oriented MVP for analyzing RFP, SOW, BRD and related presales documents.

## MVP flow

1. Upload PDF, DOCX or TXT.
2. Extract and normalize document text.
3. Identify:
   - functional requirements;
   - non-functional requirements;
   - integrations;
   - constraints;
   - deliverables;
   - deadlines and commercial conditions.
4. Detect:
   - ambiguities;
   - contradictions;
   - missing information;
   - dependencies.
5. Generate:
   - clarification questions;
   - risks;
   - assumptions;
   - preliminary scope summary.
6. Review and approve results.
7. Export structured JSON. DOCX/XLSX export is planned for the next iteration.

## Architecture

- Python 3.12
- FastAPI
- Pydantic
- OpenAI Responses API
- Local filesystem for the first iteration
- PostgreSQL + pgvector in a later iteration

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Open API documentation at:

```text
http://127.0.0.1:8000/docs
```

## Initial endpoints

- `GET /health`
- `POST /api/v1/documents/upload`
- `POST /api/v1/analysis/demo`

`analysis/demo` currently returns a deterministic sample response. The next implementation step is connecting extraction and the LLM analysis service.

## Definition of Done for MVP

- Supports PDF, DOCX and TXT.
- Produces structured, editable analysis.
- Every finding includes evidence from the source document.
- Questions are grouped by business, functional, architecture, integration, security, data, delivery and commercial categories.
- A human can accept, reject or edit each finding.
- Analysis can be exported.
