# Onboarding: reading her transcript, the catalogue the review screen picks from, and Finish setup,
# which saves the lines she confirmed and attaches her plans
from fastapi import APIRouter, Depends, Request
from starlette.concurrency import run_in_threadpool

from sage.api.routes.me import me
from sage.services import onboarding
from sage.shared.api.deps import (
    STUDENT_ERRORS,
    Generator,
    Rules,
    StudentAccount,
    Students,
    student_account,
)
from sage.shared.api.models import (
    Catalogue,
    Course,
    Curriculum,
    Me,
    ResultSymbol,
    Setup,
    Transcript,
    TranscriptLine,
    TranscriptWarning,
)
from sage.shared.api.problems import errors
from sage.shared.errors import (
    FileTooLarge,
    InvalidRequest,
    NoCourseHistory,
    NotAPdf,
    NotATranscript,
    RulebookNotLoaded,
    TranscriptIncomplete,
    TranscriptNotYours,
    TranscriptUnreadable,
    UnknownCurriculum,
    UnknownResult,
)
from sage.shared.students import CourseHistoryLine

MAX_TRANSCRIPT_BYTES = 10 * 1024 * 1024

router = APIRouter(tags=["onboarding"])


@router.post(
    "/onboarding/transcript",
    summary="Read the course history off her transcript PDF, keeping nothing",
    # The PDF is the whole body rather than a multipart form, because Starlette writes a multipart
    # upload over 1 MB to disk, and the transcript must never touch disk
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/pdf": {"schema": {"type": "string", "format": "binary"}}
            },
        }
    },
    responses=errors(
        *STUDENT_ERRORS,
        FileTooLarge,
        NotAPdf,
        TranscriptUnreadable,
        NotATranscript,
        TranscriptNotYours,
        TranscriptIncomplete,
        NoCourseHistory,
        RulebookNotLoaded,
    ),
)
async def read_transcript(
    request: Request, account: StudentAccount, rulebook: Rules
) -> Transcript:
    if (
        request.headers.get("content-type", "").partition(";")[0].strip()
        != "application/pdf"
    ):
        raise NotAPdf()
    data = bytearray()
    async for chunk in request.stream():
        data += chunk
        if len(data) > MAX_TRANSCRIPT_BYTES:
            raise FileTooLarge()
    if not data.startswith(b"%PDF-"):
        raise NotAPdf()
    # Reading a PDF is slow work for the CPU, and the rulebook may need a database read, so both
    # run off the event loop
    transcript, options = await run_in_threadpool(
        onboarding.read_transcript, bytes(data), account, rulebook
    )
    return Transcript(
        student_number=transcript.student_number,
        programme=transcript.programme,
        curriculum_options=[
            Curriculum(code=row.code, name=row.name) for row in options
        ],
        issued_on=transcript.issued_on,
        lines=[
            TranscriptLine.model_validate(line, from_attributes=True)
            for line in transcript.lines
        ],
        warnings=[
            TranscriptWarning.model_validate(warning, from_attributes=True)
            for warning in transcript.warnings
        ],
    )


@router.get(
    "/catalogue",
    summary="The current handbook's curricula, courses and result symbols",
    dependencies=[Depends(student_account)],
    responses=errors(*STUDENT_ERRORS, RulebookNotLoaded),
)
def get_catalogue(rulebook: Rules) -> Catalogue:
    year = rulebook.current_year()
    rules = rulebook.year(year)
    return Catalogue(
        year=year,
        curricula=[
            Curriculum(code=row.code, name=row.name)
            for row in sorted(rules.curricula, key=lambda row: row.code)
        ],
        courses=[
            Course.model_validate(row, from_attributes=True)
            for row in sorted(rules.courses, key=lambda row: row.code)
        ],
        symbols=[
            ResultSymbol.model_validate(row, from_attributes=True)
            for row in rulebook.symbols().values()
        ],
    )


@router.post(
    "/onboarding/complete",
    summary="Save the course history she confirmed, and attach her plans",
    responses=errors(
        *STUDENT_ERRORS,
        InvalidRequest,
        UnknownCurriculum,
        UnknownResult,
        RulebookNotLoaded,
    ),
)
def complete_onboarding(
    setup: Setup,
    account: StudentAccount,
    students: Students,
    rulebook: Rules,
    generator: Generator,
) -> Me:
    history = [
        CourseHistoryLine(student_id=account.id, **line.model_dump())
        for line in setup.lines
    ]
    profile = onboarding.complete(
        account.id, setup.curriculum_code, history, students, rulebook, generator
    )
    return me(account, onboarding_complete=profile.onboarding_complete)
