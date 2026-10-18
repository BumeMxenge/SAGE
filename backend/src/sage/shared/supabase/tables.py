# What both Supabase repositories do to a table: write rows of a domain type, and read them back
from collections.abc import Sequence
from typing import Any, get_args

from postgrest import ReturnMethod
from pydantic import BaseModel
from supabase import Client

PAGE = 1000  # the most rows the Data API returns per request (max_rows)
BATCH = 500  # rows per write, so no single request grows too large
# Postgres refusing a row that points at one that isn't there, or a removal another row needs
FOREIGN_KEY_VIOLATION = "23503"


def columns(model: type[BaseModel]) -> str:
    # A select list naming exactly the type's columns
    return ",".join(model.model_fields)


def row_type(container: type[BaseModel], field: str) -> type[BaseModel]:
    # The row type inside a field such as `courses: tuple[Course, ...]`
    return get_args(container.model_fields[field].annotation)[0]


def insert(
    client: Client,
    table: str,
    rows: Sequence[BaseModel],
    *,
    skip_existing: bool = False,
) -> None:
    payload = [row.model_dump(mode="json") for row in rows]
    for start in range(0, len(payload), BATCH):
        batch, query = payload[start : start + BATCH], client.table(table)
        if skip_existing:
            # INSERT ... ON CONFLICT DO NOTHING on the primary key
            query.upsert(
                batch, ignore_duplicates=True, returning=ReturnMethod.minimal
            ).execute()
        else:
            query.insert(batch, returning=ReturnMethod.minimal).execute()


def select[T: BaseModel](
    client: Client,
    table: str,
    model: type[T],
    column: str,
    value: Any,
    order: Sequence[str],
) -> tuple[T, ...]:
    # Only the type's columns, a page at a time, in a fixed order so the pages don't overlap
    rows: list[dict[str, Any]] = []
    while True:
        query = client.table(table).select(columns(model)).eq(column, value)
        for name in order:
            query = query.order(name)
        page = query.range(len(rows), len(rows) + PAGE - 1).execute().data
        rows.extend(page)
        if len(page) < PAGE:
            return tuple(model.model_validate(row) for row in rows)
