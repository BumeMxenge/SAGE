# Checks the elective tab list is the backend's one check on categories, now the database has none
from typing import get_args

import pytest
from pydantic import ValidationError

from sage.domain.electives import ElectiveTab
from sage.domain.rules import CourseGroupMember


def member(category: str | None) -> CourseGroupMember:
    return CourseGroupMember(
        handbook_year=2026,
        group_key="complementary",
        course_code="AGE1002S",
        category=category,
    )


def test_the_twelve_prototype_tabs():
    assert len(get_args(ElectiveTab)) == 12
    assert member("science").category == "science"


def test_a_list_other_than_complementary_has_no_category():
    assert member(None).category is None


def test_an_unknown_tab_is_refused():
    with pytest.raises(ValidationError):
        member("cooking")
