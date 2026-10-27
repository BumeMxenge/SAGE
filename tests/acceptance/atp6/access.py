# ATP-6's access sweep, run against the live deployment. For every /v1 route it sends the request
# as the owner, as another student using the owner's ids, as staff, signed out, with a forged token
# and with an expired one, and checks each outcome against the expectation written down here before
# the run. The owner's claim is only that she is never wrongly turned away (reachable); the other
# five visitors have exact expectations, as that is where a breach would show. Then, with the
# owner's token and the publishable key, it tries another student's rows in every table straight
# through PostgREST. Then it uploads one made-up transcript as a third account and lists the storage
# buckets, to confirm nothing was stored. Every attempt goes in attempts.csv. The expired-token
# sweep is a separate run, so it can wait until the owner's token is over an hour old.
from __future__ import annotations

import argparse
import json
import time
import uuid
from pathlib import Path

import httpx
import jwt
from common import (
    REPO_ROOT,
    Config,
    Tokens,
    accounts_of_role,
    number_of,
    read_csv,
    routes,
    student_tables,
    transcript_pdf,
    write_csv,
)

RESULTS = Path(__file__).resolve().parent / "results"
FIELDS = ["category", "route", "visitor", "expected", "actual", "result"]
QUESTION = "Roughly how many hours of work does one credit stand for?"
RECORD = json.loads(
    (REPO_ROOT / "data/synthetic/ziyela.json").read_text(encoding="utf-8")
)
PERMISSION_DENIED = (
    "42501"  # PostgREST's code for a row the grant or the policy refuses
)
# The codes that mean a visitor was turned away, so the owner is "reachable" only if she meets none
BLOCKED = {
    "not_signed_in",
    "uct_account_required",
    "students_only",
    "plan_not_found",
    "chat_not_found",
}

# The routes that name one student's own plans or chats: another student calling them with the
# owner's ids is turned away, exactly as backend/tests/unit/shared/api/test_guards.py asserts.
NOT_HERS = {
    "GET /v1/plans/{plan_id}": (404, "plan_not_found"),
    "GET /v1/plans/{plan_id}/previews/{course_code}": (404, "plan_not_found"),
    "GET /v1/plans/compare": (404, "plan_not_found"),
    "GET /v1/chats": (200, "[]"),
    "POST /v1/chats": (404, "plan_not_found"),
    "GET /v1/chats/{chat_id}/messages": (404, "chat_not_found"),
    "POST /v1/chats/{chat_id}/messages": (404, "chat_not_found"),
}
REACHABLE = "reachable"


def expected_text(outcome) -> str:
    if outcome == REACHABLE:
        return "reachable (not blocked)"
    status, marker = outcome
    return f"{status} {marker}" if marker else str(status)


def forged_token() -> str:
    # A well-formed token signed with a key that is not the project's, so the signature check fails
    claims = {
        "sub": str(uuid.uuid4()),
        "aud": "authenticated",
        "role": "authenticated",
        "email": "forged999@myuct.ac.za",
        "app_metadata": {"provider": "email"},
        "exp": int(time.time()) + 3600,
    }
    return jwt.encode(
        claims, "a-made-up-signing-key-not-the-projects-32plus", algorithm="HS256"
    )


def onboard(client: httpx.Client, token: str) -> None:
    # A and B end onboarded and past the questionnaire, so their chat routes work and the sweep sees
    # the ready state the seeded student in test_guards.py has. Idempotent: the same calls twice
    # leave the same state.
    headers = {"Authorization": f"Bearer {token}"}
    if not client.get("/v1/me", headers=headers).json().get("onboarding_complete"):
        client.post(
            "/v1/onboarding/complete",
            headers=headers,
            json={
                "curriculum_code": RECORD["students"][0]["curriculum_code"],
                "lines": RECORD["course_history"],
            },
        )
    if client.get("/v1/questionnaire", headers=headers).json().get("needed"):
        client.post(
            "/v1/questionnaire", headers=headers, json={"week": "no_preference"}
        )


