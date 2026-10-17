# The rulebook in Supabase
from postgrest import APIError
from supabase import Client

from sage.adapters.supabase.tables import (
    FOREIGN_KEY_VIOLATION,
    columns,
    insert,
    row_type,
    select,
)
from sage.domain.repositories import YearInUse
from sage.domain.rules import PRIMARY_KEYS, ResultSymbol, RuleSet, year_column


class SupabaseRuleRepository:
    def __init__(self, client: Client) -> None:
        self._client = client

    def add_missing(self, rules: RuleSet) -> None:
        # In RuleSet's foreign-key order
        for table in RuleSet.model_fields:
            insert(self._client, table, getattr(rules, table), skip_existing=True)

    def replace_year(self, rules: RuleSet) -> None:
        (version,) = rules.handbook_versions
        try:
            # Every row of the year cascades from its version, unless a student's row uses it
            self._client.table("handbook_versions").delete().eq(
                "year", version.year
            ).execute()
        except APIError as error:
            if error.code == FOREIGN_KEY_VIOLATION:
                raise YearInUse(version.year) from error
            raise
        # The year stays unapproved until every row is in, so one that fails partway is never
        # served, and loading it again replaces it
        insert(
            self._client,
            "handbook_versions",
            [version.model_copy(update={"approved": False})],
        )
        for table in list(RuleSet.model_fields)[1:]:
            insert(self._client, table, getattr(rules, table))
        if version.approved:
            self._client.table("handbook_versions").update({"approved": True}).eq(
                "year", version.year
            ).execute()

    def get(self, year: int) -> RuleSet:
        def rows(table: str):
            model, column = row_type(RuleSet, table), year_column(table)
            return select(self._client, table, model, column, year, PRIMARY_KEYS[table])

        return RuleSet(**{table: rows(table) for table in RuleSet.model_fields})

    def current_year(self) -> int | None:
        rows = (
            self._client.table("handbook_versions")
            .select("year")
            .eq("approved", True)
            .order("year", desc=True)
            .limit(1)
            .execute()
            .data
        )
        return rows[0]["year"] if rows else None

    def symbols(self) -> tuple[ResultSymbol, ...]:
        rows = (
            self._client.table("result_symbols")
            .select(columns(ResultSymbol))
            .order("symbol")
            .execute()
            .data
        )
        return tuple(ResultSymbol.model_validate(row) for row in rows)
