from fastapi import APIRouter

api_router = APIRouter(prefix="/api/v1")

from backend.app.api import health  # noqa: E402, F401
