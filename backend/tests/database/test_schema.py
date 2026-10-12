# Checks a passage can hold an embedding. That the backend's secret key reaches every table is shown by
# the seed, which writes and reads back every table with it in almost every test here.
import pytest

pytestmark = pytest.mark.integration


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
