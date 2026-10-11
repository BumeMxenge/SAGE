# The rulebook in one dictionary per table, keyed like the table's primary key
from typing import Any

from sage.domain.rules import PRIMARY_KEYS, RuleSet, year_column


class InMemoryRuleRepository:
    def __init__(self) -> None:
        self._tables: dict[str, dict[tuple[Any, ...], Any]] = {
            table: {} for table in RuleSet.model_fields
        }

    def add_missing(self, rules: RuleSet) -> None:
        for table, stored in self._tables.items():
            for row in getattr(rules, table):
                key = tuple(getattr(row, column) for column in PRIMARY_KEYS[table])
                stored.setdefault(key, row)

    def get(self, year: int) -> RuleSet:
        def in_year(table: str, row: Any) -> bool:
            return getattr(row, year_column(table)) == year

        return RuleSet(
            **{
                table: tuple(row for row in stored.values() if in_year(table, row))
                for table, stored in self._tables.items()
            }
        )
