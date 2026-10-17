# The rulebook as types: one per table row, named after its columns. The database enforces every
# rule on these rows except the elective tab, the delta flag and the shape of each rule tree, which
# only the backend checks.
from datetime import time
from typing import Annotated, Any, Literal, Self
from uuid import UUID

from pydantic import (
    AfterValidator,
    Discriminator,
    Field,
    JsonValue,
    Tag,
    model_validator,
)

from sage.domain.base import Row
from sage.domain.electives import ElectiveTab

# The term_code domain in the rule-tables migration: every term a course or meeting can run in
TermCode = Literal[
    "q1", "q2", "q3", "q4", "sem1", "sem2", "full_year", "winter", "summer", "other"
]
# A course code in the handbook's eight-character format, as courses.code's check in the
# rule-tables migration gives it, such as EEE4117F
COURSE_CODE = r"[A-Z]{3}[0-9]{4}[A-Z]"
# The handbook's course-code suffix key, as the rule-tables migration gives it: A to D are quarters,
# F and S semesters, H and W the whole year, L winter, U, J and P summer, and M, X and Z other
TERM_BY_SUFFIX: dict[str, TermCode] = {
    "A": "q1",
    "B": "q2",
    "C": "q3",
    "D": "q4",
    "F": "sem1",
    "S": "sem2",
    "H": "full_year",
    "W": "full_year",
    "L": "winter",
    "U": "summer",
    "J": "summer",
    "P": "summer",
    "M": "other",
    "X": "other",
    "Z": "other",
}

# What a result symbol means, as result_symbols.outcome allows
Outcome = Literal[
    "pass",
    "fail",
    "dp_refused",
    "supp_pending",
    "in_progress",
    "credited",
    "not_counted",
]

# A printed rule as a tree, in the seed's JSON shapes. Each node is told apart by its one
# distinctive key, as in {"any": [...]}, {"course": "EEE3091F", "need": "pass"} or {"refer": "..."}.
NODE_KEYS = (
    "all",
    "any",
    "course",
    "student_in",
    "min_year_of_study",
    "refer",
    "all_of_group",
    "choose",
    "credits",
    "total_credits",
)


def _node_key(node: Any) -> str | None:
    # A node's distinctive key, whether it arrives as JSON or as a built node. Anything else, such
    # as a bare course code where a leaf should be, has none, so the union refuses it.
    keys = node if isinstance(node, dict) else getattr(type(node), "model_fields", ())
    return next((key for key in NODE_KEYS if key in keys), None)


def _in_order[T: Row](children: tuple[T, ...]) -> tuple[T, ...]:
    # all and any don't depend on order, so their children are kept sorted: the same rule printed
    # in another order is then the same tree, and comparing years finds no change
    return tuple(sorted(children, key=lambda child: child.model_dump_json()))


# Codes or group keys whose printed order means nothing, kept sorted for the same reason
SortedNames = Annotated[
    tuple[str, ...], AfterValidator(lambda names: tuple(sorted(names)))
]


class AllOf(Row):
    all: Annotated[
        tuple["EntryRule", ...], Field(min_length=1), AfterValidator(_in_order)
    ]


class AnyOf(Row):
    any: Annotated[
        tuple["EntryRule", ...], Field(min_length=1), AfterValidator(_in_order)
    ]


class CourseNeed(Row):
    # A pass in the course, taking it alongside (a co-requisite), or a final mark of at least
    # min_mark in it, pass or not. "At least 45% for CSC2001F" is a mark leaf, and so is a printed
    # "pass with at least n%".
    course: str
    need: Literal["pass", "concurrent", "mark"]
    min_mark: int | None = Field(default=None, exclude_if=lambda mark: mark is None)

    @model_validator(mode="after")
    def min_mark_only_with_a_mark(self) -> Self:
        # The mark is the whole test of a mark leaf, and means nothing on the others
        if (self.need == "mark") != (self.min_mark is not None):
            raise ValueError(
                "min_mark is required with need 'mark' and refused with any other"
            )
        return self


class StudentIn(Row):
    student_in: SortedNames  # curriculum codes


class MinYearOfStudy(Row):
    min_year_of_study: int


class Refer(Row):
    # Printed text only a person can judge: the engine treats it as conditional, never as a fail
    refer: str


