<!-- What ATP-2 checks, how its checker and sweep work, how to run it, and how to read its report -->
# ATP-2: the engine's decisions and plans

ATP-2 asks whether the engine gives the right decision and reason for every course, and every valid plan exactly once (F-2, F-3 and NF-1), within NF-4's 10 seconds. Its pass criterion, from Table 3.4, is "Every decision matches its label, and plan sets hold every valid plan once and nothing else." The harness never edits what it tests. It reads `backend/src`, `data/rules` and the result symbols, and calls no model.

## Three oracles

| Oracle | Records | What it checks |
| --- | --- | --- |
| Labels written from print, in [labels/](labels/), committed before any run | The held-out records | Each decision, plan set, slot and reason against print |
| The checker, written from [SEMANTICS.md](SEMANTICS.md) alone | Every record | Every plan set, status and slot, by brute force |
| The sweep of made-up failures | 531 records | A large n, and what failing each course costs a student |

The checker never opens the engine's code and imports nothing from it, as a checker that shared the engine's code would share its mistakes. It reads the approved 2026 rules through `shared/`'s types, with the meetings `timetabled()` adds, as [ENGINE_INTERFACE.md](ENGINE_INTERFACE.md) says the engine reads them. It writes its own covers and its own filter of a curriculum's meetings, rather than import `offerings()` and `meetings_on()` from `shared/rules.py`, which the engine relies on.

## What the checker computes

For one record:

- **Her year of study**, by FB5 as SEMANTICS.md reads it.
- **Owed and excluded core**: outstanding core from earlier years, core whose entry rule no plan can meet, and current-year core FB3.4 leaves out.
- **Each course's status** outside a plan: eligible, check or not_eligible.
- **Every valid plan**, by trying every subset of her open choices: the electives of her year's choose and credits groups, and of any earlier year's she hasn't met, that she hasn't passed or isn't waiting on. A subset is a plan when it meets every year rule and the credit minimum, has no spare elective, meets every entry rule inside the plan, and has one section of each choice group, chosen for the whole plan at once, with no clash. CSC3002F's and CSC3003S's practical day pairs are choices like any other. It counts the subsets it tries.
- **Each slot**: one per unfilled complementary line and per owed 576-credit place, with its credits and the approved complementary courses that fit the plan.

It leaves out forced sections, recorded alternatives, ranking, the 50-plan cap, plan names, reasons' wording and passages, a slot's marks for untimed courses and courses worth fewer credits, and 2023. The labels check reasons and passages against print.

### Readings SEMANTICS.md doesn't settle

Each is a place a disagreement can come from. All but the last were approved at Stop 1, and the last came up while building the checker:

- A plan course stands in for a pass in every code its pass would cover.
- A course's own meetings never clash with each other.
- A result still to come counts as passed for her year of study, for her plans, which assume she passes, for her outstanding core and for the year's printed minimum. It doesn't count for the final-year floor, whose passed credits are pass and credited lines alone.
- For "starts no later", q1, sem1 and full_year start together, q2 halfway through sem1, then sem2 and q3 together, then q4. An "earlier term" ends before the other starts.
- Core courses are passed through plain covers. A group rule counts each of her lines once, by matching lines to codes.
- A 576-credit place counts 8 credits towards the minimum.
- A complementary course with a result still to come stays on a slot's list, as only passes leave one out.
- One repeated course clashing with two current-year courses is two one-to-one clashes under FB3.4, so both are left out, and each lowers the credit minimum as an exclusion does.
- The 576-credit places don't count towards her year of study. Like practical training, they're never plan members.

## Its tests

`test_checker.py` holds 23 cases, each on a made-up year small enough to work by hand, with boundaries on both sides: meetings that touch and overlap, a mark at min_mark and one below, the supplementary cap, one equivalence and one offering step against two equivalences, a co-requisite in the same term and the next, a spare elective, FB3.4 against one and two current-year courses, the year-of-study threshold, a section choice that works pairwise but not for the whole plan, and a slot list. `make test` collects them, so CI runs them. `make atp2` runs them first and stops if any fails, so no record runs on a checker that fails its own tests.

## The sweep

