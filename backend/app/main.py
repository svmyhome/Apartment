from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse

from backend.app.db.health import DatabaseUnavailableError, check_database

app = FastAPI()


@app.exception_handler(DatabaseUnavailableError)
def database_unavailable_handler(request: Request, exc: DatabaseUnavailableError) -> JSONResponse:
    return JSONResponse(status_code=503, content={"status": "database_unavailable"})


@app.get("/api/v1/health")
def health(_: None = Depends(check_database)) -> dict[str, str]:
    return {"status": "ok"}
