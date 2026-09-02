import json

from backend.app.api.problems import EmailConflictError, problem_response, validation_problem


def test_problem_response_uses_problem_json_format() -> None:
    response = problem_response(EmailConflictError())

    assert response.status_code == 409
    assert response.headers["content-type"] == "application/problem+json"
    assert json.loads(response.body) == {
        "type": "https://api.renovation-planner.local/problems/email-conflict",
        "title": "Конфликт email",
        "status": 409,
        "detail": "Этот email уже зарегистрирован.",
    }


def test_validation_problem_normalizes_fastapi_error() -> None:
    problem = validation_problem(
        [
            {
                "loc": ("query", "limit"),
                "type": "greater_than",
                "msg": "Input should be greater than 0",
            }
        ]
    )

    response = problem_response(problem)

    assert json.loads(response.body)["errors"] == [
        {
            "field": "limit",
            "code": "greater_than",
            "message": "Input should be greater than 0",
        }
    ]
