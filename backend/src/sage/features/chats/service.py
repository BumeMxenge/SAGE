# Chats about a plan, or about a pair of plans, and the questions she asks in them. Nothing here
# opens while the questionnaire is still waiting to narrow her set.
from uuid import UUID, uuid4

from sage.features.plans import service as plans
from sage.shared.advisor import Advisor
from sage.shared.errors import (
    ChatNotFound,
    DifferentPlanSets,
    QuestionnairePending,
    SamePlan,
)
from sage.shared.repositories import StudentRepository
from sage.shared.students import Chat, CitedMessage, Message


def ensure_ready(students: StudentRepository, student_id: UUID) -> None:
    rows = students.current_plan_set(student_id)
    if rows is not None and plans.questionnaire_needed(rows):
        raise QuestionnairePending()


def stored_pair(plan_id: UUID, other_plan_id: UUID | None) -> tuple[UUID, UUID | None]:
    # A pair is stored lowest id first, so it reads the same whichever order she sent it in
    if other_plan_id is None:
        return plan_id, None
    if plan_id == other_plan_id:
        raise SamePlan()
    return min(plan_id, other_plan_id), max(plan_id, other_plan_id)


def on(
    students: StudentRepository,
    student_id: UUID,
    plan_id: UUID,
    other_plan_id: UUID | None,
) -> tuple[Chat, ...]:
    ensure_ready(students, student_id)
    return students.chats(student_id, *stored_pair(plan_id, other_plan_id))


def start(
    students: StudentRepository,
    student_id: UUID,
    plan_id: UUID,
    other_plan_id: UUID | None,
) -> Chat:
    ensure_ready(students, student_id)
    first, second = stored_pair(plan_id, other_plan_id)
    if second is None:
        plans.one_plan(students, student_id, first)  # only to check it's hers
    else:
        one, two = plans.two_plans(students, student_id, first, second)
        if one.plan_set.id != two.plan_set.id:
            raise DifferentPlanSets()
    return students.add_chat(
        Chat(id=uuid4(), student_id=student_id, plan_id=first, other_plan_id=second)
    )


def read(
    students: StudentRepository, student_id: UUID, chat_id: UUID
) -> tuple[CitedMessage, ...]:
    ensure_ready(students, student_id)
    found = students.messages(student_id, chat_id)
    if found is None:
        raise ChatNotFound()
    return found


def ask(
    students: StudentRepository,
    advisor: Advisor,
    student_id: UUID,
    chat_id: UUID,
    content: str,
    term: str | None,
) -> tuple[CitedMessage, CitedMessage]:
    ensure_ready(students, student_id)
    chat = students.chat(student_id, chat_id)
    if chat is None:
        raise ChatNotFound()
    reply = advisor.reply(chat, content, term)
    asked = Message(
        id=uuid4(),
        chat_id=chat.id,
        student_id=student_id,
        role="user",
        content=content,
        term=term,
    )
    answered = Message(
        id=uuid4(),
        chat_id=chat.id,
        student_id=student_id,
        role="assistant",
        content=reply.content,
        term=term,
        referral=reply.referral,
        open_plan_id=reply.open_plan_id,
    )
    question, answer = students.add_exchange(asked, answered, reply.citations)
    if reply.title is not None:
        students.name_chat(student_id, chat.id, reply.title)
    return (
        CitedMessage(message=question),
        CitedMessage(message=answer, citations=reply.citations),
    )
