-- The rulebook: each handbook year's curricula, courses, course lists, timetable and prose, plus UCT's
-- result symbols. Signed-in students read approved years only, and only the backend writes.
-- Each table is secured straight after it is created, so none ever exists without row level security.

create extension if not exists vector with schema extensions;

-- Every term a course or meeting can run in. It covers the handbook's whole suffix key: A to D are
-- quarters, F and S semesters, H and W the whole year, L winter, U, J and P summer, and M, X and Z other.
create domain public.term_code as text
  check (value in ('q1', 'q2', 'q3', 'q4', 'sem1', 'sem2', 'full_year', 'winter', 'summer', 'other'));

-- One handbook edition.
create table public.handbook_versions (
  year smallint primary key check (year between 2000 and 2100),
  -- the release switch: students see nothing from a year until it's true
  approved boolean not null default false
);

alter table public.handbook_versions enable row level security;
create policy "Signed-in users read approved handbooks" on public.handbook_versions
  for select to authenticated using (approved);
revoke all on table public.handbook_versions from anon, authenticated;
grant select on table public.handbook_versions to authenticated;
grant select, insert, update, delete on table public.handbook_versions to service_role;

-- One change from the previous year's rules, with the decision on it. Reloading a year never
-- overwrites a decided row, so corrections survive as the record of extraction errors.
create table public.handbook_deltas (
  handbook_year smallint not null references public.handbook_versions (year) on delete cascade,
  -- the table the change is in
  entity text not null check (entity in ('curricula', 'curriculum_rules', 'courses', 'course_groups',
    'course_group_members', 'equivalences')),
  -- the changed row's key without the year, parts joined by '/'
  -- (EEE4117F; EB011EEE05/4; EB011EEE05-y4-core/EEE4117F)
  entity_key text not null,
  old_value jsonb, -- null = added
  new_value jsonb, -- what extraction read; null = removed
  corrected_value jsonb, -- what the row was corrected to; null = extraction was right
  -- accepts the change from old_value to corrected_value, or to new_value when there's no
  -- correction; null = pending
  approved boolean,
  primary key (handbook_year, entity, entity_key),
  -- a change has a before, an after, or both
  check (old_value is not null or new_value is not null)
);

-- No policy and no grant for signed-in users, so only the backend sees the review.
alter table public.handbook_deltas enable row level security;
revoke all on table public.handbook_deltas from anon, authenticated;
grant select, insert, update, delete on table public.handbook_deltas to service_role;

-- One printed curriculum. There is no programmes table, programme code or route column: the handbook
-- prints no programme code, and each 5-year curriculum has its own code, rules and timetable sheet.
create table public.curricula (
  handbook_year smallint not null references public.handbook_versions (year) on delete cascade,
  -- the full code printed in square brackets under the heading (EB011EEE05, EB822EEE02), because EB
  -- numbers alone repeat across EBE (EB001CHE01 and EB001CHE06)
  code text not null,
  name text not null, -- the heading as printed
  department text not null, -- the department heading it's printed under; departments have no table
  degree_rule jsonb, -- whole-degree requirements, such as the credits to graduate; null = none loaded
  primary key (handbook_year, code)
);

alter table public.curricula enable row level security;
create policy "Signed-in users read approved years" on public.curricula
  for select to authenticated
  using (exists (select 1 from public.handbook_versions v
                 where v.year = curricula.handbook_year and v.approved));
revoke all on table public.curricula from anon, authenticated;
grant select on table public.curricula to authenticated;
grant select, insert, update, delete on table public.curricula to service_role;

-- What a curriculum demands in one year of study.
create table public.curriculum_rules (
  handbook_year smallint not null,
  curriculum_code text not null,
  year_of_study smallint not null check (year_of_study between 1 and 5),
  rule jsonb not null,
  primary key (handbook_year, curriculum_code, year_of_study),
  foreign key (handbook_year, curriculum_code)
    references public.curricula (handbook_year, code) on delete cascade
);