def owner_ids(client: httpx.Client, token: str) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {token}"}
    plans = client.get("/v1/plans", headers=headers).json()["plans"]
    chat = client.post(
        "/v1/chats", headers=headers, json={"plan_id": plans[0]["id"]}
    ).json()
    return {
        "plan": plans[0]["id"],
        "plan2": plans[1]["id"],
        "chat": chat["id"],
        "course": "SLL1002S",
    }


def route_specs(ids: dict[str, str], pdf: bytes) -> dict[str, dict]:
    # One concrete request per route, with the owner's ids and the body a real call sends. overrides
    # pins a visitor's expectation where it is not the default (another student can't claim a
    # transcript that names a different number).
    def spec(method, path, **kw):
        overrides = kw.pop("overrides", {})
        return {"method": method, "path": path, "overrides": overrides, "kw": kw}

    pdf_headers = {"Content-Type": "application/pdf"}
    body = {
        "curriculum_code": RECORD["students"][0]["curriculum_code"],
        "lines": RECORD["course_history"],
    }
    return {
        "GET /v1/me": spec("GET", "/v1/me"),
        "GET /v1/catalogue": spec("GET", "/v1/catalogue"),
        "POST /v1/onboarding/transcript": spec(
            "POST",
            "/v1/onboarding/transcript",
            content=pdf,
            headers=pdf_headers,
            overrides={"other": (422, "transcript_not_yours")},
        ),
        "POST /v1/onboarding/complete": spec(
            "POST", "/v1/onboarding/complete", json=body
        ),
        "GET /v1/plans": spec("GET", "/v1/plans"),
        "GET /v1/plans/compare": spec(
            "GET",
            "/v1/plans/compare",
            params={"first": ids["plan"], "second": ids["plan2"]},
        ),
        "GET /v1/plans/{plan_id}": spec("GET", f"/v1/plans/{ids['plan']}"),
        "GET /v1/plans/{plan_id}/previews/{course_code}": spec(
            "GET", f"/v1/plans/{ids['plan']}/previews/{ids['course']}"
        ),
        "GET /v1/questionnaire": spec("GET", "/v1/questionnaire"),
        "POST /v1/questionnaire": spec(
            "POST", "/v1/questionnaire", json={"week": "no_preference"}
        ),
        "GET /v1/electives": spec("GET", "/v1/electives"),
        "PUT /v1/favourites/{course_code}": spec(
            "PUT", f"/v1/favourites/{ids['course']}"
        ),
        "DELETE /v1/favourites/{course_code}": spec(
            "DELETE", f"/v1/favourites/{ids['course']}"
        ),
        "GET /v1/history": spec("GET", "/v1/history"),
        "GET /v1/chats": spec("GET", "/v1/chats", params={"plan_id": ids["plan"]}),
        "POST /v1/chats": spec("POST", "/v1/chats", json={"plan_id": ids["plan"]}),
        "GET /v1/chats/{chat_id}/messages": spec(
            "GET", f"/v1/chats/{ids['chat']}/messages"
        ),
        "POST /v1/chats/{chat_id}/messages": spec(
            "POST", f"/v1/chats/{ids['chat']}/messages", json={"content": QUESTION}
        ),
    }


def describe(response: httpx.Response) -> tuple[int, str | None]:
    status = response.status_code
    if 200 <= status < 300:
        try:
            if response.json() == []:
                return status, "[]"
        except ValueError:
            pass
        return status, None
    try:
        return status, response.json().get("code")
    except ValueError:
        return status, None


def expected_for(visitor: str, route: str, spec: dict):
    if visitor in spec["overrides"]:
        return spec["overrides"][visitor]
    if visitor == "owner":
        return REACHABLE
    if visitor in ("signed_out", "forged", "expired"):
        return (401, "not_signed_in")
    if visitor == "staff":
        return (200, None) if route == "GET /v1/me" else (403, "students_only")
    return NOT_HERS.get(route, REACHABLE)


def passes(expected, actual: tuple[int, str | None]) -> bool:
    if expected == REACHABLE:
        return actual[0] not in (401, 403) and actual[1] not in BLOCKED
    return actual == expected


