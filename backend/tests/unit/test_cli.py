# Checks `sage seed` asks before writing anywhere but this laptop, `sage sign-in` refuses to run
# anywhere else and makes nothing before her plans' year is loaded, and `sage review` walks a person
# through the pending rows, correcting an elective by picking its tab from the list. The database is
# replaced by the in-memory fakes, so these tests never reach a real project.
import json
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

import sage.cli
from sage.config import get_settings
from sage.ingestion.checks import Check, Failure
from sage.ingestion.ingest import Candidate, Sitting
from sage.ingestion.sources import Reading
from sage.ingestion.translate import Translations
from sage.shared.memory.rules import InMemoryRuleRepository
from sage.shared.memory.students import InMemoryStudentRepository
from sage.shared.rules import (
    AllOfGroup,
    Course,
    CourseGroupMember,
    CurriculumRule,
    HandbookVersion,
    Refer,
    RuleSet,
    TotalCredits,
    YearRules,
)

ACCOUNT = UUID("00000000-0000-4000-8000-000000000001")


@pytest.fixture
def opened(monkeypatch, approved_2026):
    # Hands the command the fakes instead of Supabase, with the approved 2026 loaded, and records
    # each connection it opens
    urls = []
    rules = InMemoryRuleRepository()
    rules.replace_year(approved_2026)
    monkeypatch.setattr(sage.cli, "connect", lambda url, secret_key: urls.append(url))
    monkeypatch.setattr(sage.cli, "SupabaseRuleRepository", lambda client: rules)
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


def test_sign_in_refuses_a_hosted_project(opened, database):
    database("https://example.supabase.co")
    with pytest.raises(SystemExit, match="only runs on local Supabase"):
        sage.cli.run_sign_in(3000)
    assert opened == []


def test_sign_in_makes_nothing_until_her_plans_year_is_loaded(
    opened, database, monkeypatch
):
    # Local Supabase before make load, so not even her account is made
    database("http://127.0.0.1:54321")
    monkeypatch.setattr(
        sage.cli, "SupabaseRuleRepository", lambda client: InMemoryRuleRepository()
    )
    monkeypatch.setattr(
        sage.cli, "sign_in_token", lambda client, email: pytest.fail("made her account")
    )
    with pytest.raises(SystemExit, match="make load"):
        sage.cli.run_sign_in(3000)


def made_up_year() -> Candidate:
    # A first year whose review has four rows: a curriculum note on a year whose printed total
    # fails its check, and three drafted requirements
    codes = ("EEE3001F", "EEE3002F", "EEE3004F")
    year_two = YearRules(
        all=(
            AllOfGroup(all_of_group="EB022EEE02-y2-core"),
            TotalCredits(total_credits=136),
        )
    )
    rules = RuleSet(
        handbook_versions=(HandbookVersion(year=2026),),
        curriculum_rules=(
            CurriculumRule(
                handbook_year=2026,
                curriculum_code="EB022EEE02",
                year_of_study=2,
                rule=year_two,
            ),
        ),
        courses=tuple(
            Course(
                handbook_year=2026,
                code=code,
                name="Made Up",
                credits=8,
                nqf_level=5,
                term="sem1",
                entry_rule=Refer(refer=f"{code}'s words"),
            )
            for code in codes
        ),
    )
    readings = (
        Reading(
            entity="curriculum_rules",
            key="EB022EEE02/2",
            place="p. 53",
            printed="*A made-up note.",
            flag="refused_free_text",
        ),
        *(
            Reading(
                entity="courses",
                key=code,
                place="p. 130",
                printed=f"{code}'s words",
                flag="refused_free_text",
            )
            for code in codes
        ),
    )
    totals = Failure(
        place="p. 53",
        what="EB022EEE02 year 2's core table prints 136 credits, but its rows add up to 144",
        flags=("curriculum_rules", "EB022EEE02/2"),
    )
    return Candidate(
        year=2026,
        rules=rules,
        readings=readings,
        rows={},
        translations=Translations(translations=(), calls=0, reused=0, refused=()),
        checks=(Check(name="Printed totals add up", failures=(totals,)),),
        expanded={},
        left_out=(),
        entries=frozenset(),
        unprinted=(),
        notes=(),
        previous=None,
        carried=(),
    )


