# Shared pytest fixtures for every backend test
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from sage.domain.rules import ResultSymbol
from sage.main import create_app
from sage.services.seed import SEED_FILE


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture(scope="session")
def seed_file() -> Path:
    return SEED_FILE


@pytest.fixture(scope="session")
def result_symbols() -> tuple[ResultSymbol, ...]:
    # UCT's 26 symbols, as the rule-tables migration stores them, for the in-memory rulebook
    path = Path(__file__).parent / "fixtures" / "result_symbols.json"
    rows = json.loads(path.read_text(encoding="utf-8"))
    return tuple(ResultSymbol.model_validate(row) for row in rows)


@pytest.fixture(scope="session")
def fake_account(seed_file) -> dict[str, str]:
    # Mbali's made-up name and email, which the seed file keeps for the tests
    return json.loads(seed_file.read_text(encoding="utf-8"))["fake_account"]


@pytest.fixture(scope="session")
def mbali_counts() -> dict[str, int]:
    # The rows per table the seed file holds, written out by hand rather than counted from the file
    return {
        "handbook_versions": 1,
        "curricula": 1,
        "curriculum_rules": 1,
        "courses": 52,
        "course_groups": 4,
        "course_group_members": 52,
        "equivalences": 11,
        "timetable_slots": 25,
        "timetable_slot_curricula": 0,
        "passages": 0,
        "handbook_deltas": 0,
        "students": 1,
        "course_history": 34,
        "favourites": 6,
        "plan_sets": 1,
        "plans": 10,
        "plan_courses": 80,
        "plan_reasons": 6,
        "chats": 2,
        "messages": 4,
        "message_citations": 0,
    }
