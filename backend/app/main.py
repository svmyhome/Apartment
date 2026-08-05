from fastapi import FastAPI

from backend.app.core.config import settings

app = FastAPI()

@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok"}