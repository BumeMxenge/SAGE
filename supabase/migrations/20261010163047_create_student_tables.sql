-- One student's data: profile, confirmed course history, favourites, generated plans and chats.
-- Each student reads only their own rows, and only the backend writes. Each table is secured straight
-- after it is created, so none ever exists without row level security.

-- Stamps updated_at on every update, so the database keeps it current rather than every caller.
create function public.set_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  new.updated_at := now();
  return new;
end
$$;
-- Only triggers call it. Postgres checks this privilege when a trigger is created, not each time it
-- fires, so the triggers at the end of this file still run for the backend.
revoke execute on function public.set_updated_at() from public, anon, authenticated;

-- One profile per sign-in account. The name comes from the account's metadata and the student number
-- from the UCT email, so neither is stored here. Transcript extraction is one request that saves
-- nothing until Finish setup, and the PDF is never kept, so there are no transcript columns either.
create table public.students (
  id uuid primary key references auth.users (id) on delete cascade,
  -- the full code, such as EB011EEE05, with no foreign key because curricula rows are per year;
  -- null until onboarding sets it
  curriculum_code text,
  -- the year the student first registered; null until onboarding sets it
  intake_year smallint check (intake_year between 2000 and 2100),
  onboarding_complete boolean not null default false,
  updated_at timestamptz not null default now(),
  -- a finished onboarding has set both
  check (not onboarding_complete or (curriculum_code is not null and intake_year is not null))
);

alter table public.students enable row level security;
create policy "Students read their own profile" on public.students
  for select to authenticated using (id = (select auth.uid()));
revoke all on table public.students from anon, authenticated;
grant select on table public.students to authenticated;
grant select, insert, update, delete on table public.students to service_role;

-- One transcript line, as printed. Lines are written only when the student presses Finish setup, so
-- every row is one they confirmed; the extractor's confidence flags stay on the review screen.
create table public.course_history (
  student_id uuid not null references public.students (id) on delete cascade,
  academic_year smallint not null check (academic_year between 2000 and 2100),
  term public.term_code not null,
  course_code text not null, -- as printed, with no foreign key, so discontinued courses stay
  course_name text not null,
  credits smallint not null check (credits >= 0),
  -- null = not printed, as on current-year GIP lines
  nqf_level smallint check (nqf_level between 5 and 10),
  result text not null references public.result_symbols (symbol) on delete restrict,
  mark smallint check (mark between 0 and 100), -- null = no mark printed
  updated_at timestamptz not null default now(),
  primary key (student_id, academic_year, term, course_code)
);
create index on public.course_history (result);

alter table public.course_history enable row level security;
create policy "Students read their own course history" on public.course_history
  for select to authenticated using (student_id = (select auth.uid()));
revoke all on table public.course_history from anon, authenticated;
grant select on table public.course_history to authenticated;
grant select, insert, update, delete on table public.course_history to service_role;

-- A course the student hearted.
create table public.favourites (
  student_id uuid not null references public.students (id) on delete cascade,
  -- a code rather than a year's row, so the heart survives into next year (no foreign key)
  course_code text not null,
  primary key (student_id, course_code)
);

alter table public.favourites enable row level security;
create policy "Students read their own favourites" on public.favourites
  for select to authenticated using (student_id = (select auth.uid()));
revoke all on table public.favourites from anon, authenticated;
grant select on table public.favourites to authenticated;
grant select, insert, update, delete on table public.favourites to service_role;

-- One run of plan generation for a year.
create table public.plan_sets (
  id uuid primary key default gen_random_uuid(),
  student_id uuid not null references public.students (id) on delete cascade,
  -- the year planned
  period smallint not null references public.handbook_versions (year) on delete restrict,
  -- a semester-2 regeneration is a new version in the same period
  version smallint not null check (version > 0),
  complete boolean not null default false,
  answers jsonb, -- the questionnaire's answers; null = not answered
  created_at timestamptz not null default now(),
  unique (student_id, period, version),
  unique (id, student_id) -- lets a child row name a plan set and its owner together
);
create index on public.plan_sets (period);

alter table public.plan_sets enable row level security;
create policy "Students read their own plan sets" on public.plan_sets
  for select to authenticated using (student_id = (select auth.uid()));
revoke all on table public.plan_sets from anon, authenticated;
grant select on table public.plan_sets to authenticated;
grant select, insert, update, delete on table public.plan_sets to service_role;

-- One valid plan in a set.
create table public.plans (
  id uuid primary key default gen_random_uuid(),
  plan_set_id uuid not null,
  student_id uuid not null,
  position smallint not null check (position > 0), -- its ranking in the set
  name text not null,
  hidden boolean not null default false, -- hidden by the questionnaire, never deleted by it
  -- the plan set must belong to the same student
  foreign key (plan_set_id, student_id)
    references public.plan_sets (id, student_id) on delete cascade,
  unique (plan_set_id, position),
  unique (id, student_id), -- lets a child row name a plan and its owner together
  unique (id, plan_set_id, student_id) -- lets a reason name a plan, its set and its owner together
);
create index on public.plans (plan_set_id, student_id);

alter table public.plans enable row level security;
create policy "Students read their own plans" on public.plans
  for select to authenticated using (student_id = (select auth.uid()));
revoke all on table public.plans from anon, authenticated;
grant select on table public.plans to authenticated;
grant select, insert, update, delete on table public.plans to service_role;