`sweep.py` builds the made-up records with seed 4022, from the approved 2026 curriculum tables. For each curriculum and continuing year there's an on-track base record: intake 2026 less her years before this one, so an intake before 2025 is on the 576-credit curriculum. Every earlier year's core is passed with marks from 55 to 85 and the symbols that match them, practical training as PA, the cheapest electives that meet each earlier year's rules, and AGE1002S, the first 18-credit approved complementary course with no entry rule, for each earlier complementary line. A 576-credit place's own course, ASL1200S or CON2026S, is passed in its place's year when that's before hers, so a place in her own year is owed.

From each base come:

- **fail**: one previous-year core course failed (F, 40), ASL1200S and CON2026S included where they're core, and first-year maths and physics together (MAM1020F and PHY1012F) on the 4-year curricula's year-2 records. Under FB5 she's in the previous year again, so these measure how often a failure holds a student back.
- **arrears**: the same failure, with passes in the first two of her own year's core courses, by code, whose entry rules name nothing the failure covers. FB5 then puts her in her year, owing it. These give the thesis's figure of what each failure costs.
- **supplementary**: one previous-year core course with a supplementary pending (FS, 46).

The base records are reported apart, as in-sample: the engine was built on on-track students.

## What the run compares

On every record, `run.py` runs the checker once, then the engine's `generate()` five times, comparing the first, and its `check()` once, each timed, one record at a time.

- **Plan sets**, as sets of course-code sets: valid plans missing, plans that aren't valid, and plans listed twice. Past 50 valid plans, the engine's must be 50 of them.
- **Statuses** for every course in the groups her year's rules name, complementary courses included where her year has a line.
- **Slots**, in plans both sides hold: each slot's credits, owed course and fitting courses.
- **Plans resting on judgement** (NF-1): each plan course whose rule is open inside the plan, or with a meeting with no printed time, needs a conditional reason naming it, on the plan or the set.
- **Three metamorphic relations** on every sweep record, each a change whose effect is known without knowing the answer. Her history in another order gives the same plan sets and statuses. One alternative of one plan course's choice group taken away never adds a plan, wherever the checker's FB3.4 drops stay the same. A pass in a course of her year's groups she hasn't passed, complementary courses aside, never turns another course from eligible to not_eligible, leaving out that course and those its pass covers.

Every disagreement is classed by hand in `results/causes.csv`, with its evidence: an engine fault, a checker fault, a label slip, a semantics gap (a line SEMANTICS.md doesn't settle) or a known gap, such as EEE2046S, which the approved rules don't hold. A fault becomes an Open row in `docs/shortfalls.md`.

## Running it

From the repo root, on a quiet laptop, as the times are measured:

```
make atp2
```

It needs no database, as everything is in memory, and calls no model. It writes the sweep to `results/sweep/`, every CSV, and then `results/report.md`.

## Results

| File | Holds |
| --- | --- |
| `report.md` | The verdicts, then each measure's tables, the disagreements by cause and the inputs |
| `sweep/` | Every made-up record as a seed file, and `manifest.csv`, saying what each is |
| `sweep.csv` | One row per sweep record: the engine's plan sets against the checker's, slots, plans resting on judgement, the core each side excludes and drops, and the reasons by kind |
| `decisions.csv` | One row per record and course: the engine's status, the checker's and the engine's reason |
| `metamorphic.csv` | One row per instance of each relation: whether it applies, whether it held, and what changed |
| `timings.csv` | Each record's five generate times, its check time and the checker's time, in seconds |
| `failure_cost.csv` | One row per failure record: plans left beside the base record's, the core excluded, FB3.4's drops, conditional courses and reasons by kind, whether FB5 held her back, and whether the checker agreed |
| `scaling.csv` | One row per record: the subsets the checker tried, the engine's p50 and p95, and the checker's time |
| `causes.csv` | Each disagreement's cause and evidence, written by hand after the first run |
| `inputs.csv` | The SHA-256 of every file the run read |

## Reading the report

Verdicts come first, one line per target, with the held-out records, the failure sweep and the in-sample base records side by side. A rate carries its 95% Wilson interval, a count with none wrong gives the one-sided 95% upper bound, 1 − 0.05^(1/n), and a time gives its p50 and p95. The interval and the bound come from ATP-1's `scoring.py`.

The first result is committed on its own and kept. A rerun reproduces every file but the times. A checker fault fixed after the first run gets a retest in a folder of its own beside the first result, never over it.
