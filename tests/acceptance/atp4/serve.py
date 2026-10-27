# SAGE's API on port 8001 for ATP-4, against local Supabase, with only the advisor swapped. The fake
# advisor sleeps for the delay a question names, such as [d=3.2], then replies with the question's id
# and the names of the chat's plan or pair, as the chat it was handed holds them. [offer] makes it
# offer her first hidden plan, as a reply offers one. Sign-in, the chats service and the store are
# the real ones, and no file in backend/src changes.
import re
import time

import uvicorn
from fastapi import Request

from sage.config import get_settings, is_local
from sage.main import app
from sage.shared.advisor import Reply
from sage.shared.api import deps
from sage.shared.repositories import StudentRepository
from sage.shared.students import Chat

PORT = 8001
# The OpenAI key make atp4 passes, so a fake that failed to take over could never spend money
STAND_IN = "atp4-stand-in"
DELAY = re.compile(r"\[d=(\d+(?:\.\d+)?)\]")
ASKED = re.compile(r"\[(S\d-\d{2}-\d)\]")
OFFER = "[offer]"


def delay(question: str) -> float:
    found = DELAY.search(question)
    return float(found.group(1)) if found else 0.0


class FakeAdvisor:
    def __init__(self, students: StudentRepository) -> None:
        self.students = students

    def reply(self, chat: Chat, question: str, term: str | None) -> Reply:
        time.sleep(delay(question))
        asked = ASKED.search(question)
        held = [chat.plan_id, *([chat.other_plan_id] if chat.other_plan_id else [])]
        names = sorted(
            rows.plans[0].name for rows in self.students.plans(chat.student_id, held)
        )
        offered = None
        if OFFER in question:
            current = self.students.current_plan_set(chat.student_id)
            hidden = sorted(
                (plan for plan in current.plans if plan.hidden),
                key=lambda plan: plan.position,
            )
            offered = hidden[0].id
        question_id = asked.group(1) if asked else "unnamed"
        return Reply(
            content=f"{question_id} answered for {' | '.join(names)}",
            referral=False,
            open_plan_id=offered,
        )


def fake(request: Request) -> FakeAdvisor:
    return FakeAdvisor(request.app.state.students)


def main() -> None:
    settings = get_settings()
    # backend/.env may name the hosted project, and this writes chats
    if not is_local(settings.supabase_url):
        raise SystemExit(
            "serve.py runs only against local Supabase: make atp4 points it there"
        )
    if settings.openai_api_key != STAND_IN:
        raise SystemExit(
            f"serve.py runs only with OPENAI_API_KEY={STAND_IN}, as make atp4 sets"
        )
    app.dependency_overrides[deps.advisor] = fake
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")


if __name__ == "__main__":
    main()
