# The rulebook in one dictionary per table, keyed like the table's primary key
from collections.abc import Callable
from typing import Any

from sage.domain.rules import RuleSet

# Each table's primary key, so add_missing can tell which rows are already stored
_KEYS: dict[str, Callable[[Any], tuple[Any, ...]]] = {
    "handbook_versions": lambda row: (row.year,),
    "curricula": lambda row: (row.handbook_year, row.code),
    "curriculum_rules": lambda row: (
        row.handbook_year,
        row.curriculum_code,
        row.year_of_study,
    ),
    "courses": lambda row: (row.handbook_year, row.code),
    "course_groups": lambda row: (row.handbook_year, row.group_key),
    "course_group_members": lambda row: (
        row.handbook_year,
        row.group_key,
        row.course_code,
    ),
    "equivalences": lambda row: (row.handbook_year, row.course_code, row.counts_as),
    "timetable_slots": lambda row: (row.id,),
    "timetable_slot_curricula": lambda row: (row.slot_id, row.curriculum_code),
    "passages": lambda row: (row.id,),
    "handbook_deltas": lambda row: (row.handbook_year, row.entity, row.entity_key),
}


class InMemoryRuleRepository:
    def __init__(self) -> None:
        self._tables: dict[str, dict[tuple[Any, ...], Any]] = {
            table: {} for table in RuleSet.model_fields
        }

    def add_missing(self, rules: RuleSet) -> None:
        for table, stored in self._tables.items():
            for row in getattr(rules, table):
                stored.setdefault(_KEYS[table](row), row)

    def get(self, year: int) -> RuleSet:
        def in_year(row: Any) -> bool:
            # handbook_versions names its year "year"; every other table "handbook_year"
            return getattr(row, "handbook_year", getattr(row, "year", None)) == year

        return RuleSet(
            **{
                table: tuple(row for row in stored.values() if in_year(row))
                for table, stored in self._tables.items()
            }
        )
