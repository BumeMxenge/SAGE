# Shared pytest fixtures for every backend test
import json
from collections.abc import Callable
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from fpdf import FPDF

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
    # UCT's 26 symbols, as the rule-tables migration stores them, for the in-memory rulebook. A copy,
    # as the unit tests have no database, and test_the_symbols_are_ucts_26 compares it with the
    # migration's rows on every make check-db, so the two can't drift apart.
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


@pytest.fixture
def transcript_pages() -> list[list[str]]:
    # The made-up transcript in the real layout, page by page, as pdf_pages reads one: Mbali's
    # identity and her seeded lines. A fresh copy each time, so a test can edit it.
    text = (Path(__file__).parent / "fixtures" / "transcript.txt").read_text(
        encoding="utf-8"
    )
    return [page.strip("\n").split("\n") for page in text.split("\f")]


@pytest.fixture(scope="session")
def pdf_of() -> Callable[[list[list[str]]], bytes]:
    # Prints pages of lines into a PDF, one line per row. Windows-1252 lets the built-in font print
    # the record's dashes.
    def make(pages: list[list[str]]) -> bytes:
        pdf = FPDF()
        pdf.core_fonts_encoding = "windows-1252"
        pdf.set_font("Helvetica", size=9)
        for page in pages:
            pdf.add_page()
            for line in page:
                pdf.cell(text=line, new_x="LMARGIN", new_y="NEXT")
        return bytes(pdf.output())

    return make
