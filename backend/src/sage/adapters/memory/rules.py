# The rulebook in one dictionary per table, keyed like the table's primary key
from typing import Any

from sage.domain.rules import PRIMARY_KEYS, ResultSymbol, RuleSet, year_column


class InMemoryRuleRepository:
    def __init__(self, symbols: tuple[ResultSymbol, ...] = ()) -> None:
        self._tables: dict[str, dict[tuple[Any, ...], Any]] = {
            table: {} for table in RuleSet.model_fields
        }
        # A migration stores the real symbols, so a fake is handed them
        self._symbols = symbols

    def add_missing(self, rules: RuleSet) -> None:
        for table, stored in self._tables.items():
            for row in getattr(rules, table):
                key = tuple(getattr(row, column) for column in PRIMARY_KEYS[table])
                stored.setdefault(key, row)

    def replace_year(self, rules: RuleSet) -> None:
        # The fake holds no student rows, so nothing here refuses the removal
        (version,) = rules.handbook_versions
        for table, stored in self._tables.items():
            column = year_column(table)
            for key in [
                k for k, row in stored.items() if getattr(row, column) == version.year
            ]:
                del stored[key]
        self.add_missing(rules)

    def get(self, year: int) -> RuleSet:
        def in_year(table: str, row: Any) -> bool:
            return getattr(row, year_column(table)) == year

        return RuleSet(
            **{
                table: tuple(row for row in stored.values() if in_year(table, row))
                for table, stored in self._tables.items()
            }
        )

    def current_year(self) -> int | None:
        versions = self._tables["handbook_versions"].values()
        return max((row.year for row in versions if row.approved), default=None)

    def symbols(self) -> tuple[ResultSymbol, ...]:
        return tuple(sorted(self._symbols, key=lambda row: row.symbol))
