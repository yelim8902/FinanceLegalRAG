from fastapi import FastAPI

from app.api.routes import router


app = FastAPI(
    title="Financial Regulation Compliance Monitoring Agent",
    description="Monitors official financial regulation sources and checks fintech compliance impact.",
    version="0.1.0",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(router)
