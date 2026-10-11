# Checks `sage seed` asks before writing anywhere but this laptop. The database is replaced by the
# in-memory fakes, so these tests never reach a real project.
from uuid import UUID

import pytest

import sage.cli
from sage.adapters.memory.rules import InMemoryRuleRepository
from sage.adapters.memory.students import InMemoryStudentRepository
from sage.config import get_settings

ACCOUNT = UUID("00000000-0000-4000-8000-000000000001")


@pytest.fixture
def connected(monkeypatch):
    # Count connections, and hand the command the fakes instead of Supabase
    calls = []
    monkeypatch.setattr(sage.cli, "connect", lambda *args: calls.append(args))
    monkeypatch.setattr(
        sage.cli, "SupabaseRuleRepository", lambda _: InMemoryRuleRepository()
    )
    monkeypatch.setattr(
        sage.cli, "SupabaseStudentRepository", lambda _: InMemoryStudentRepository()
    )
    return calls


@pytest.fixture
def database(monkeypatch):
    # Points the settings at a URL, as `make seed` or backend/.env would. Settings are cached.
    def point_at(url: str) -> None:
        monkeypatch.setenv("SUPABASE_URL", url)
        monkeypatch.setenv("SUPABASE_SECRET_KEY", "made-up-key")
        get_settings.cache_clear()

    yield point_at
    get_settings.cache_clear()


def never_asked(prompt: str) -> str:
    raise AssertionError(f"asked: {prompt}")


def test_local_supabase_is_seeded_without_asking(
    seed_file, connected, database, monkeypatch, capsys
):
    database("http://127.0.0.1:54321")
    monkeypatch.setattr("builtins.input", never_asked)
    sage.cli.run_seed(ACCOUNT, seed_file, yes=False)
    assert len(connected) == 1
    assert "her data matches the file" in capsys.readouterr().out


def test_a_hosted_project_needs_a_yes(seed_file, connected, database, monkeypatch):
    database("https://example.supabase.co")
    monkeypatch.setattr("builtins.input", lambda prompt: "no")
    with pytest.raises(SystemExit, match="Nothing written"):
        sage.cli.run_seed(ACCOUNT, seed_file, yes=False)
    assert connected == []


def test_yes_answers_for_you(seed_file, connected, database, monkeypatch):
    database("https://example.supabase.co")
    monkeypatch.setattr("builtins.input", never_asked)
    sage.cli.run_seed(ACCOUNT, seed_file, yes=True)
    assert len(connected) == 1


def test_missing_settings_stop_it_before_anything_else(seed_file, connected, database):
    database("")
    with pytest.raises(SystemExit, match="SUPABASE_URL"):
        sage.cli.run_seed(ACCOUNT, seed_file, yes=True)
    assert connected == []
