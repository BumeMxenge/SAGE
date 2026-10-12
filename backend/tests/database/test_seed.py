# Checks sage seed's path through the real database: a second run changes nothing, and her data
# reads back as the file holds it, row for row and in number
import pytest
from postgrest import CountMethod

from sage.adapters.supabase import students
from sage.domain.rules import RuleSet, year_column
from sage.services.seed import load_seed, seed

pytestmark = pytest.mark.integration


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


def test_seeding_again_changes_nothing_and_reads_back_as_the_file(
    secret, her, stores, seed_file, mbali_counts
):
    before = stores[1].get(her.id)
    result = seed(*stores, load_seed(seed_file, her.id))
    assert result.rulebook_differences == result.student_differences == ()
    # Compared as written: seeding again stamps her chats and messages with new times
    assert stores[1].get(her.id).model_dump() == before.model_dump()
    assert stored_counts(secret, str(her.id)) == mbali_counts
