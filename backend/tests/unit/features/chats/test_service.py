# Checks the chats service on Mbali's seeded set, whose answers hid her plans at positions 2 to 4: a
# reply that offers one of them shows it again. How a reply is stored and who may reach a chat are in
# test_routes.py and test_guards.py.
from uuid import UUID

from sage.features.chats import service as chats
from sage.shared.advisor import Reply
from sage.shared.students import Chat
from tests.unit.accounts import MBALI


class Offering:
    # Answers every question by offering one plan
    def __init__(self, plan_id: UUID) -> None:
        self.plan_id = plan_id

    def reply(self, chat: Chat, question: str, term: str | None) -> Reply:
        return Reply(content="Made-up reply", referral=False, open_plan_id=self.plan_id)


def test_a_reply_that_offers_a_plan_her_answers_hid_shows_it(stores):
    students = stores[1]
    by_position = {
        plan.position: plan.id for plan in students.current_plan_set(MBALI).plans
    }
    # Her chat on plan 1 alone (c1 in the seed file), which is shown
    (chat,) = students.chats(MBALI, by_position[1], None)
    chats.ask(students, Offering(by_position[2]), MBALI, chat.id, "Made up?", "sem1")
    hidden = [
        plan.position for plan in students.current_plan_set(MBALI).plans if plan.hidden
    ]
    assert hidden == [3, 4]
