# Checks the rulebook cache: a year is read once and reused for ten minutes, read again after that,
# and a year that isn't there is the rulebook_not_loaded refusal rather than an empty rulebook. Each
# year comes with the meetings its course entries print, once.
import pytest

from sage.shared.errors import RulebookNotLoaded
from sage.shared.memory.rules import InMemoryRuleRepository
from sage.shared.printed_meetings import timetabled
from sage.shared.rulebook import TIME_LIMIT, Rulebook
from sage.shared.rules import HandbookVersion, RuleSet


class CountingRules(InMemoryRuleRepository):
    # Counts how often the cache really reads a year
    def __init__(self) -> None:
        super().__init__()
        self.reads = 0

    def get(self, year: int):
        self.reads += 1
        return super().get(year)


class Clock:
    # Time that only moves when a test moves it
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def rules(approved_2026) -> CountingRules:
    rules = CountingRules()
    rules.replace_year(approved_2026)
    return rules


def test_a_year_is_reused_until_the_time_limit(rules):
    clock = Clock()
    rulebook = Rulebook(rules, clock)
    first = rulebook.current()
    clock.now = TIME_LIMIT - 1
    assert rulebook.current() is first
    assert rules.reads == 1
    clock.now = TIME_LIMIT
    rulebook.current()
    assert rules.reads == 2


def test_no_approved_year_means_no_rulebook():
    with pytest.raises(RulebookNotLoaded):
        Rulebook(InMemoryRuleRepository()).current_year()


def test_a_year_that_isnt_stored_means_no_rulebook(rules):
    with pytest.raises(RulebookNotLoaded, match="2031"):
        Rulebook(rules).year(2031)


def test_a_year_holds_the_meetings_its_course_entries_print_once(rules):
    # CSC3002F's entry prints two practicals a week on two weekdays a plan picks (p. 171), which the
    # department's timetable leaves out, holding only its lectures: one alternative for each of the
    # ten pairs of weekdays, two meetings each
    year = Rulebook(rules).year(2026)
    practicals = [
        s
        for s in year.timetable_slots
        if s.course_code == "CSC3002F" and s.kind == "practical"
    ]
    assert len(practicals) == 20
    assert timetabled(year).timetable_slots == year.timetable_slots


def test_a_year_whose_entries_print_no_meetings_is_left_as_it_is():
    # 2023's entries print none that its rules lack
    rules = RuleSet(handbook_versions=(HandbookVersion(year=2023, approved=True),))
    assert timetabled(rules) == rules
