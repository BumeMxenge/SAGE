# Checks the contract describes itself: every operation has a summary, a camelCase id and a typed
# success response, and declares its errors as problem details
import re


def operations(client) -> dict[str, dict]:
    schema = client.get("/openapi.json").json()
    return {
        f"{method.upper()} {path}": operation
        for path, methods in schema["paths"].items()
        for method, operation in methods.items()
    }


def test_every_operation_has_a_summary_and_a_readable_id(client):
    for name, operation in operations(client).items():
        assert operation["summary"], name
        assert re.fullmatch(r"[a-z]+(?:[A-Z][a-z]*)*", operation["operationId"]), name


def test_every_success_is_typed_and_every_error_is_a_problem(client):
    for name, operation in operations(client).items():
        for status, response in operation["responses"].items():
            if int(status) >= 400:
                assert response["content"] == {
                    "application/problem+json": {
                        "schema": {"$ref": "#/components/schemas/Problem"}
                    }
                }, name
            elif status != "204":
                assert response["content"]["application/json"]["schema"], name
