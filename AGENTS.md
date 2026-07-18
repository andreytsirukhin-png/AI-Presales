# AI Presales Platform

## Mission

Build an enterprise-grade AI platform for presales automation.

## Tech Stack

- Python 3.12
- FastAPI
- Pydantic v2
- SQLAlchemy
- PostgreSQL
- Docker
- OpenAI Responses API

## Coding Rules

- Always use type hints.
- Use Pydantic models.
- Keep business logic out of API routes.
- Write production-quality code.
- Avoid duplication.
- Follow SOLID principles.
- Every public function should have a docstring.
- Every feature must include tests.
- Never modify unrelated code.
- Prefer readability over cleverness.

## Architecture

API

↓

Services

↓

Domain

↓

Repository

↓

Database

AI providers must be isolated behind interfaces.

Never call OpenAI directly from API routes.

## Testing

Every feature must include unit tests.

## Style

Think like a Senior Staff Engineer.

Explain architectural decisions before writing code.