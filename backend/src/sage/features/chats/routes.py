# Chats about one plan or a pair of plans, and the questions she asks in them. Each answer is the
# advisor stand-in's fixed reply until the real advisor arrives.
from uuid import UUID

from fastapi import APIRouter

from sage.features.chats import service as chats
from sage.features.chats.models import (
    Chat,
    Citation,
    Exchange,
    Message,
    NewChat,
    NewMessage,
)
from sage.shared import students as domain
from sage.shared.api.deps import ONBOARDED_ERRORS, ChatAdvisor, Onboarded, Students
from sage.shared.api.problems import errors
from sage.shared.errors import (
    AdvisorUnavailable,
    ChatNotFound,
    DifferentPlanSets,
    InvalidRequest,
    PlanNotFound,
    QuestionnairePending,
    RulebookNotLoaded,
    SamePlan,
)

router = APIRouter(prefix="/chats", tags=["chats"])


@router.get(
    "",
    summary="Her chats on exactly this plan or pair, newest first",
    responses=errors(*ONBOARDED_ERRORS, InvalidRequest, SamePlan, QuestionnairePending),
)
def list_chats(
    plan_id: UUID,
    student: Onboarded,
    students: Students,
    other_plan_id: UUID | None = None,
) -> list[Chat]:
    return [
        Chat.model_validate(chat, from_attributes=True)
        for chat in chats.on(students, student.id, plan_id, other_plan_id)
    ]


@router.post(
    "",
    status_code=201,
    summary="Start a chat about one of her plans, or a pair from the same set",
    responses=errors(
        *ONBOARDED_ERRORS,
        InvalidRequest,
        PlanNotFound,
        SamePlan,
        DifferentPlanSets,
        QuestionnairePending,
    ),
)
def start_chat(new: NewChat, student: Onboarded, students: Students) -> Chat:
    chat = chats.start(students, student.id, new.plan_id, new.other_plan_id)
    return Chat.model_validate(chat, from_attributes=True)


@router.get(
    "/{chat_id}/messages",
    summary="A chat's messages in order, with what each answer cites",
    responses=errors(
        *ONBOARDED_ERRORS, InvalidRequest, ChatNotFound, QuestionnairePending
    ),
)
def list_messages(
    chat_id: UUID, student: Onboarded, students: Students
) -> list[Message]:
    return [message_model(row) for row in chats.read(students, student.id, chat_id)]


@router.post(
    "/{chat_id}/messages",
    status_code=201,
    summary="Ask a question in a chat, and get the advisor's reply",
    responses=errors(
        *ONBOARDED_ERRORS,
        InvalidRequest,
        ChatNotFound,
        QuestionnairePending,
        RulebookNotLoaded,
        AdvisorUnavailable,
    ),
)
def send_message(
    chat_id: UUID,
    new: NewMessage,
    student: Onboarded,
    students: Students,
    advisor: ChatAdvisor,
) -> Exchange:
    question, reply = chats.ask(
        students, advisor, student.id, chat_id, new.content, new.term
    )
    return Exchange(question=message_model(question), reply=message_model(reply))


def message_model(row: domain.CitedMessage) -> Message:
    message = row.message
    return Message(
        id=message.id,
        role=message.role,
        content=message.content,
        term=message.term,
        created_at=message.created_at,
        referral=message.referral,
        open_plan_id=message.open_plan_id,
        citations=[
            Citation.model_validate(citation, from_attributes=True)
            for citation in row.citations
        ],
    )