alter table public.curriculum_rules enable row level security;
create policy "Signed-in users read approved years" on public.curriculum_rules
  for select to authenticated
  using (exists (select 1 from public.handbook_versions v
                 where v.year = curriculum_rules.handbook_year and v.approved));
revoke all on table public.curriculum_rules from anon, authenticated;
grant select on table public.curriculum_rules to authenticated;
grant select, insert, update, delete on table public.curriculum_rules to service_role;

-- One course in one handbook year. Its outline, requirements and class times as printed live in
-- passages, so there is no description column.
create table public.courses (
  handbook_year smallint not null references public.handbook_versions (year) on delete cascade,
  code text not null check (code ~ '^[A-Z]{3}[0-9]{4}[A-Z]$'), -- the handbook's eight-character format
  name text not null,
  credits smallint not null check (credits >= 0), -- 0-credit courses exist (CHE3000X)
  nqf_level smallint not null check (nqf_level between 5 and 10),
  term public.term_code not null, -- taken from the source, never parsed from the code
  entry_rule jsonb, -- prerequisites and co-requisites as one tree; null = no entry requirements
  -- display only, as printed (one or more names, or a school), for the Explore Electives cards and
  -- outside the validated rule model; null = none printed
  convener text,
  primary key (handbook_year, code)
);

alter table public.courses enable row level security;
create policy "Signed-in users read approved years" on public.courses
  for select to authenticated
  using (exists (select 1 from public.handbook_versions v
                 where v.year = courses.handbook_year and v.approved));
revoke all on table public.courses from anon, authenticated;
grant select on table public.courses to authenticated;
grant select, insert, update, delete on table public.courses to service_role;

-- A named list of courses that a rule picks from. A group exists only when a rule picks from it, and
-- core is a group.
create table public.course_groups (
  handbook_year smallint not null references public.handbook_versions (year) on delete cascade,
  -- a name only, and nothing reads meaning back out of it: a curriculum's lists are named after the
  -- curriculum and year of study (EB011EEE05-y4-core), faculty-wide lists plainly (complementary)
  group_key text not null,
  label text not null, -- the list's heading as printed
  primary key (handbook_year, group_key)
);

alter table public.course_groups enable row level security;
create policy "Signed-in users read approved years" on public.course_groups
  for select to authenticated
  using (exists (select 1 from public.handbook_versions v
                 where v.year = course_groups.handbook_year and v.approved));
revoke all on table public.course_groups from anon, authenticated;
grant select on table public.course_groups to authenticated;
grant select, insert, update, delete on table public.course_groups to service_role;

-- One course in one list. A printed wildcard such as CSC3xxx is expanded by the loader into real courses.
create table public.course_group_members (
  handbook_year smallint not null,
  group_key text not null,
  course_code text not null,
  -- the Explore Electives tab key for a complementary course (null on every other list); the tab
  -- list lives in one place in the backend, which the loader's LLM picks from, the frontend reads
  -- and the backend checks every value against, so tabs can change without a migration
  category text,
  primary key (handbook_year, group_key, course_code),
  foreign key (handbook_year, group_key)
    references public.course_groups (handbook_year, group_key) on delete cascade,
  foreign key (handbook_year, course_code)
    references public.courses (handbook_year, code) on delete cascade
);
create index on public.course_group_members (handbook_year, course_code);

alter table public.course_group_members enable row level security;
create policy "Signed-in users read approved years" on public.course_group_members
  for select to authenticated
  using (exists (select 1 from public.handbook_versions v
                 where v.year = course_group_members.handbook_year and v.approved));
revoke all on table public.course_group_members from anon, authenticated;
grant select on table public.course_group_members to authenticated;
grant select, insert, update, delete on table public.course_group_members to service_role;

-- A pass in one code counts as a pass in another: renamed codes and F/S twins only. Shared courses
-- such as EEE2046F and EEE2050F are not equivalences.
create table public.equivalences (
  handbook_year smallint not null references public.handbook_versions (year) on delete cascade,
  -- neither code has a foreign key, so retired codes are allowed
  course_code text not null,
  counts_as text not null,
  primary key (handbook_year, course_code, counts_as),
  check (course_code <> counts_as)
);