def test_a_review_walk_saves_each_decision_as_it_is_made(tmp_path, capsys):
    path = tmp_path / "review.json"
    start = datetime(2026, 10, 18, 9, tzinfo=UTC)
    times = iter([start, *[start + timedelta(minutes=8)] * 9])
    sitting = Sitting(made_up_year(), path, lambda: next(times))
    # The note asks for a note, as its year's total fails a check. A stray key is asked again. The
    # correction is first saved without its need. A first year has nothing to reject for.
    answers = iter(["a", "The rows are right", "x", "a", "c", "r", "q"])
    saved = iter(['{"course": "EEE3001F"}', '{"course": "EEE3001F", "need": "pass"}'])
    opened = []

    def edit(file):
        opened.append(file.read_text(encoding="utf-8"))
        file.write_text(next(saved), encoding="utf-8")

    sage.cli.walk(sitting, lambda prompt: next(answers), edit)
    rows = json.loads(path.read_text(encoding="utf-8"))["rows"]
    assert [
        (row["id"], row["decision"], row["corrected"], row["note"]) for row in rows
    ] == [
        ("rule/EB022EEE02/2", "accept", None, "The rows are right"),
        ("requirement/EEE3001F", "accept", None, None),
        (
            "requirement/EEE3002F",
            "correct",
            {"course": "EEE3001F", "need": "pass"},
            None,
        ),
        ("requirement/EEE3004F", None, None, None),
    ]
    # The editor opened with the draft, then again with why the first save wasn't used
    assert '"refer": "EEE3002F\'s words"' in opened[0]
    assert "Not used" not in opened[0]
    assert "// Not used: corrected isn't a requirement tree" in opened[1]
    assert '{"course": "EEE3001F"}' in opened[1]
    out = capsys.readouterr().out
    assert "Row 1 of 4: rule/EB022EEE02/2" in out
    assert "every course in EB022EEE02-y2-core, and 136 credits in total" in out
    assert "This sitting took 8 minutes and decided 3 rows." in out


def test_correcting_an_elective_picks_its_tab_by_number(tmp_path, capsys):
    # A course the model put on history, and a language option, whose tab is fixed
    drafted = {"HST1013F": "history", "SLL1017F": "languages"}
    rules = RuleSet(
        handbook_versions=(HandbookVersion(year=2026),),
        courses=tuple(
            Course(
                handbook_year=2026,
                code=code,
                name="Made Up",
                credits=18,
                nqf_level=5,
                term="sem1",
                summary="A drafted summary. It reads well.",
            )
            for code in drafted
        ),
        course_group_members=tuple(
            CourseGroupMember(
                handbook_year=2026,
                group_key="complementary",
                course_code=code,
                category=tab,
            )
            for code, tab in drafted.items()
        ),
    )
    readings = tuple(
        reading
        for code in drafted
        for reading in (
            Reading(entity="courses", key=code, place="p. 9", printed="None"),
            Reading(
                entity="course_group_members",
                key=f"complementary/{code}",
                place="Courses row 3",
                printed=f"{code} Made Up\nCourse outline: A made-up outline.",
                flag="model_written",
            ),
        )
    )
    candidate = made_up_year().model_copy(
        update={"rules": rules, "readings": readings, "checks": ()}
    )
    path = tmp_path / "review.json"
    start = datetime(2026, 10, 23, 9, tzinfo=UTC)
    sitting = Sitting(candidate, path, lambda: start)
    # The tabs less languages, in ElectiveTab's order: arts, business, econ and on to society, the
    # 11th, so 12 is asked again and 3 is econ. The language option asks only for its summary.
    answers = iter(["c", "12", "3", "History, corrected. Short.", "c", "Corrected."])
    sage.cli.walk(sitting, lambda prompt: next(answers), lambda file: None)
    rows = json.loads(path.read_text(encoding="utf-8"))["rows"]
    assert [(row["id"], row["decision"], row["corrected"]) for row in rows] == [
        (
            "elective/HST1013F",
            "correct",
            {"tab": "econ", "summary": "History, corrected. Short."},
        ),
        ("elective/SLL1017F", "correct", {"tab": "languages", "summary": "Corrected."}),
    ]
    out = capsys.readouterr().out
    assert "  3 econ" in out
    assert "on the history tab: A drafted summary. It reads well." in out
