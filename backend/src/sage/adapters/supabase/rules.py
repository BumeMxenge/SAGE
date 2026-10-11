# The rulebook in Supabase, written and read with the secret key
from supabase import Client

from sage.adapters.supabase.tables import insert, row_type, select
from sage.domain.rules import RuleSet

# The columns each table is read in order of, in the foreign-key order RuleSet lists them
ORDER = {
    "handbook_versions": ("year",),
    "curricula": ("code",),
    "curriculum_rules": ("curriculum_code", "year_of_study"),
    "courses": ("code",),
    "course_groups": ("group_key",),
    "course_group_members": ("group_key", "course_code"),
    "equivalences": ("course_code", "counts_as"),
    "timetable_slots": ("id",),
    "timetable_slot_curricula": ("slot_id", "curriculum_code"),
    "passages": ("id",),
    "handbook_deltas": ("entity", "entity_key"),
}


class SupabaseRuleRepository:
    def __init__(self, client: Client) -> None:
        self._client = client

    def add_missing(self, rules: RuleSet) -> None:
        for table in ORDER:
            insert(self._client, table, getattr(rules, table), skip_existing=True)

    def get(self, year: int) -> RuleSet:
        def rows(table: str, order: tuple[str, ...]):
            # handbook_versions names its year "year"; every other table "handbook_year"
            column = "year" if table == "handbook_versions" else "handbook_year"
            model = row_type(RuleSet, table)
            return select(self._client, table, model, column, year, order)

        return RuleSet(**{table: rows(table, order) for table, order in ORDER.items()})
