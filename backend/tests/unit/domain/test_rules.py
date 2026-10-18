# Checks the rule trees' shapes: a tree that doesn't fit is refused, an any needs a child, a rule
# printed in another order is the same tree, and so is one grouped differently within its own kind
# or wrapped in an all or an any of one. An Explore Electives tab must be one the frontend has.
import pytest
from pydantic import TypeAdapter, ValidationError

from sage.shared.rules import AllOf, Course, CourseGroupMember, CourseNeed, EntryRule

ENTRY_RULE = TypeAdapter(EntryRule)


@pytest.mark.parametrize(
    "tree",
    [
        {"courses": "EEE3091F", "need": "pass"},  # a misspelt key
        {"any": ["EEE3091F", "EEE3092F"]},  # codes where leaves should be
        {"course": "EEE3091F", "need": "dp"},  # a need outside the set
        {"course": "EEE3091F", "need": "pass", "refer": "Or"},  # an extra key
        {"course": "CSC2001F", "need": "mark"},  # a mark leaf without its mark
        {"course": "EEE3091F", "need": "pass", "min_mark": 50},  # a pass leaf with one
    ],
)
def test_a_malformed_tree_is_refused(tree):
    with pytest.raises(ValidationError):
        ENTRY_RULE.validate_python(tree)


def test_an_all_or_an_any_needs_a_child():
    # An empty one could never hold, or always would, so it is refused. One child is the next test.
    for kind in ("all", "any"):
        with pytest.raises(ValidationError):
            ENTRY_RULE.validate_python({kind: []})


def test_a_rule_printed_in_another_order_is_the_same_tree():
    # EEE4113F's "EEE3097S or EEE3098S or EEE3099S", PHY2010S's co-requisite "MAM2084F/S",
    # CSC2002S's "At least 45% for CSC2001F" and two curricula, none of them in sorted order
    printed = {
        "all": [
            {"student_in": ["EB011EEE05", "EB009EEE01"]},
            {"course": "CSC2001F", "need": "mark", "min_mark": 45},
            {
                "any": [
                    {"course": "MAM2084S", "need": "concurrent"},
                    {"course": "MAM2084F", "need": "concurrent"},
                ]
            },
            {
                "any": [
                    {"course": "EEE3099S", "need": "pass"},
                    {"course": "EEE3097S", "need": "pass"},
                    {"course": "EEE3098S", "need": "pass"},
                ]
            },
        ]
    }
    # Sorted by hand on each node's JSON text: "any" before "course" before "student_in", the two
    # anys by their first code, and the codes alphabetically. Only the mark leaf has a min_mark.
    expected = {
        "all": [
            {
                "any": [
                    {"course": "EEE3097S", "need": "pass"},
                    {"course": "EEE3098S", "need": "pass"},
                    {"course": "EEE3099S", "need": "pass"},
                ]
            },
            {
                "any": [
                    {"course": "MAM2084F", "need": "concurrent"},
                    {"course": "MAM2084S", "need": "concurrent"},
                ]
            },
            {"course": "CSC2001F", "need": "mark", "min_mark": 45},
            {"student_in": ["EB009EEE01", "EB011EEE05"]},
        ]
    }
    tree = ENTRY_RULE.validate_python(printed)
    assert ENTRY_RULE.dump_python(tree, mode="json") == expected


def leaf(code, need="pass"):
    return {"course": code, "need": need}