def send(client: httpx.Client, spec: dict, token: str | None) -> httpx.Response:
    headers = dict(spec["kw"].get("headers", {}))
    if token:
        headers["Authorization"] = f"Bearer {token}"
    kw = {k: v for k, v in spec["kw"].items() if k != "headers"}
    return client.request(spec["method"], spec["path"], headers=headers, **kw)


def sweep_routes(
    cfg: Config, visitors: dict[str, str | None], ids: dict[str, str], pdf: bytes
):
    specs = route_specs(ids, pdf)
    served = {
        f"{method} {path}"
        for method, path in routes(cfg.api_url)
        if path.startswith("/v1")
    }
    missing = served - specs.keys()
    if missing:
        raise SystemExit(f"Routes with no expectation written down: {sorted(missing)}")
    rows = []
    with httpx.Client(base_url=cfg.api_url, timeout=60) as client:
        for route, spec in specs.items():
            for visitor, token in visitors.items():
                expected = expected_for(visitor, route, spec)
                actual = describe(send(client, spec, token))
                rows.append(
                    {
                        "category": "route",
                        "route": route,
                        "visitor": visitor,
                        "expected": expected_text(expected),
                        "actual": expected_text(actual),
                        "result": "pass" if passes(expected, actual) else "fail",
                    }
                )
    return rows


def sweep_rest(cfg: Config, a_token: str, b_id: str):
    # The owner's token and the publishable key, straight at the database, trying another student's
    # rows in every table. Row level security hides a read; the grants refuse every write.
    rest = f"{cfg.supabase_url}/rest/v1"
    headers = {"apikey": cfg.publishable_key, "Authorization": f"Bearer {a_token}"}
    rows = []
    for table in student_tables():
        column = "id" if table == "students" else "student_id"
        attempts = {
            "read": httpx.get(
                f"{rest}/{table}",
                headers=headers,
                params={column: f"eq.{b_id}", "select": "*"},
                timeout=30,
            ),
            "insert": httpx.post(
                f"{rest}/{table}", headers=headers, json={column: b_id}, timeout=30
            ),
            "update": httpx.patch(
                f"{rest}/{table}",
                headers=headers,
                params={column: f"eq.{b_id}"},
                json={column: b_id},
                timeout=30,
            ),
            "delete": httpx.request(
                "DELETE",
                f"{rest}/{table}",
                headers=headers,
                params={column: f"eq.{b_id}"},
                timeout=30,
            ),
        }
        for operation, response in attempts.items():
            expected = "200 []" if operation == "read" else f"4xx {PERMISSION_DENIED}"
            actual = _rest_outcome(response)
            rows.append(
                {
                    "category": "rest",
                    "route": f"{table}.{operation}",
                    "visitor": "other (A's token)",
                    "expected": expected,
                    "actual": actual,
                    "result": "pass" if _rest_ok(operation, actual) else "fail",
                }
            )
    return rows


def _rest_outcome(response: httpx.Response) -> str:
    if 200 <= response.status_code < 300:
        try:
            body = response.json()
        except ValueError:
            body = None
        return "200 []" if body == [] else f"{response.status_code} {body}"
    try:
        return f"{response.status_code} {response.json().get('code')}"
    except ValueError:
        return str(response.status_code)


def _rest_ok(operation: str, actual: str) -> bool:
    if operation == "read":
        return actual == "200 []"
    return PERMISSION_DENIED in actual


