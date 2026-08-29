from collections.abc import Sequence
from typing import Any

from fastapi.responses import JSONResponse

PROBLEM_TYPE_BASE_URL = "https://api.renovation-planner.local/problems"


class ProblemError(Exception):
    """Ошибка предметной области, которую приложение отдаёт в RFC 9457-формате."""

    def __init__(
        self,
        *,
        type_name: str,
        title: str,
        status: int,
        detail: str,
        errors: Sequence[dict[str, Any]] | None = None,
    ) -> None:
        self.type_name = type_name
        self.title = title
        self.status = status
        self.detail = detail
        self.errors = list(errors) if errors else None


class EmailConflictError(ProblemError):
    def __init__(self) -> None:
        super().__init__(
            type_name="email-conflict",
            title="Конфликт email",
            status=409,
            detail="Этот email уже зарегистрирован.",
        )


class ResourceNotFoundError(ProblemError):
    def __init__(self) -> None:
        super().__init__(
            type_name="resource-not-found",
            title="Ресурс не найден",
            status=404,
            detail="Запрошенный ресурс не найден.",
        )


def problem_response(
    problem: ProblemError, *, headers: dict[str, str] | None = None
) -> JSONResponse:
    """Строит ответ application/problem+json, общий для всех API-ошибок."""
    content: dict[str, Any] = {
        "type": f"{PROBLEM_TYPE_BASE_URL}/{problem.type_name}",
        "title": problem.title,
        "status": problem.status,
        "detail": problem.detail,
    }
    if problem.errors:
        content["errors"] = problem.errors

    return JSONResponse(
        status_code=problem.status,
        content=content,
        media_type="application/problem+json",
        headers=headers,
    )


def validation_problem(errors: Sequence[dict[str, Any]]) -> ProblemError:
    """Преобразует ошибки FastAPI/Pydantic в стабильный внешний контракт."""
    normalized_errors: list[dict[str, Any]] = []
    for error in errors:
        location = error.get("loc", ())
        field = ".".join(str(item) for item in location if item not in {"body", "query", "path"})
        normalized_errors.append(
            {
                "field": field,
                "code": str(error["type"]),
                "message": str(error["msg"]),
            }
        )

    return ProblemError(
        type_name="validation-error",
        title="Ошибка валидации",
        status=422,
        detail="Проверьте переданные поля.",
        errors=normalized_errors,
    )
