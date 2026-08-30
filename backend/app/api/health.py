from fastapi import Depends

from backend.app.api.router import api_router
from backend.app.db.health import check_database


@api_router.get("/health")
def health(_: None = Depends(check_database)) -> dict[str, str]:
    return {"status": "ok"}
