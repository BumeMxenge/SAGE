# Onboarding: reading her transcript for the review screen, then saving the course history she
# confirmed and attaching her plans
from collections.abc import Sequence
from uuid import UUID

from sage.domain.accounts import Account
from sage.domain.errors import UnknownCurriculum, UnknownResult
from sage.domain.planning import PlanGenerator
from sage.domain.repositories import StudentRepository
from sage.domain.rules import Curriculum
from sage.domain.students import CourseHistoryLine, Student
from sage.ingestion.transcript import (
    Transcript,
    TranscriptWarning,
    pdf_pages,
    read_lines,
)
from sage.services.rulebook import Rulebook


def read_transcript(
    data: bytes, account: Account, rulebook: Rulebook
) -> tuple[Transcript, tuple[Curriculum, ...]]:
    # Her transcript's lines, warnings and the curricula her programme could be. The PDF and its
    # text are only ever in memory, and nothing is saved until Finish setup.
    transcript = read_lines(pdf_pages(data), account.student_number)
    year = rulebook.current_year()
    previous = year - 1
    warnings = list(transcript.warnings)
    if not any(line.academic_year == previous for line in transcript.lines):
        # A gap year looks the same, so she can carry on
        warnings.append(
            TranscriptWarning(
                code="recent_year_missing",
                message=f"Your record has no courses for {previous}. If you took that year "
                "off, you can carry on.",
            )
        )
    elif any(
        line.academic_year == previous and not line.result_printed
        for line in transcript.lines
    ):
        warnings.append(
            TranscriptWarning(
                code="results_pending",
                message=f"Some of your {previous} results aren't out yet, so those courses "
                "are marked in progress. Check them before you finish.",
            )
        )
    programme = (transcript.programme or "").casefold()
    options = tuple(
        curriculum
        for curriculum in sorted(
            rulebook.year(year).curricula, key=lambda row: row.code
        )
        if programme and curriculum.name.casefold().startswith(programme)
    )
    return transcript.model_copy(update={"warnings": tuple(warnings)}), options


def complete(
    student_id: UUID,
    curriculum_code: str,
    history: Sequence[CourseHistoryLine],
    students: StudentRepository,
    rulebook: Rulebook,
    generator: PlanGenerator,
) -> Student:
    year = rulebook.current_year()
    rules = rulebook.year(year)
    if curriculum_code not in {curriculum.code for curriculum in rules.curricula}:
        raise UnknownCurriculum(
            f"{curriculum_code} isn't a curriculum in the {year} handbook."
        )
    symbols = rulebook.symbols()
    for line in history:
        if line.result not in symbols:
            raise UnknownResult(f"{line.result} isn't one of UCT's result symbols.")

    # Written in an order a retry can finish: she stays in onboarding until the last write, and
    # sending the same lines twice leaves the same state, with one plan set
    profile = Student(
        id=student_id,
        curriculum_code=curriculum_code,
        intake_year=min(line.academic_year for line in history),
    )
    students.save_profile(profile)
    students.replace_history(student_id, history)
    current = students.current_plan_set(student_id)
    if current is None or current.plan_set.period != year:
        students.add_plan_set(generator.generate(profile, history, rules))
    done = profile.model_copy(update={"onboarding_complete": True})
    students.save_profile(done)
    return done
