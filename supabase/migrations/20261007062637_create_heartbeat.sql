-- A one-row table that .github/workflows/keep-alive.yml reads a few times a day.
-- Supabase pauses a free project after a week without database activity, and this read counts.

create table public.heartbeat (
  id smallint primary key default 1 check (id = 1), -- the check allows only one row
  note text not null
);

comment on table public.heartbeat is
  'Read by the keep-alive workflow so the free-tier project is never paused for inactivity.';

insert into public.heartbeat (note) values ('SAGE keep-alive');

-- Row level security: the Data API only returns rows that a policy allows.
alter table public.heartbeat enable row level security;

create policy "Anyone can read the heartbeat"
  on public.heartbeat
  for select
  to anon
  using (true);

-- The Data API only sees tables its roles have been granted. Start from nothing, then let
-- requests made with the publishable key (the anon role) read, and nothing else.
revoke all on table public.heartbeat from anon, authenticated;
grant select on table public.heartbeat to anon;