def sweep_storage(cfg: Config, c_token: str, c_number: str, pdf: bytes):
    # Upload one transcript as C, then list the buckets and their objects with the secret key, to
    # confirm the transcript was read in memory and nothing landed in storage
    rows = []
    with httpx.Client(base_url=cfg.api_url, timeout=60) as client:
        upload = client.post(
            "/v1/onboarding/transcript",
            headers={
                "Authorization": f"Bearer {c_token}",
                "Content-Type": "application/pdf",
            },
            content=pdf,
        )
    rows.append(
        {
            "category": "storage",
            "route": "POST /v1/onboarding/transcript (C)",
            "visitor": "C",
            "expected": "200",
            "actual": str(upload.status_code),
            "result": "pass" if upload.status_code == 200 else "fail",
        }
    )
    storage = f"{cfg.supabase_url}/storage/v1"
    admin = {"apikey": cfg.secret_key, "Authorization": f"Bearer {cfg.secret_key}"}
    buckets = httpx.post(f"{storage}/bucket/list", headers=admin, json={}, timeout=30)
    bucket_names = (
        [b["name"] for b in buckets.json()] if buckets.status_code == 200 else []
    )
    hits = []
    for name in bucket_names:
        listing = httpx.post(
            f"{storage}/object/list/{name}",
            headers=admin,
            json={"limit": 1000},
            timeout=30,
        )
        for obj in listing.json() if listing.status_code == 200 else []:
            if c_number in (obj.get("name") or ""):
                hits.append(f"{name}/{obj['name']}")
    rows.append(
        {
            "category": "storage",
            "route": "storage objects naming C's number",
            "visitor": "secret key",
            "expected": "none",
            "actual": ", ".join(hits)
            if hits
            else f"none ({len(bucket_names)} buckets)",
            "result": "pass" if not hits else "fail",
        }
    )
    return rows


def run() -> None:
    cfg = Config()
    tokens = Tokens(cfg)
    a, b, c, staff = (accounts_of_role(role)[0] for role in ("A", "B", "C", "staff"))
    with httpx.Client(base_url=cfg.api_url, timeout=60) as client:
        onboard(client, tokens.access_token(a["email"]))
        onboard(client, tokens.access_token(b["email"]))
        ids = owner_ids(client, tokens.access_token(a["email"]))
    pdf_a = transcript_pdf(number_of(a["email"]))
    pdf_c = transcript_pdf(number_of(c["email"]))
    visitors = {
        "owner": tokens.access_token(a["email"]),
        "other": tokens.access_token(b["email"]),
        "staff": tokens.access_token(staff["email"]),
        "signed_out": None,
        "forged": forged_token(),
    }
    rows = sweep_routes(cfg, visitors, ids, pdf_a)
    rows += sweep_rest(cfg, tokens.access_token(a["email"]), b["id"])
    rows += sweep_storage(
        cfg, tokens.access_token(c["email"]), number_of(c["email"]), pdf_c
    )
    write_csv(RESULTS / "attempts.csv", FIELDS, rows)
    print(f"Wrote {RESULTS / 'attempts.csv'} ({len(rows)} attempts).")


def expired() -> None:
    # The expired-token sweep, run at the end when A's step-5 token is over an hour old. If it is
    # not that old yet, every route is recorded "not run", as agreed.
    cfg = Config()
    tokens = Tokens(cfg)
    a = accounts_of_role("A")[0]
    age = time.time() - (tokens.obtained(a["email"]) or time.time())
    token = tokens.raw_access_token(a["email"])
    ids = {k: uuid.uuid4().hex for k in ("plan", "plan2", "chat")} | {
        "course": "SLL1002S"
    }
    specs = route_specs(ids, b"%PDF-")
    too_young = age < 3600
    rows = []
    with httpx.Client(base_url=cfg.api_url, timeout=60) as client:
        for route, spec in specs.items():
            expected = (401, "not_signed_in")
            if too_young:
                actual_text, result = "not run", "not run"
            else:
                actual_text = expected_text(describe(send(client, spec, token)))
                result = "pass" if actual_text == expected_text(expected) else "fail"
            rows.append(
                {
                    "category": "route",
                    "route": route,
                    "visitor": "expired",
                    "expected": expected_text(expected),
                    "actual": actual_text,
                    "result": result,
                }
            )
    existing = RESULTS / "attempts.csv"
    prior = read_csv(existing) if existing.exists() else []
    write_csv(existing, FIELDS, prior + rows)
    note = "token under an hour old, recorded not run" if too_young else "ran"
    print(f"Expired sweep: {note}. attempts.csv now has {len(prior) + len(rows)} rows.")


def main() -> None:
    parser = argparse.ArgumentParser(prog="access")
    parser.add_argument(
        "action",
        choices=["run", "expired"],
        help="the full sweep, or the expired-token sweep",
    )
    if parser.parse_args().action == "run":
        run()
    else:
        expired()


if __name__ == "__main__":
    main()
