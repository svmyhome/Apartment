from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.problems import (
    ProblemError,
    UnauthorizedError,
    problem_response,
    validation_problem,
)
from backend.app.api.router import api_router
from backend.app.core.config import get_cors_allowed_origins
from backend.app.db.health import DatabaseUnavailableError

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.exception_handler(DatabaseUnavailableError)
def database_unavailable_handler(request: Request, exc: DatabaseUnavailableError) -> JSONResponse:
    return JSONResponse(status_code=503, content={"status": "database_unavailable"})


@app.exception_handler(ProblemError)
def problem_error_handler(request: Request, exc: ProblemError) -> JSONResponse:
    return problem_response(exc)


@app.exception_handler(UnauthorizedError)
def unauthorized_error_handler(request: Request, exc: UnauthorizedError) -> JSONResponse:
    return problem_response(exc, headers={"WWW-Authenticate": "Bearer"})


@app.exception_handler(RequestValidationError)
def request_validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return problem_response(validation_problem(exc.errors()))


app.include_router(api_router)
