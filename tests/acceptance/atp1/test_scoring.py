# Checks ATP-1's scoring rules with values worked out by hand from the Scoring section and the
# decisions at the harness's Stop 1. No test reads a source or calls a model.
import json
import re

import pytest
from scoring import (
    ACCEPTED,
    BOOKS,
    REVIEWED,
    WORKBOOK_DAYS,
    bound,
    by_cell,
    course_changes,
    course_review,
    day_name,
    joined,
    wilson,
    within,
)

from sage.ingestion.timetable import DAYS as SHEET_DAYS
from sage.ingestion.timetable import Printed
from sage.shared.rules import HandbookDelta

# Made-up codes, as in the labels README's examples
A = {"course": "ABC1001F", "need": "pass"}
B = {"course": "ABC1002S", "need": "pass"}
CO = {"course": "XYZ1003F", "need": "concurrent"}


@pytest.mark.parametrize(
    ("requirement", "corequisite", "rule"),
    [
        (json.dumps(A), None, A),
        (json.dumps(A), json.dumps(CO), {"all": [A, CO]}),
        # A blank or null tree adds nothing, so the other stands alone
        ("null", json.dumps(CO), CO),
        ("null", None, None),
    ],
)
def test_a_labels_two_trees_are_one_rule(requirement, corequisite, rule):
    assert joined(requirement, corequisite) == rule


@pytest.mark.parametrize(
    ("page", "pages", "inside"),
    [
        (58, "58", True),
        (59, "58", False),
        (59, "58–59", True),
        (57, "58–59", False),
        (60, "58–59", False),
        (247, "153, 247", True),
        (200, "153, 247", False),
    ],
)
def test_a_page_falls_within_the_workbooks_printed_pages(page, pages, inside):
    assert within(page, pages) is inside


def test_each_cover_title_maps_to_its_own_faculty_s_book():
    # The workbook's name for a handbook names its faculty, as the cover title does, so a swapped
    # pair fails, and no two cover titles map to one book
    for cover, name in BOOKS.items():
        faculty = re.search(r"Faculty of .+?(?= Undergraduate| Handbook)", name)[0]
        assert faculty in cover
    assert len(set(BOOKS.values())) == len(BOOKS)


def test_the_workbooks_days_and_the_readers_day_numbers_name_the_same_days():
    # The workbook writes mon to sun, and the timetable reader numbers Monday 1
    assert [WORKBOOK_DAYS[day] for day in ("mon", "thu", "sun")] == [
        "Monday",
        "Thursday",
        "Sunday",
    ]
    for name in ("Monday", "Thursday", "Friday"):
        assert day_name(SHEET_DAYS[name.upper()]) == name


def test_a_merged_block_is_found_by_its_first_cell_only():
    def printed(sheet: str, cells: str) -> Printed:
        return Printed(
            sheet=sheet,
            cells=cells,
            codes=("ABC1001F",),
            year=1,
            semester="sem1",
            day=1,
            first="1",
            last="2",
        )

    block, single = printed("EB009", "C7:C8"), printed("Labs", "D5")
    cells = by_cell([block, single])
    assert cells["EB009", "C7"] is block
    assert ("EB009", "C8") not in cells
    assert cells["Labs", "D5"] is single


@pytest.mark.parametrize(
    ("k", "n", "low", "high"),
    [
        # p = 0.5, z² = 3.8415 and the scale 1 + z²/n = 1.38415. The centre is
        # (0.5 + 0.19207) / 1.38415 = 0.5, and the half-width 1.96 × √(0.025 + 0.0096) / 1.38415
        # = 0.2634
        (5, 10, 0.2366, 0.7634),
        # The centre and the half-width are both 0.19207 / 1.38415 = 0.1388
        (0, 10, 0.0, 0.2775),
        (10, 10, 0.7225, 1.0),
    ],
)
def test_the_wilson_interval(k, n, low, high):
    assert wilson(k, n) == pytest.approx((low, high), abs=1e-4)


def test_the_bound_when_nothing_is_wrong():
    # 1 − 0.05^(1/59): 0.05^(1/59) = e^(−2.9957/59) = 0.9505, so 0.0495
    assert bound(0, 59) == pytest.approx(0.0495, abs=1e-4)


def test_one_wrong_has_no_bound():
    assert bound(1, 59) is None


