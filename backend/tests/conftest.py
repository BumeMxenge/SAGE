# Shared pytest fixtures for every backend test
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from sage.cli import SEED_FILE
from sage.main import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture(scope="session")
def seed_file() -> Path:
    return SEED_FILE


@pytest.fixture(scope="session")
def mbali_counts() -> dict[str, int]:
    # The rows per table that the M1 plan's Mbali table lists for the seed file
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
