# Checks sage seed's path through the real database: a second run changes nothing, and her data
# reads back as the file holds it, row for row
import pytest

from sage.shared.seed import load_seed, seed

pytestmark = pytest.mark.integration


def test_seeding_again_changes_nothing_and_reads_back_as_the_file(
    her, stores, seed_file
):
    before = stores[1].get(her.id)
    result = seed(*stores, load_seed(seed_file, her.id))
    assert result.student_differences == ()
    # Compared as written: seeding again stamps her chats and messages with new times
    assert stores[1].get(her.id).model_dump() == before.model_dump()
