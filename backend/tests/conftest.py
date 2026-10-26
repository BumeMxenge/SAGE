# Shared pytest fixtures for every backend test
import json
import os
import tempfile
from pathlib import Path

import pytest

from sage.ingestion.ingest import approved_snapshot
from sage.shared.rules import ResultSymbol, RuleSet
from sage.shared.seed import SEED_FILE
from tests.pdf import split_pages


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    # make mutation runs many test sessions at once, so each takes a temporary folder of its own in
    # SAGE_TEST_TEMP. Their default folders share one pytest-current link, which every session
    # remakes as it ends, and a session that crashes there would count as a caught mutant.
    root = os.environ.get("SAGE_TEST_TEMP")
    if root and config.option.basetemp is None:
        config.option.basetemp = tempfile.mkdtemp(dir=root)


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
def approved_2026() -> RuleSet:
    # The approved 2026 rulebook, data/rules/2026/rulebook.json, read once. A test that needs rules
    # loads it into a store of its own, so no test can change another's.
    return approved_snapshot(2026).rules


@pytest.fixture(scope="session")
def fake_account(seed_file) -> dict[str, str]:
    # Mbali's made-up email, which the seed file keeps for the tests and sage sign-in
    return json.loads(seed_file.read_text(encoding="utf-8"))["fake_account"]


@pytest.fixture(scope="session")
def mbali_counts() -> dict[str, int]:
    # The rows per table the seed file holds, written out by hand rather than counted from the file
    return {
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
    return split_pages(text)
