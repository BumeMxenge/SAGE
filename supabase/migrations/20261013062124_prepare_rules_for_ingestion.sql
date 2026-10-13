-- Readies the rule tables for handbook ingestion. A delta records why a person had to review it, a
-- passage keeps its place in its source, and passages lose their embeddings, because the advisor is
-- handed the passages for a student's courses instead of searching them by meaning. The tables'
-- existing grants and policies cover the new columns.

-- why a person had to review this change; null = accepted automatically. The backend holds the
-- allowed values, so a new cause needs no migration.
alter table public.handbook_deltas add column flag text;

-- the unit's order in its source, so a year's passages read back in printed order. No database
-- holds a passage yet, so the column needs no default.
alter table public.passages add column position integer not null;
alter table public.passages add unique (handbook_year, source, position);

-- the column goes first, as its type comes from the extension
alter table public.passages drop column embedding;
drop extension vector;
