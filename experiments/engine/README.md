<!-- The engine's design decisions: each one's choice, options, deciding rule, reason and cost, and the count they rest on -->
# Engine decisions

How SAGE's engine plans a student's year was settled by the three decisions below. Each gives the choice, the options that would work, the rule that decided it, why it won and what it costs. None was settled by experiment: their outcomes don't depend on how a model behaves, so each is argued from the literature, the documentation and one count of SAGE's own rules, Table 1. Chapter 3 gives the argument in full, with its sources.

## The count

[count_plans.py](count_plans.py) reads an approved year's snapshot and, for a student on track in each curriculum and year from 2, counts the open choices and the valid plans under both ways a plan could hold complementary studies. A plan is valid when it holds the year's core, meets the group and credit rules with no spare elective, and has no clash. Courses with alternative sections are tested pair by pair, so the counts are upper bounds. The 576-credit rows multiply each plan by the complementary courses that fit it, once per place, so they are rough upper bounds.

The count looks at the timetable and nothing else. It ignores entry rules, as an on-track student meets them, and its last column counts timetable fit alone. The engine's own lists also leave out the courses she has passed and those whose entry rule she doesn't meet, so they can be shorter.

**Table 1. Plans per on-track student under the 2026 rules**, counted on 20 October.

| Case | Open EEE choices | Plans, each complementary course a member | Plans, complementary credits as one slot | Complementary courses that fit each plan |
| --- | --- | --- | --- | --- |
| Final year, all six curricula | 6 to 8 | 10 to 28 | 10 to 28 | None needed |
| Year 3 (EB009, EB011, EB022) | 0 to 3 | 283 to 895 | 1 to 3 | 43 to 61 |
| ASPECT year with complementary credits (EB809 y4, EB811 y4, EB822 y3) | 0 | 307 to 440 | 1 | 45 to 55 |
| Year 3, 576-credit student owing one complementary place | 0 to 3 | 12,452 to 41,993, roughly 10⁴ to 10⁵ | 1 to 3 | 43 to 61 |
| Year 3, 576-credit student owing two places | 0 to 3 | 547,888 to 1,985,971, roughly 10⁵ to 10⁶ | 1 to 3 | 43 to 61 |

EB822's fourth year has 3 open choices, 3 plans and no complementary requirement. Two facts follow. How a plan is defined changes its count by up to five orders of magnitude. Under the slot definition, no on-track student has more than 8 open choices, which is at most 256 combinations to check.

Each case:

| Curriculum | Year | Open EEE choices | Plans, each complementary course a member | Plans, complementary credits as one slot | Complementary courses that fit each plan |
| --- | --- | --- | --- | --- | --- |
| EB009EEE01 | 2 | 0 | 1 | 1 | None needed |
| EB009EEE01 | 3 | 0 | 495 | 1 | 61 |
| EB009EEE01 | 4 | 6 | 19 | 19 | None needed |
| EB011EEE05 | 2 | 0 | 1 | 1 | None needed |
| EB011EEE05 | 3 | 0 | 283 | 1 | 44 |
| EB011EEE05 | 4 | 6 | 10 | 10 | None needed |
| EB022EEE02 | 2 | 0 | 1 | 1 | None needed |
| EB022EEE02 | 3 | 3 | 895 | 3 | 43 to 52 |
| EB022EEE02 | 4 | 8 | 28 | 28 | None needed |
| EB809EEE01 | 2 | 0 | 1 | 1 | None needed |
| EB809EEE01 | 3 | 0 | 1 | 1 | None needed |
| EB809EEE01 | 4 | 0 | 389 | 1 | 55 |
| EB809EEE01 | 5 | 6 | 19 | 19 | None needed |
| EB811EEE05 | 2 | 0 | 1 | 1 | None needed |
| EB811EEE05 | 3 | 0 | 1 | 1 | None needed |
| EB811EEE05 | 4 | 0 | 307 | 1 | 45 |
| EB811EEE05 | 5 | 6 | 10 | 10 | None needed |
| EB822EEE02 | 2 | 0 | 1 | 1 | None needed |
| EB822EEE02 | 3 | 0 | 440 | 1 | 54 |
| EB822EEE02 | 4 | 3 | 3 | 3 | None needed |
| EB822EEE02 | 5 | 8 | 28 | 28 | None needed |

The first draft of Table 1 counted two of the three ASPECT cases. All three are counted here, and the third, EB809's 389, falls inside the same range.