# What a student needs before taking a course
EntryRule = Annotated[
    Annotated[AllOf, Tag("all")]
    | Annotated[AnyOf, Tag("any")]
    | Annotated[CourseNeed, Tag("course")]
    | Annotated[StudentIn, Tag("student_in")]
    | Annotated[MinYearOfStudy, Tag("min_year_of_study")]
    | Annotated[Refer, Tag("refer")],
    Discriminator(_node_key),
]
AllOf.model_rebuild()
AnyOf.model_rebuild()


class AllOfGroup(Row):
    all_of_group: str


class ChooseFromGroup(Row):
    choose: int
    from_group: str


class CreditsFromGroups(Row):
    credits: int
    from_groups: SortedNames


class TotalCredits(Row):
    total_credits: int


# One of a curriculum's demands in a year of study
YearRule = Annotated[
    Annotated[AllOfGroup, Tag("all_of_group")]
    | Annotated[ChooseFromGroup, Tag("choose")]
    | Annotated[CreditsFromGroups, Tag("credits")]
    | Annotated[TotalCredits, Tag("total_credits")],
    Discriminator(_node_key),
]


class YearRules(Row):
    all: Annotated[tuple[YearRule, ...], Field(min_length=1), AfterValidator(_in_order)]


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
    rule: YearRules


class Course(Row):
    handbook_year: int
    code: str
    name: str
    credits: int
    nqf_level: int
    term: str
    entry_rule: EntryRule | None = None
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
    position: int  # its order in its source
    content: str


# Why the requirement grammar refused printed wording, so a model drafted its tree instead
RefusalCause = Literal[
    "refused_school_result",  # such as NSC Mathematics
    "refused_programme",  # a programme or degree the student must be on
    "refused_year_of_study",
    "refused_mark_threshold",  # such as "At least 45% for CSC2001F"
    "refused_or_equivalent",
    "refused_code_without_term",  # such as MAM1020, which doesn't say which term's course
    "refused_free_text",  # other words, such as a condition in prose
    "refused_punctuation",  # a semicolon or full stop that joins parts
    "refused_mixed_and_or",  # "and" and "or" with no brackets to group them
    "refused_other",  # codes and joins that don't form a requirement, such as an unclosed bracket
]

# Why a person had to review a change; a change accepted automatically has none. Like the elective
# tabs, the list lives only here, so a cause changes here, never in a migration.
DeltaFlag = (
    RefusalCause
    | Literal[
        "model_written",  # a model wrote it: an elective's summary or category
        "removed",  # in last year's approved rules, gone from this year's
        "not_printed",  # an equivalence no handbook prints
        "no_entry",  # a course a curriculum lists but the handbook never describes
        "check_failed",  # a check across the sources failed on it
    ]
)


class HandbookDelta(Row):
    handbook_year: int
    entity: str
    entity_key: str
    old_value: JsonValue = None
    new_value: JsonValue = None
    corrected_value: JsonValue = None
    approved: bool | None = None
    flag: DeltaFlag | None = None


class ResultSymbol(Row):
    # One of UCT's result symbols. Not tied to a year, so it isn't part of a RuleSet.
    symbol: str
    outcome: Outcome
    label: str


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


# Each table's primary key. A store skips a row whose key it already holds, and reads rows in key
# order, which gives every row one fixed place across pages
PRIMARY_KEYS: dict[str, tuple[str, ...]] = {
    "handbook_versions": ("year",),
    "curricula": ("handbook_year", "code"),
    "curriculum_rules": ("handbook_year", "curriculum_code", "year_of_study"),
    "courses": ("handbook_year", "code"),
    "course_groups": ("handbook_year", "group_key"),
    "course_group_members": ("handbook_year", "group_key", "course_code"),
    "equivalences": ("handbook_year", "course_code", "counts_as"),
    "timetable_slots": ("id",),
    "timetable_slot_curricula": ("slot_id", "curriculum_code"),
    "passages": ("id",),
    "handbook_deltas": ("handbook_year", "entity", "entity_key"),
}


def year_column(table: str) -> str:
    # handbook_versions names its year "year"; every other table "handbook_year"
    return "year" if table == "handbook_versions" else "handbook_year"
