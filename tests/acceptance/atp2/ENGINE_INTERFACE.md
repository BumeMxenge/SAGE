# SAGE Engine Interface, for ATP-2's Checker

From the engine's Stop 4 hand-back on 22 October 2026, at `af1c76e` on `feature/build-plan-engine`. It says how to call the engine and what comes back, and nothing on how the encoding works, so the checker can't copy it. The rules the checker follows are in `claude/SAGE_ENGINE_SEMANTICS.md`.

## Entry points

In `backend/src/sage/engine/`, filling the interfaces in `shared/planning.py`:

- `generator.ClingoPlanGenerator().generate(student, history, rules, symbols)` returns a `PlanSetRows`.
- `eligibility.EntryRuleEligibility().check(courses, history, rules, symbols, student)` returns `{code: Eligibility}`. Each `status` is `eligible`, `check` or `not_eligible`, with a `reason` or none.

## Inputs

- `student`: a `Student` with `curriculum_code` and `intake_year`.
- `history`: her confirmed `CourseHistoryLine`s, with `academic_year`, `term`, `course_code` as printed, `course_name`, `credits`, `nqf_level`, `result` (a transcript symbol) and `mark`.
- `rules`: one approved year with the printed meetings added, `timetabled(approved_snapshot(2026).rules)`. `timetabled` is in `shared/printed_meetings.py`. **Passing the raw snapshot leaves out the CSC meetings**, so the checker must build its rules the same way.
- `symbols`: the result symbols by symbol, from `backend/tests/fixtures/result_symbols.json`.

## Outputs

They come back unwritten, with the set not yet complete.

- `plan_set`: `period` (the year planned) and `version` 1.
- `plans`: at most 50, best first.
  - `position`: 1 is best. The order is fewest conditional courses, then fewest credits, then course codes.
  - `name`: one theme word per elective in code order, written "A, B & C". A word two electives share appears once, an elective with no word gets its printed name, and "Core Courses Only" means no electives.
  - `combination`: the electives' codes in code order joined with " · ", or null with none.
  - `hidden`: false.
- `plan_courses`: `plan_id`, `course_code`, `handbook_year` and `choices`.
  - `choices` holds each choice group's alternatives that fit the rest of the plan, sorted, such as `{"practical": ["Monday and Thursday", "Tuesday and Thursday"]}`.
  - One alternative left means it's fixed. Null means the course has no choice group.
- `plan_reasons`:
  - `plan_id`: null for the set's own reasons.
  - `course_code`: the course it's about, if any.
  - `kind` and `message`.
  - `passage_id`: the passage it cites, in `rules.passages`, if any.
  - `details`: on slot reasons only.

## Reason kinds

- `included`: the core, the year rules and credit minimum the plans meet, next year's core she could take early, an entry rule a plan meets itself, and a slot with a course that fits.
- `excluded`: a course whose entry rule she doesn't meet, and plans with more electives than the year needs.
- `conditional`: words a person must judge, a meeting with no printed time, practical training, a result still to come, the same-timetable-slots note, a slot whose courses all need a check, and a year with no timetable to check against.
- `conflict`: an FB3.4 clash that leaves a course out, the smallest set of rules no plan can meet, no plan at all, and a finished record.

## Slot details

On the reason for a complementary line or a 576-credit place that a plan leaves to her:

- `credits`: what the line needs.
- `fits`: the approved complementary courses that fit the plan's timetable.
- `untimed`: those with a meeting that has no printed time.
- `fewer_credits`: those worth less than the line.
- `sections`: `{code: {group: [choices]}}`, for a course that fits only in some sections.
- `forced`: `{code: {plan course: {group: choice}}}`, where a course forces a section of one of the plan's courses.
- `owed`: on a place, the course it stands in for.

The slot reason is `included` when more courses fit than need a check, and `conditional` otherwise.

## Running it on a record

1. Write the record as JSON outside the repo, using the keys of the `students` and `course_history` rows in `data/synthetic/mbali.json`. Every other table is optional.
2. From `backend/`, run `uv run python scripts/show_plans.py --seed FILE`. It prints the set's reasons, then for each plan its name, combination and credits, its courses with their choices, and its reasons with the section and page each cites. Add `--rules 2023` to plan against 2023.
3. In code, `load_seed(path, account_id)` gives `student` and `course_history` to pass to `generate`, as the show script does.