To rerun it, from `experiments/engine/`: `uv run count_plans.py 2026`. It takes under a second. It runs on its own, outside the group's usual environment, which imports the backend by path: uv's inline script header asks only for Python 3.12, and the script reads the snapshot with the standard library, so it shares no code with the engine.

## What the engine returns

- **Choice.** Every valid plan, ranked. The questionnaire hides plans, and no one edits one.
- **Options.** Check a plan the student builds, as registration on SEAT works today; find one best plan by optimisation, as mixed-integer course planning does; or return every valid plan for her to filter, as Hahn et al. do for study regulations at Potsdam.
- **Rule.** F-3: the valid plans, for her to filter and compare.
- **Why it won.** Table 1 shows it's affordable: at most 28 plans on track. In Karp and Heiser's study of 24 students planning a semester, considerations unrelated to graduation requirements outnumbered those related to them by about two to one, among them work, timing, cost and interest, which no engine can rank by. Checking a plan she builds leaves the combinatorial work with her, which the same students called the hard part. A question about a swap is then answered with an existing plan (F-4), and as plans are never edited, there's no edit race to test.
- **Cost.** Plans are generated and stored up front, so a corrected record means generating the set again, and each set takes storage. A programme with many more plans would need the ranking and the cap of 50.

## What a plan holds

- **Choice.** One slot per complementary requirement. A plan holds her core and EEE electives, and each slot gives its credits, the passage it rests on and the complementary courses that fit that plan's timetable, marking those with a meeting that has no printed time.
- **Options.** Each complementary course a plan member; members drawn only from the courses she hearted; or a slot.
- **Rule.** F-3, read with the questionnaire's rules: it runs only above five plans and builds its questions from how plans differ, so a set must be small enough to compare, and its plans must differ on choices the engine can judge.
- **Why it won.** As members, complementary courses turn a year-3 student's 1 to 3 plans into 283 to 895, and give a 576-credit student owing both places up to about two million, differing mainly in which humanities or commerce course fills 18 credits, a choice made on interest. The handbook already draws this line. Elective courses are left to the student's choice, subject to the timetable (p. 12). Mechatronics prints its complementary requirement as one 18-credit line pointing to a separate list (p. 58), and the 576-credit footnotes ask for one approved course of at least 8 credits, timetable permitting (pp. 57 to 58). Hearts start empty, so a new student would get no complementary choice, and her plans would change with every heart.
- **Cost.** A plan doesn't name its complementary course. A clash between the course she picks and her plan shows only in the slot's list. 35 of the 106 offerings have a meeting with no printed day or time, which send her to an advisor. The API doesn't carry the slot's list yet, and a plan's credit total leaves the slot out.

## How plans are generated

- **Choice.** clingo, an answer set programming system. A year's rules and her record become facts under one fixed encoding, and every answer set is a plan.
- **Options.** clingo, or backtracking search written in Python, which adds one course at a time and abandons a partial plan as soon as a rule breaks. Three were excluded, one reason each: CP-SAT counts every assignment of every variable when it enumerates, so plans that differ only in section would repeat (to reconfirm); python-constraint2 adds a dependency that neither counts plans once nor ranks them; and a mixed-integer program returns one optimal plan per run, which the first decision rejects.
- **Rule.** NF-1: every plan valid, and every valid plan returned once. Speed can't decide. No on-track student has more than 8 open choices, 256 combinations, which either method checks well within NF-4's 10 seconds.
- **Why it won.** It counts each plan once by design: 20 courses have alternative sections, and clingo's enumeration projected onto the courses is proven sound, complete and free of repeats (Gebser, Kaufmann and Schaub), where hand-written search must be built and tested to do the same. It states SAGE's four rule shapes as facts under one encoding, so a new year loads as new facts (NF-6), as Hahn et al. found for Potsdam's regulations. Solving under assumptions returns the requirements that conflict, which the questionnaire's explanations need, as in TRACE-cs. And it makes ATP-2's Python checker a genuinely different implementation: in Knight and Leveson's experiment, versions written independently from one specification failed together far more often than chance, and a Python checker would share a backtracking engine's loops and bounds.
- **Cost.** A dependency, clingo 5.8.2, with wheels for CPython 3.12 on Intel macOS and Linux. A second language for anyone maintaining the engine. A translation step from rulebook to facts, which can carry faults of its own. A silent failure mode, as an encoding error removes plans without raising an error, which each rule shape's tests and ATP-2's checker guard. Grounding on every generation, which ATP-5 measures. Speed and scale are not claimed.
