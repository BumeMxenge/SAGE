# The rulebook as the API reads it, kept in memory. A year only changes when it's loaded or approved,
# so each read is reused for ten minutes: a change shows up within that time with no redeploy, and a
# busy registration week reads each year a few times an hour instead of on every request.
import time
from collections.abc import Callable
from typing import Any

from sage.shared.errors import RulebookNotLoaded
from sage.shared.repositories import RuleRepository
from sage.shared.rules import ResultSymbol, RuleSet

TIME_LIMIT = 600  # seconds, the same as supabase-auth keeps the token signing keys


class Rulebook:
    def __init__(
        self, rules: RuleRepository, clock: Callable[[], float] = time.monotonic
    ) -> None:
        self._rules = rules
        self._clock = clock
        self._kept: dict[object, tuple[float, Any]] = {}

    def current_year(self) -> int:
        # The latest approved handbook year
        year = self._keep("current year", self._rules.current_year)
        if year is None:
            raise RulebookNotLoaded()
        return year

    def year(self, year: int) -> RuleSet:
        rules = self._keep(year, lambda: self._rules.get(year))
        if not rules.handbook_versions:
            raise RulebookNotLoaded(f"The {year} handbook rules aren't loaded.")
        return rules

    def current(self) -> RuleSet:
        return self.year(self.current_year())

    def symbols(self) -> dict[str, ResultSymbol]:
        return self._keep(
            "symbols", lambda: {row.symbol: row for row in self._rules.symbols()}
        )

    def _keep[T](self, key: object, read: Callable[[], T]) -> T:
        kept = self._kept.get(key)
        if kept is None or self._clock() - kept[0] >= TIME_LIMIT:
            kept = self._kept[key] = (self._clock(), read())
        return kept[1]