def test_an_all_inside_an_all_is_the_same_tree_as_one_all():
    # PHY2010S's requirement joined to its co-requisite "MAM2084F/S", as the ingest joins them: an
    # all holding an all. E2's prompt.md rule 10 says to join them, and a model may group either way.
    requirement = {
        "all": [
            {"any": [leaf("PHY1012F"), leaf("PHY1012S")]},
            {"any": [leaf("MAM2083F"), leaf("MAM2083S")]},
        ]
    }
    corequisite = {
        "any": [leaf("MAM2084F", "concurrent"), leaf("MAM2084S", "concurrent")]
    }
    joined = ENTRY_RULE.validate_python({"all": [requirement, corequisite]})
    flat = ENTRY_RULE.validate_python({"all": [*requirement["all"], corequisite]})
    assert joined == flat
    # Sorted by hand as above: the three anys by their first code, MAM2083F, MAM2084F, PHY1012F
    assert ENTRY_RULE.dump_python(joined, mode="json") == {
        "all": [
            {"any": [leaf("MAM2083F"), leaf("MAM2083S")]},
            {"any": [leaf("MAM2084F", "concurrent"), leaf("MAM2084S", "concurrent")]},
            {"any": [leaf("PHY1012F"), leaf("PHY1012S")]},
        ]
    }


def test_an_any_inside_an_any_joins_however_deep():
    nested = {
        "any": [
            leaf("EEE3097S"),
            {"any": [leaf("EEE3098S"), {"any": [leaf("EEE3099S")]}]},
        ]
    }
    assert ENTRY_RULE.dump_python(ENTRY_RULE.validate_python(nested), mode="json") == {
        "any": [leaf("EEE3097S"), leaf("EEE3098S"), leaf("EEE3099S")]
    }


def test_an_all_and_an_any_inside_each_other_stay_apart():
    # Joining only holds within a kind: "A and (B or C)" is not "A and B and C", nor is
    # "A or (B and C)" "A or B or C". Each node's children are only sorted, "all" and "any" before
    # "course" by their JSON text.
    b_or_c = {"any": [leaf("EEE3098S"), leaf("EEE3099S")]}
    b_and_c = {"all": [leaf("EEE3098S"), leaf("EEE3099S")]}
    for kind, inner in (("all", b_or_c), ("any", b_and_c)):
        tree = ENTRY_RULE.validate_python({kind: [leaf("EEE3097S"), inner]})
        assert ENTRY_RULE.dump_python(tree, mode="json") == {
            kind: [inner, leaf("EEE3097S")]
        }


@pytest.mark.parametrize(
    "tree",
    [
        {"all": [leaf("EEE3091F")]},
        {"any": [leaf("EEE3091F")]},
        # Wrapped twice, and in the other kind
        {"all": [{"any": [leaf("EEE3091F")]}]},
        {"any": [{"all": [{"any": [leaf("EEE3091F")]}]}]},
    ],
)
def test_an_all_or_an_any_of_one_is_that_one(tree):
    # E2's prompt.md rule 10: "A" wrapped in an all or an any is just A
    assert ENTRY_RULE.dump_python(
        ENTRY_RULE.validate_python(tree), mode="json"
    ) == leaf("EEE3091F")


def test_unwrapping_and_joining_work_together():
    # "A or (all of (any of (C or D)))": the middle any joins its own child, C or D. The all of one
    # around it unwraps to that any, and that any then joins the outer one, as both are anys.
    c_or_d = {"any": [leaf("EEE3098S"), leaf("EEE3099S")]}
    tree = {"any": [leaf("EEE3097S"), {"all": [{"any": [c_or_d]}]}]}
    assert ENTRY_RULE.dump_python(ENTRY_RULE.validate_python(tree), mode="json") == {
        "any": [leaf("EEE3097S"), leaf("EEE3098S"), leaf("EEE3099S")]
    }


def test_a_rule_built_with_one_child_is_stored_without_the_wrapper():
    # How the ingest builds a course's rule: as an object, before it goes into the course
    need = CourseNeed(course="EEE3091F", need="pass")
    course = Course(
        handbook_year=2026,
        code="EEE3092F",
        name="Made Up",
        credits=8,
        nqf_level=7,
        term="sem1",
        entry_rule=AllOf(all=(need,)),
    )
    assert course.entry_rule == need


def test_an_unknown_tab_is_refused():
    with pytest.raises(ValidationError):
        CourseGroupMember(
            handbook_year=2026,
            group_key="complementary",
            course_code="SLL1052F",
            category="cooking",
        )
