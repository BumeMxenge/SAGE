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
def opened(monkeypatch):
    # Hands the command the fakes instead of Supabase, and records each connection it opens
    urls = []
    monkeypatch.setattr(sage.cli, "connect", lambda url, secret_key: urls.append(url))
    monkeypatch.setattr(
        sage.cli, "SupabaseRuleRepository", lambda client: InMemoryRuleRepository()
    )
    monkeypatch.setattr(
        sage.cli,
        "SupabaseStudentRepository",
        lambda client: InMemoryStudentRepository(),
    )
    return urls


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


def test_local_supabase_is_seeded_without_asking(opened, database, monkeypatch, capsys):
    database("http://127.0.0.1:54321")
    monkeypatch.setattr("builtins.input", never_asked)
    sage.cli.run_seed(ACCOUNT, yes=False)
    assert opened == ["http://127.0.0.1:54321"]
    assert "her data matches the file" in capsys.readouterr().out


def test_a_hosted_project_needs_a_yes(opened, database, monkeypatch):
    database("https://example.supabase.co")
    monkeypatch.setattr("builtins.input", lambda prompt: "no")
    with pytest.raises(SystemExit, match="Nothing written"):
        sage.cli.run_seed(ACCOUNT, yes=False)
    assert opened == []


def test_yes_answers_for_you(opened, database, monkeypatch):
    database("https://example.supabase.co")
    monkeypatch.setattr("builtins.input", never_asked)
    sage.cli.run_seed(ACCOUNT, yes=True)
    assert opened == ["https://example.supabase.co"]


def test_missing_settings_stop_it_before_anything_else(opened, database):
    database("")
    with pytest.raises(SystemExit, match="SUPABASE_URL"):
        sage.cli.run_seed(ACCOUNT, yes=True)
    assert opened == []
