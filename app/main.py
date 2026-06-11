from fastapi import FastAPI

from app.routes import api_router

app = FastAPI(
    title="Course Service",
    description="Multi-tenant online course backend",
    version="0.1.0",
)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(api_router)
