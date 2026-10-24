<!-- What ATP-1's harness reads, how to run it, and how to read its report -->
# ATP-1: how well ingestion reads print

ATP-1 asks how well SAGE's ingestion reads the printed sources, and whether anything wrong gets into SAGE without a person seeing it. The labels in [labels/](labels/README.md) are the answers, written from print and committed before any run. The harness marks SAGE against them and never edits what it tests: it only reads `backend/src`, `data/rules` and `data/sources`.

## What it compares

| Sheet | SAGE's side |
| --- | --- |
| `courses_2023.xlsx`, `courses_2026.xlsx` | Title, credits, NQF level, term and entry rule from the approved year, `data/rules/<year>/rulebook.json`. Page, requirement and co-requisite from the handbook reader, `Handbook.entry`, on that year's PDF |
| `timetable.xlsx` | The meeting `timetable.read` reads at the cell, found by its sheet and the first cell of its merged block |
| `complementary.xlsx` | The meeting `complementary.read` reads from the Meetings row, and its course's handbook and pages |
| `held_out.xlsx` | `Handbook.entry` on the 2026 PDF, then each printed string through the grammar and, where it refuses one, the drafter |

The change list comes from the two course sheets and the 2026 snapshot's deltas. The transcripts are made up by `transcripts.py`, with seed 4022.

Values are compared by the labels README's Scoring section, with these readings, settled before the first run:
- Printed text is compared with its spacing evened out. The labels write None for an entry that prints no requirement, so SAGE's side is written the same way. A co-requisite is scored where the label or the reader has one.
- Trees go through the canonical and normal forms of E2's [score.py](../../../experiments/ingestion/requirement-parsing/score.py). The course sheets join a label's two trees, as SAGE stores one rule per course. A held-out entry's requirement and co-requisite are scored apart, as each string is translated and reviewed on its own.
- No timetable label gives a Kind, so Kind isn't scored there.
- A held-out string the grammar refuses takes the drafter's tree, or a refer leaf holding the printed words where the reply isn't a rule tree, as SAGE does.
- Delta recall counts each rule field a course sheet labels: the title, ignoring case, the credits, the NQF level, the term and the rule, compared in normal form, and a course added or removed. A flagged 2026 delta where the labels show no change of rule is a wording change if the labelled requirement or co-requisite text changed, and a false alarm if not.
- A transcript row is recovered when a line gives back its name, NQF level, credits, mark and result. It's flagged when its line is marked unverified, or when only its year's Term GPA warning covers it. Otherwise it's dropped, and a line with its year and code but other values is listed as extra. A made-up record should raise no warning, so any warning is a disagreement.

## Accepted without review

An item is one labelled field of one row. It counts as reviewed when a review row a person decided showed it, in its own year, or in 2023 when it hasn't changed since. A requirement row shows the printed line, where it's printed and the trees, so:
- A course's entry rule and printed text are reviewed when its row was decided, and its page only by its own year's decision.
- A course's title, credits, NQF level and term are never shown, so they're always accepted without review.
- No row shows a meeting, so every timetable and workbook meeting is accepted without review. A workbook meeting's book and page are reviewed when its course's requirement row was decided.
- An elective row shows a course's tab and summary, none of these fields, so it reviews nothing here.
- A held-out string the grammar reads is accepted without review, and one it refuses is reviewed, as SAGE would flag its draft. The entry's page is reviewed with any refused string.
- An item SAGE holds nothing from, such as Labs D27's EEE2041F, which the 2026 manifest leaves out, is not stored.

## Running it

From the repo root:

```
make atp1
```

It reads the held-out drafts from `results/` and calls no model, then writes every CSV and `results/report.md`. It takes about two minutes, most of them reading the two handbooks. `make test` runs the harness's own tests, which read no source and call no model.

The held-out drafts were made once, on the first run, with Claude Haiku 5.5 through `backend/src/sage/ingestion/anthropic.py`, which main last held at 28717e7. SAGE now drafts with GPT-6 Luna, and the harness keeps no way to draft: its held-out drafts are its first result, and drafting them again would be a retest, on a branch of its own.

## Results

| File | Holds |
| --- | --- |
| `report.md` | The verdicts, then each measure's tables |
| `courses_2023.csv`, `courses_2026.csv`, `timetable.csv`, `complementary.csv`, `held_out.csv` | One row per labelled item and field: the label, SAGE's value, whether they match, the review status, whether it's a judgement call, and for a printed string the grammar's cause |
| `changes.csv` | Each labelled change, recalled or missed, and each flagged 2026 delta where the labels show no change of rule |
| `transcripts.csv` | Each row of the made-up transcripts, what the reader gave back, and every extra line or warning |
| `counts.csv`, `sittings.csv` | The 2023 to 2026 change count from `count_changes.py`, and CP2's review sittings |
| `drafts.json`, `refusals.json` | The held-out drafts as `translate` caches them, and every string the grammar refused, with the model's reply and what took its place |
| `inputs.csv` | The SHA-256 of every file the run read |

## Reading the report

Verdicts come first, then each measure's tables. A rate carries its 95% Wilson interval, and a count with none wrong gives the one-sided 95% upper bound, 1 − 0.05^(1/n). Each table is given for all rows and without the judgement calls. Requirement trees lead with the held-out set, which no build branch opened. The course sheets are an in-sample check, as the grammar was written from their fields.

The first result is committed on its own and kept. At the tag `atp1-result`, `make atp1` reproduces every file byte for byte from the cache, so `git status` shows any change. On later data it measures that data: from 2026's approval again on 24 October, the change count holds five more equivalences and the review minutes hold that day's sittings, so rerun the first result from that tag. A fault the run finds is logged in `docs/shortfalls.md` and fixed on its own branch, and its retest goes beside this result, in a folder of its own, never over it.