alter table public.equivalences enable row level security;
create policy "Signed-in users read approved years" on public.equivalences
  for select to authenticated
  using (exists (select 1 from public.handbook_versions v
                 where v.year = equivalences.handbook_year and v.approved));
revoke all on table public.equivalences from anon, authenticated;
grant select on table public.equivalences to authenticated;
grant select, insert, update, delete on table public.equivalences to service_role;

-- One meeting of a course, stored once however many curricula attend it. Rows sharing a choice_group
-- with different choice letters are alternatives: the student attends every row of exactly one
-- choice. A course with no rows has no contact time. Times are stored as printed, and touching times
-- (09:00 end, 09:00 start) don't clash.
-- The day and the time are stored separately, because some handbook entries print a period without
-- days, a day without a time, or neither. The engine treats an unknown day or time as "may clash",
-- never as a clash: the plan stays valid with a conditional reason telling the student to ask their
-- advisor.
create table public.timetable_slots (
  id uuid primary key default gen_random_uuid(),
  handbook_year smallint not null,
  course_code text not null,
  term public.term_code not null,
  -- day, start_time and end_time are all null when nothing is printed
  day smallint check (day between 1 and 7), -- 1 = Monday; null = no day printed
  start_time time, -- null together with end_time = no time printed
  end_time time,
  -- null = not printed
  kind text check (kind in ('lecture', 'tutorial', 'practical', 'lab', 'workshop', 'screening',
    'conversation')),
  choice_group text, -- null = compulsory
  choice text, -- the alternative's letter; null = compulsory
  foreign key (handbook_year, course_code)
    references public.courses (handbook_year, code) on delete cascade,
  -- the target of timetable_slot_curricula's year-checked link
  unique (id, handbook_year),
  -- a printed time has both a start and an end
  check ((start_time is null) = (end_time is null)),
  -- a meeting ends after it starts
  check (end_time > start_time),
  -- a meeting is either compulsory or one letter of a named choice
  check ((choice_group is null) = (choice is null))
);
create index on public.timetable_slots (handbook_year, course_code);

alter table public.timetable_slots enable row level security;
create policy "Signed-in users read approved years" on public.timetable_slots
  for select to authenticated
  using (exists (select 1 from public.handbook_versions v
                 where v.year = timetable_slots.handbook_year and v.approved));
revoke all on table public.timetable_slots from anon, authenticated;
grant select on table public.timetable_slots to authenticated;
grant select, insert, update, delete on table public.timetable_slots to service_role;

-- A curriculum that attends a meeting, when not everyone taking the course does. A slot with no rows
-- here is attended by everyone taking the course.
create table public.timetable_slot_curricula (
  slot_id uuid not null,
  handbook_year smallint not null,
  curriculum_code text not null,
  primary key (slot_id, curriculum_code),
  -- naming the year in this link keeps it equal to the slot's
  foreign key (slot_id, handbook_year)
    references public.timetable_slots (id, handbook_year) on delete cascade,
  foreign key (handbook_year, curriculum_code)
    references public.curricula (handbook_year, code) on delete cascade
);
create index on public.timetable_slot_curricula (slot_id, handbook_year);
create index on public.timetable_slot_curricula (handbook_year, curriculum_code);

alter table public.timetable_slot_curricula enable row level security;
create policy "Signed-in users read approved years" on public.timetable_slot_curricula
  for select to authenticated
  using (exists (select 1 from public.handbook_versions v
                 where v.year = timetable_slot_curricula.handbook_year and v.approved));
revoke all on table public.timetable_slot_curricula from anon, authenticated;
grant select on table public.timetable_slot_curricula to authenticated;
grant select, insert, update, delete on table public.timetable_slot_curricula to service_role;

