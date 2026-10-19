# Checks the rulebook cache: a year is read once and reused for ten minutes, read again after that,
# and a year that isn't there is the rulebook_not_loaded refusal rather than an empty rulebook
import pytest

from sage.shared.errors import RulebookNotLoaded
from sage.shared.memory.rules import InMemoryRuleRepository
from sage.shared.rulebook import TIME_LIMIT, Rulebook


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
