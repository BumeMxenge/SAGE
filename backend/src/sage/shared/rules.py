# The rulebook as types: one per table row, named after its columns. The database enforces every
# rule on these rows except the elective tab, the delta flag and the shape of each rule tree, which
# only the backend checks.
from collections import defaultdict
from datetime import time
from functools import partial
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

from sage.shared.base import Row
from sage.shared.students import PlanCourse

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

# A printed rule as a tree, in the JSON shapes the snapshots store. Each node is told apart by its
# one distinctive key, as in {"any": [...]}, {"course": "EEE3091F", "need": "pass"} or
# {"refer": "..."}.
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


def _joined[T: Row](kind: str, children: tuple[T, ...]) -> tuple[T, ...]:
    # Nor do they depend on grouping: an all inside an all holds when its parts do, so its parts
    # join the outer one (E2's prompt.md, rule 10). Joining a requirement to a co-requisite nests
    # them, and a model may group by habit; flat, the same rule is the same tree however it was put
    # together. Each inner node was joined when it was validated, so one level is enough.
    return _in_order(
        tuple(part for child in children for part in getattr(child, kind, (child,)))
    )


def _only_child(node: Row) -> Row:
    # An all or an any with one child holds when that child does, so it is that child (E2's prompt.md,
    # rule 10). It runs on the union, as a model can't turn into another model. Each child was
    # unwrapped when it was validated, so a node left with one child here is the last to unwrap.
    children = getattr(node, "all", None) or getattr(node, "any", None) or ()
    return children[0] if len(children) == 1 else node


# Codes or group keys whose printed order means nothing, kept sorted for the same reason
SortedNames = Annotated[
    tuple[str, ...], AfterValidator(lambda names: tuple(sorted(names)))
]


class AllOf(Row):
    all: Annotated[
        tuple["EntryRule", ...],
        Field(min_length=1),
        AfterValidator(partial(_joined, "all")),
    ]


class AnyOf(Row):
    any: Annotated[
        tuple["EntryRule", ...],
        Field(min_length=1),
        AfterValidator(partial(_joined, "any")),
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
    AfterValidator(_only_child),
]
AllOf.model_rebuild()
AnyOf.model_rebuild()


def continues(node: EntryRule) -> bool:
    # Printed words that only continue the list before them, such as "or equivalent", and so read
    # only with that list
    return isinstance(node, Refer) and node.refer.startswith("or ")


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


# The group of a year's approved complementary studies courses, which every curriculum's
# complementary credits come from
COMPLEMENTARY = "complementary"


# The Explore Electives tabs: the one list a member's category comes from, which the frontend reads
# and the backend checks every category against, so a tab changes here, never in a migration
ElectiveTab = Literal[
    "arts",
    "business",
    "econ",
    "ethics",
    "history",
    "languages",
    "literature",
    "logic",
    "media",
    "religion",
    "science",
    "society",
]


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


# The tables a change can be in, as handbook_deltas.entity's check in the rule-tables migration allows
DeltaTable = Literal[
    "curricula",
    "curriculum_rules",
    "courses",
    "course_groups",
    "course_group_members",
    "equivalences",
]


class HandbookDelta(Row):
    handbook_year: int
    entity: DeltaTable
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


def meetings_on(
    rules: RuleSet, curriculum: str, course_code: str
) -> list[TimetableSlot]:
    # A course's meetings on one curriculum's timetable: a meeting linked to curricula is theirs
    # alone
    only_for: dict[UUID, set[str]] = defaultdict(set)
    for link in rules.timetable_slot_curricula:
        only_for[link.slot_id].add(link.curriculum_code)
    return [
        slot
        for slot in rules.timetable_slots
        if slot.course_code == course_code
        and (slot.id not in only_for or curriculum in only_for[slot.id])
    ]


def meetings(
    course: PlanCourse, rules: RuleSet, curriculum: str
) -> list[TimetableSlot]:
    # The meetings she attends: the compulsory ones, and each alternative of a choice group that
    # fits her plan, or every alternative of a group her plan doesn't record
    chosen = course.choices or {}
    attended = [
        slot
        for slot in meetings_on(rules, curriculum, course.course_code)
        if slot.choice_group not in chosen or slot.choice in chosen[slot.choice_group]
    ]
    # Unknown days and times last
    return sorted(
        attended,
        key=lambda slot: (
            slot.day or 8,
            slot.start_time or time.max,
            slot.choice or "",
        ),
    )


# Each table's primary key. The fake keys its rows by it, and a store reads rows in key order,
# which gives every row one fixed place across pages
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
