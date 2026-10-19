# Checks the advisor's stand-in, which hands every question to a human advisor
from uuid import uuid4

import pytest

from sage.advisor.stubs import FIXED_REPLY, FixedAdvisor
from sage.shared.advisor import Reply
from sage.shared.students import Chat


@pytest.mark.stub("advisor")
def test_the_fixed_reply_refers_her_and_offers_a_pairs_second_plan():
    pair = Chat(id=uuid4(), student_id=uuid4(), plan_id=uuid4(), other_plan_id=uuid4())
    assert FixedAdvisor().reply(pair, "Which plan?", "sem1") == Reply(
        content=FIXED_REPLY, referral=True, open_plan_id=pair.other_plan_id
    )
    alone = pair.model_copy(update={"other_plan_id": None})
    assert FixedAdvisor().reply(alone, "Which plan?", "sem1").open_plan_id is None
