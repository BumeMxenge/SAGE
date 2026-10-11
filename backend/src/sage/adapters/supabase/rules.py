# The rulebook in Supabase
from supabase import Client

from sage.adapters.supabase.tables import insert, row_type, select
from sage.domain.rules import PRIMARY_KEYS, RuleSet, year_column


class SupabaseRuleRepository:
    def __init__(self, client: Client) -> None:
        self._client = client

    def add_missing(self, rules: RuleSet) -> None:
        # In RuleSet's foreign-key order
        for table in RuleSet.model_fields:
            insert(self._client, table, getattr(rules, table), skip_existing=True)

    def get(self, year: int) -> RuleSet:
        def rows(table: str):
            model, column = row_type(RuleSet, table), year_column(table)
            return select(self._client, table, model, column, year, PRIMARY_KEYS[table])

        return RuleSet(**{table: rows(table) for table in RuleSet.model_fields})
