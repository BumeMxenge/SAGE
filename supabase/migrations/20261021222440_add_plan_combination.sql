-- A plan's electives' codes, which the planner prints under its name, as the prototype does. The
-- engine writes it with each new set. No stored plan is backfilled, as every stored plan set is
-- development data: generating or seeding a set again fills it. The table's existing grants and
-- policy cover the column.
alter table public.plans add column combination text;

comment on column public.plans.combination is
  'The plan''s electives'' codes in code order, joined with " · ", such as "EEE4117F · EEE4118F · EEE4119F". Null = no electives.';
