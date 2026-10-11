# The rulebook as types: one per table row, named after its columns. The database enforces every
# rule on these rows except the elective tab, which only the backend checks. Passage embeddings
# arrive with the advisor, so they aren't here yet.
from datetime import time
from typing import Any
from uuid import UUID

from pydantic import JsonValue

from sage.domain.base import Row
from sage.domain.electives import ElectiveTab


class HandbookVersion(Row):
    year: int
    approved: bool = False


class Curriculum(Row):
    handbook_year: int
    code: str
    name: str
    department: str
    degree_rule: dict[str, Any] | None = None


class CurriculumRule(Row):
    handbook_year: int
    curriculum_code: str
    year_of_study: int
    rule: dict[str, Any]


class Course(Row):
    handbook_year: int
    code: str
    name: str
    credits: int
    nqf_level: int
    term: str
    entry_rule: dict[str, Any] | None = None
    convener: str | None = None
    summary: str | None = None


class CourseGroup(Row):
    handbook_year: int
    group_key: str
    label: str


class CourseGroupMember(Row):
    handbook_year: int
    group_key: str
    course_code: str
    category: ElectiveTab | None = None


class Equivalence(Row):
    handbook_year: int
    course_code: str
    counts_as: str


class TimetableSlot(Row):
    id: UUID
    handbook_year: int
    course_code: str
    term: str
    day: int | None = None
    start_time: time | None = None
    end_time: time | None = None
    kind: str | None = None
    choice_group: str | None = None
    choice: str | None = None


class TimetableSlotCurriculum(Row):
    slot_id: UUID
    handbook_year: int
    curriculum_code: str


class Passage(Row):
    id: UUID
    handbook_year: int
    curriculum_code: str | None = None
    course_code: str | None = None
    source: str
    section: str
    page: int
    content: str


class HandbookDelta(Row):
    handbook_year: int
    entity: str
    entity_key: str
    old_value: JsonValue = None
    new_value: JsonValue = None
    corrected_value: JsonValue = None
    approved: bool | None = None


class RuleSet(Row):
    # Named after the tables and listed in foreign-key order, so writing them top to bottom never
    # points at a row that isn't stored yet
    handbook_versions: tuple[HandbookVersion, ...] = ()
    curricula: tuple[Curriculum, ...] = ()
    curriculum_rules: tuple[CurriculumRule, ...] = ()
    courses: tuple[Course, ...] = ()
    course_groups: tuple[CourseGroup, ...] = ()
    course_group_members: tuple[CourseGroupMember, ...] = ()
    equivalences: tuple[Equivalence, ...] = ()
    timetable_slots: tuple[TimetableSlot, ...] = ()
    timetable_slot_curricula: tuple[TimetableSlotCurriculum, ...] = ()
    passages: tuple[Passage, ...] = ()
    handbook_deltas: tuple[HandbookDelta, ...] = ()
