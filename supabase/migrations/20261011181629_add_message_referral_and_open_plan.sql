-- What a reply hands on besides its text: whether it passes the question to a human advisor, and a
-- plan it offers to open. Stored, so neither vanishes when a chat reloads. The table's existing
-- grants and policy already cover new columns.

-- the reply hands the question to a human advisor
alter table public.messages add column referral boolean not null default false;

-- a plan the reply offers to open; null = none
alter table public.messages add column open_plan_id uuid;

-- the plan must be the same student's; deleting it clears the offer and keeps the message
alter table public.messages add foreign key (open_plan_id, student_id)
  references public.plans (id, student_id) on delete set null (open_plan_id);

-- only a reply can refer a question or offer a plan
alter table public.messages add check (role = 'assistant' or (not referral and open_plan_id is null));

-- serves the foreign key
create index on public.messages (open_plan_id, student_id);