@pytest.mark.parametrize(
    ("field", "decided", "unchanged", "decided_before", "status"),
    [
        # No review row shows a title, credits, an NQF level or a term, even on a decided course
        ("title", True, False, False, ACCEPTED),
        ("term", True, True, True, ACCEPTED),
        # A rule shown in a row decided this year, or in 2023 and unchanged since
        ("entry_rule", True, False, False, REVIEWED),
        ("entry_rule", False, True, True, REVIEWED),
        ("requirement", False, True, True, REVIEWED),
        # Changed since its 2023 decision, or unchanged but never decided
        ("entry_rule", False, False, True, ACCEPTED),
        ("entry_rule", False, True, False, ACCEPTED),
        # A page belongs to its year's book, so only that year's decision covers it
        ("page", True, False, False, REVIEWED),
        ("page", False, True, True, ACCEPTED),
    ],
)
def test_a_field_counts_as_reviewed_only_where_a_decided_row_showed_it(
    field, decided, unchanged, decided_before, status
):
    assert course_review(field, decided, unchanged, decided_before) == status


def labels(
    requirement: str = "ABC1001F", tree: dict = A, title: str = "Signals I", note=None
) -> dict:
    # A course sheet's row for the made-up ABC2001S
    return {
        "Code": "ABC2001S",
        "Page": 100,
        "Title": title,
        "Credits": "16",
        "NQF level": "6",
        "Term": "sem2",
        "Requirement": requirement,
        "Requirement tree": json.dumps(tree),
        "Co-requisite": None,
        "Co-requisite tree": None,
        "Note": note,
    }


def stored(rule: dict) -> dict:
    # ABC2001S as SAGE stores it
    return {
        "code": "ABC2001S",
        "name": "Signals I",
        "credits": 16,
        "nqf_level": 6,
        "term": "sem2",
        "entry_rule": rule,
    }


def delta(old: dict | None, new: dict | None, flag: str | None) -> HandbookDelta:
    return HandbookDelta(
        handbook_year=2026,
        entity="courses",
        entity_key="ABC2001S",
        old_value=old,
        new_value=new,
        flag=flag,
    )


@pytest.mark.parametrize(
    ("before", "after", "found", "expected"),
    [
        # A changed rule is recalled when a delta records it, flagged or not, and missed without one
        (
            labels(),
            labels("ABC1002S", B),
            delta(stored(A), stored(B), None),
            [("entry_rule", "changed", "recalled")],
        ),
        (labels(), labels("ABC1002S", B), None, [("entry_rule", "changed", "missed")]),
        # A delta that records another field doesn't recall the rule's change
        (
            labels(),
            labels("ABC1002S", B),
            delta(stored(A), stored(A) | {"credits": 12}, None),
            [("entry_rule", "changed", "missed")],
        ),
        # Flagged, though the rule is the same in another order: the wording changed
        (
            labels("ABC1001F or ABC1002S", {"any": [A, B]}),
            labels("ABC1002S or ABC1001F", {"any": [B, A]}),
            delta(stored({"refer": "x"}), stored({"refer": "y"}), "refused_free_text"),
            [("entry_rule", "none", "wording change")],
        ),
        # Flagged, though neither the rule nor the wording changed, and a title in other capitals
        # is the same title
        (
            labels(),
            labels(title="SIGNALS I"),
            delta(stored(A), stored({"refer": "ABC1001F"}), "refused_free_text"),
            [("entry_rule", "none", "false alarm")],
        ),
        # Nothing labelled and nothing flagged
        (labels(), labels(), delta(stored(A), stored(A) | {"credits": 12}, None), []),
        # A course one year prints and the other doesn't
        (
            labels(),
            None,
            delta(stored(A), None, "removed"),
            [("course", "removed", "recalled")],
        ),
        (
            labels(),
            labels(note="no entry printed"),
            None,
            [("course", "removed", "missed")],
        ),
        # SAGE flagging the removal of a course both years print
        (
            labels(),
            labels(),
            delta(stored(A), None, "removed"),
            [("course", "none", "false alarm")],
        ),
    ],
)
def test_a_change_counts_by_what_the_labels_show(before, after, found, expected):
    rows = course_changes("ABC2001S", before, after, found)
    assert [(row["field"], row["change"], row["outcome"]) for row in rows] == expected