-- Handbook prose, chunked and embedded for the advisor. One passage per course entry holds its outline,
-- requirements, convener and class times as printed. One model embeds every passage (the backend's
-- settings name it), and the vector index arrives with that model, as its own migration.
create table public.passages (
  id uuid primary key default gen_random_uuid(),
  handbook_year smallint not null references public.handbook_versions (year) on delete cascade,
  -- curriculum_code and course_code are both null for faculty rules or a department introduction
  curriculum_code text, -- prose printed under one curriculum's heading; null = not under one
  course_code text, -- one course entry; null = not a course entry
  source text not null, -- the handbook's official title, e.g. "UCT Faculty of Engineering & the Built Environment Undergraduate Handbook 2026 (Book 7a)"
  section text not null, -- the heading the chunk sits under
  page smallint not null check (page > 0), -- the printed page number
  content text not null,
  embedding extensions.vector, -- null = not embedded yet
  foreign key (handbook_year, curriculum_code)
    references public.curricula (handbook_year, code) on delete cascade,
  foreign key (handbook_year, course_code)
    references public.courses (handbook_year, code) on delete cascade,
  -- a passage sits under one curriculum's heading or in one course entry, never both
  check (curriculum_code is null or course_code is null)
);
create index on public.passages (handbook_year, curriculum_code);
create index on public.passages (handbook_year, course_code);

alter table public.passages enable row level security;
create policy "Signed-in users read approved years" on public.passages
  for select to authenticated
  using (exists (select 1 from public.handbook_versions v
                 where v.year = passages.handbook_year and v.approved));
revoke all on table public.passages from anon, authenticated;
grant select on table public.passages to authenticated;
grant select, insert, update, delete on table public.passages to service_role;

-- One of UCT's result symbols and what it means. Not tied to a year, because the symbols come from
-- UCT's general rules.
create table public.result_symbols (
  symbol text primary key,
  outcome text not null check (outcome in ('pass', 'fail', 'dp_refused', 'supp_pending', 'in_progress',
    'credited', 'not_counted')),
  label text not null
);

alter table public.result_symbols enable row level security;
create policy "Signed-in users read the result symbols" on public.result_symbols
  for select to authenticated using (true);
revoke all on table public.result_symbols from anon, authenticated;
grant select on table public.result_symbols to authenticated;
grant select, insert, update, delete on table public.result_symbols to service_role;

-- The results-symbol list printed in the 2026 Commerce handbook.
insert into public.result_symbols (symbol, outcome, label) values
  ('1', 'pass', 'First class (75 to 100%)'),
  ('2+', 'pass', 'Second class, division one (70 to 74%)'),
  ('2-', 'pass', 'Second class, division two (60 to 69%)'),
  ('3', 'pass', 'Third class (50 to 59%)'),
  ('PA', 'pass', 'Pass (pass or fail course)'),
  ('SP', 'pass', 'Pass via a supplementary exam'),
  ('UP', 'pass', 'Unclassified pass'),
  ('F', 'fail', 'Fail'),
  ('SF', 'fail', 'Supplementary exam failed'),
  ('UF', 'fail', 'Unclassified fail'),
  ('SM', 'fail', 'Subminimum not met'),
  ('AB', 'fail', 'Absent from the exam'),
  ('INC', 'fail', 'Incomplete'),
  ('FS', 'supp_pending', 'Failed, supplementary exam allowed'),
  ('OSS', 'supp_pending', 'Subminimum failed, supplementary exam awarded'),
  ('DE', 'supp_pending', 'Deferred exam granted'),
  ('DPR', 'dp_refused', 'Duly performed certificate refused'),
  ('GIP', 'in_progress', 'Grade in progress'),
  ('OS', 'in_progress', 'Result not yet available'),
  ('CR', 'credited', 'Credit'),
  ('EX', 'credited', 'Exemption'),
  ('CX', 'credited', 'Credit and exemption'),
  ('EXC', 'not_counted', 'Credit excluded'),
  ('ATT', 'not_counted', 'Course attended'),
  ('LOA', 'not_counted', 'Leave of absence'),
  ('EXA', 'not_counted', 'Excluded from assessment');
