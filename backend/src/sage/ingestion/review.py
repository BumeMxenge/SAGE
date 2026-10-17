# An approved handbook year as data/rules/<year>/rulebook.json holds it: every row sage load writes,
# and where each was printed, which the next year reads to carry over what it prints unchanged.
from sage.domain.base import Row
from sage.domain.rules import RuleSet
from sage.ingestion.sources import Reading


class Snapshot(Row):
    rules: RuleSet
    readings: tuple[Reading, ...]

    @property
    def year(self) -> int:
        return self.rules.handbook_versions[0].year
