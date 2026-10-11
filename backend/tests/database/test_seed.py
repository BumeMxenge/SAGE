# Checks sage seed's path through the real database: the counts, a second run, the read-back, and
# the query the browser will make to show her plans
import pytest
from postgrest import CountMethod

from sage.adapters.supabase import students
from sage.domain.rules import RuleSet, year_column
from sage.services.seed import load_seed, seed

pytestmark = pytest.mark.integration

# The query the frontend will make: her latest complete plan set, its visible plans in order, and
# each plan's courses with their names and credits
PLANS = "period, version, plans(position, name, hidden, plan_courses(course_code, courses(name, credits)))"


def stored_counts(secret, student_id: str) -> dict[str, int]:
    def count(table: str, column: str, value: object) -> int:
        query = secret.table(table).select("*", count=CountMethod.exact, head=True)
        return query.eq(column, value).execute().count

    rulebook = {
        table: count(table, year_column(table), 2026) for table in RuleSet.model_fields
    }
    hers = {"students": count("students", "id", student_id)}
    hers |= {table: count(table, "student_id", student_id) for table in students.ORDER}
    return rulebook | hers


def latest_plans(client) -> list[dict]:
    query = (
        client.table("plan_sets")
        .select(PLANS)
        .eq("complete", True)
        .eq("plans.hidden", False)
        .order("period", desc=True)
        .order("version", desc=True)
        .order("position", foreign_table="plans")
        .limit(1)
    )
    rows = query.execute().data
    return rows[0]["plans"] if rows else []


def test_counts_match_the_mbali_table(secret, her, mbali_counts):
    assert stored_counts(secret, str(her.id)) == mbali_counts


def test_seeding_again_changes_nothing_and_reads_back_as_the_file(
    secret, her, stores, seed_file, mbali_counts
):
    before = stores[1].get(her.id)
    result = seed(*stores, load_seed(seed_file, her.id))
    assert result.rulebook_differences == result.student_differences == ()
    # Compared as written: seeding again stamps her chats and messages with new times
    assert stores[1].get(her.id).model_dump() == before.model_dump()
    assert stored_counts(secret, str(her.id)) == mbali_counts


def test_the_browser_gets_her_visible_plans_with_their_courses(her, stranger):
    plans = latest_plans(her.client)
    assert [plan["position"] for plan in plans] == [1, 5, 6, 7, 8, 9, 10]
    for plan in plans:
        assert len(plan["plan_courses"]) == 8
        assert sum(row["courses"]["credits"] for row in plan["plan_courses"]) == 138
    assert latest_plans(stranger.client) == []
