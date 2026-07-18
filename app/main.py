from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(
    title="AI RFP Analyzer",
    version="0.1.0",
    description="Structured analysis of RFP and presales documents.",
)

app.include_router(router)


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