-- One course in a plan. Core or elective comes from course groups, so there is no kind column.
create table public.plan_courses (
  plan_id uuid not null,
  course_code text not null,
  student_id uuid not null,
  -- written by the backend from the plan set's period, because the course link needs (year, code)
  handbook_year smallint not null,
  -- the chosen alternative per choice group, such as {"lecture": "B"}; null = no alternatives chosen
  choices jsonb,
  primary key (plan_id, course_code),
  -- the plan must belong to the same student
  foreign key (plan_id, student_id) references public.plans (id, student_id) on delete cascade,
  foreign key (handbook_year, course_code)
    references public.courses (handbook_year, code) on delete restrict
);
create index on public.plan_courses (plan_id, student_id);
create index on public.plan_courses (handbook_year, course_code);

alter table public.plan_courses enable row level security;
create policy "Students read their own plan courses" on public.plan_courses
  for select to authenticated using (student_id = (select auth.uid()));
revoke all on table public.plan_courses from anon, authenticated;
grant select on table public.plan_courses to authenticated;
grant select, insert, update, delete on table public.plan_courses to service_role;

-- The engine's plain-language explanation for a set or one plan.
create table public.plan_reasons (
  id uuid primary key default gen_random_uuid(),
  plan_set_id uuid not null,
  student_id uuid not null,
  plan_id uuid, -- null = about the whole set
  course_code text, -- no foreign key; null = not about one course
  passage_id uuid references public.passages (id) on delete restrict, -- null = no passage cited
  kind text not null check (kind in ('excluded', 'conflict', 'conditional', 'included')),
  message text not null,
  details jsonb, -- null = nothing beyond the message
  -- the set must belong to the same student
  foreign key (plan_set_id, student_id)
    references public.plan_sets (id, student_id) on delete cascade,
  -- the plan must belong to the same set and student; with plan_id null the link isn't checked
  foreign key (plan_id, plan_set_id, student_id)
    references public.plans (id, plan_set_id, student_id) on delete cascade
);
create index on public.plan_reasons (plan_set_id, student_id);
create index on public.plan_reasons (plan_id, plan_set_id, student_id);
create index on public.plan_reasons (passage_id);

alter table public.plan_reasons enable row level security;
create policy "Students read their own plan reasons" on public.plan_reasons
  for select to authenticated using (student_id = (select auth.uid()));
revoke all on table public.plan_reasons from anon, authenticated;
grant select on table public.plan_reasons to authenticated;
grant select, insert, update, delete on table public.plan_reasons to service_role;

-- One conversation about a plan, or about a pair of plans being compared. Several chats may share the
-- same plan or pair.
create table public.chats (
  id uuid primary key default gen_random_uuid(),
  student_id uuid not null,
  plan_id uuid not null,
  other_plan_id uuid, -- null = a one-plan chat
  title text, -- named by the LLM after the first exchange; null = not named yet
  created_at timestamptz not null default now(),
  -- both plans must belong to the same student; with other_plan_id null, that link isn't checked
  foreign key (plan_id, student_id) references public.plans (id, student_id) on delete cascade,
  foreign key (other_plan_id, student_id) references public.plans (id, student_id) on delete cascade,
  -- a pair is stored in one fixed order, so each pair is written only one way
  check (other_plan_id is null or plan_id < other_plan_id),
  unique (id, student_id) -- lets a message name a chat and its owner together
);
create index on public.chats (plan_id, student_id);
create index on public.chats (other_plan_id, student_id);

alter table public.chats enable row level security;
create policy "Students read their own chats" on public.chats
  for select to authenticated using (student_id = (select auth.uid()));
revoke all on table public.chats from anon, authenticated;
grant select on table public.chats to authenticated;
grant select, insert, update, delete on table public.chats to service_role;

-- One turn of a chat.
create table public.messages (
  id uuid primary key default gen_random_uuid(),
  chat_id uuid not null,
  student_id uuid not null,
  role text not null check (role in ('user', 'assistant')),
  content text not null,
  term public.term_code, -- the term on screen when it was sent; null = no term on screen
  -- now() is fixed for a whole transaction, so a question and its answer saved together would share a
  -- timestamp; clock_timestamp() reads the clock for each row
  created_at timestamptz not null default clock_timestamp(),
  -- the chat must belong to the same student
  foreign key (chat_id, student_id) references public.chats (id, student_id) on delete cascade,
  unique (id, student_id) -- lets a citation name a message and its owner together
);
-- serves the foreign key and reading a chat in order
create index on public.messages (chat_id, student_id, created_at);

alter table public.messages enable row level security;
create policy "Students read their own messages" on public.messages
  for select to authenticated using (student_id = (select auth.uid()));
revoke all on table public.messages from anon, authenticated;
grant select on table public.messages to authenticated;
grant select, insert, update, delete on table public.messages to service_role;

-- A handbook passage that an answer cites.
create table public.message_citations (
  message_id uuid not null,
  passage_id uuid not null,
  student_id uuid not null,
  position smallint not null check (position > 0), -- the citation's number in the answer
  quote text not null, -- the words quoted
  primary key (message_id, passage_id),
  unique (message_id, position),
  -- the message must belong to the same student
  foreign key (message_id, student_id)
    references public.messages (id, student_id) on delete cascade,
  foreign key (passage_id) references public.passages (id) on delete restrict
);
create index on public.message_citations (message_id, student_id);
create index on public.message_citations (passage_id);

alter table public.message_citations enable row level security;
create policy "Students read their own citations" on public.message_citations
  for select to authenticated using (student_id = (select auth.uid()));
revoke all on table public.message_citations from anon, authenticated;
grant select on table public.message_citations to authenticated;
grant select, insert, update, delete on table public.message_citations to service_role;

-- Keep updated_at current on the two tables whose rows are edited in place.
create trigger set_updated_at before update on public.students
  for each row execute function public.set_updated_at();
create trigger set_updated_at before update on public.course_history
  for each row execute function public.set_updated_at();
