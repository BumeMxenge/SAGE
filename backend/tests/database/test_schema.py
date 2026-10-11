# Checks the backend's secret key reaches every table, sent the way supabase-py sends it, and that
# a passage can hold an embedding
import pytest

from sage.adapters.supabase import students
from sage.domain.rules import RuleSet

pytestmark = pytest.mark.integration

# Every table the backend uses. Not heartbeat: only the keep-alive's publishable key reads that.
TABLES = [*RuleSet.model_fields, "students", *students.ORDER, "result_symbols"]


@pytest.mark.parametrize("table", TABLES)
def test_the_secret_key_reaches_every_table(secret, table):
    secret.table(table).select("*").limit(1).execute()


def test_a_passage_can_hold_an_embedding(secret, her):
    passage = {
        "handbook_year": 2026,
        "source": "Test handbook",
        "section": "Test",
        "page": 1,
        "content": "Test",
        "embedding": [0.25, 0.5, 0.75],
    }
    stored = secret.table("passages").insert(passage).execute().data[0]
    secret.table("passages").delete().eq("id", stored["id"]).execute()
    assert stored["embedding"] == "[0.25,0.5,0.75]"
