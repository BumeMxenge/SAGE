# The advisor's stand-in, which the API runs on until the real advisor exists. It fills the interface
# in shared/advisor.py, so swapping the real one in never touches a route.
from sage.shared.advisor import Reply
from sage.shared.students import Chat

FIXED_REPLY = (
    "I can't answer questions yet. Your faculty advisor can help with this one."
)


class FixedAdvisor:
    # One fixed reply in the final format, handing every question to a human advisor. In a pair
    # chat its Open plan action points at the second plan. The real advisor replaces this.
    def reply(self, chat: Chat, question: str, term: str | None) -> Reply:
        return Reply(
            content=FIXED_REPLY, referral=True, open_plan_id=chat.other_plan_id
        )
