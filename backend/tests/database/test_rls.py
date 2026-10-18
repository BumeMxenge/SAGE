# Checks row level security as a browser meets it: a student reads only her own rows, a stranger
# and a signed-out browser read nothing, and nobody in a browser writes
import pytest

from sage.shared.rules import RuleSet
from sage.shared.supabase import students

pytestmark = pytest.mark.integration

PERMISSION_DENIED = "42501"
RULEBOOK_TABLES = [*RuleSet.model_fields]
STUDENT_TABLES = ["students", *students.ORDER]
# Students read the approved rulebook, except the review of changes, which only the backend sees
READABLE_RULEBOOK = [table for table in RULEBOOK_TABLES if table != "handbook_deltas"]


@pytest.mark.parametrize("table", STUDENT_TABLES)
def test_she_reads_her_own_rows_and_a_stranger_reads_none(
    her, stranger, mbali_counts, table
):
    assert (
        len(her.client.table(table).select("*").execute().data) == mbali_counts[table]
    )
    assert stranger.client.table(table).select("*").execute().data == []


@pytest.mark.parametrize("table", [*RULEBOOK_TABLES, *STUDENT_TABLES, "result_symbols"])
def test_a_signed_out_browser_is_refused(anon, refused, table):
    refused(anon.table(table).select("*"), PERMISSION_DENIED)


@pytest.mark.parametrize("table", READABLE_RULEBOOK)
def test_she_reads_the_rulebook_but_cannot_change_it(
    her, refused, approved_years, table
):
    # Every row of both loaded years, as the snapshot files hold them
    loaded = sum(len(getattr(snapshot.rules, table)) for snapshot in approved_years)
    assert len(her.client.table(table).select("*").execute().data) == loaded
    refused(her.client.table(table).insert({}), PERMISSION_DENIED)


def test_she_reads_every_result_symbol(her):
    assert len(her.client.table("result_symbols").select("*").execute().data) == 26


def test_an_unapproved_year_and_every_delta_stay_hidden(her, secret, refused):
    secret.table("handbook_versions").insert({"year": 2099}).execute()  # not approved
    course = {
        "handbook_year": 2099,
        "code": "TST2099F",
        "name": "Test",
        "credits": 0,
        "nqf_level": 5,
        "term": "sem1",
    }
    secret.table("courses").insert(course).execute()
    years = her.client.table("handbook_versions").select("year").execute().data
    courses = her.client.table("courses").select("code").eq("handbook_year", 2099)
    hidden = courses.execute().data
    # Deleting the year deletes its course too
    secret.table("handbook_versions").delete().eq("year", 2099).execute()
    assert sorted(row["year"] for row in years) == [2023, 2026]
    assert hidden == []
    refused(her.client.table("handbook_deltas").select("*"), PERMISSION_DENIED)
