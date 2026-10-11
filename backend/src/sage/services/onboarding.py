# Onboarding: saving the course history she confirmed, and attaching her plans
from collections.abc import Sequence
from uuid import UUID

from sage.domain.errors import UnknownCurriculum, UnknownResult
from sage.domain.planning import PlanGenerator
from sage.domain.repositories import StudentRepository
from sage.domain.students import CourseHistoryLine, Student
from sage.services.rulebook import Rulebook


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
