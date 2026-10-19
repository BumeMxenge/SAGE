# ATP-1: how well ingestion reads print

report.py wrote this from the CSVs beside it, which run.py wrote. The labels in `../labels/` were written from print and committed before any run. A rate has its 95% Wilson interval in brackets, and a count with none wrong gives the one-sided 95% upper bound, 1 − 0.05^(1/n). Each table is given for all rows and without the judgement calls: labels whose Note records a judgement, or marked Ambiguous. Tables that compare nothing with a label, such as the refusals, the minutes and the change count, have none to leave out. Verdicts are on all rows.

## Verdicts

| Measure | All rows | Without judgement calls | Target | Verdict |
| --- | --- | --- | --- | --- |
| Wrong items accepted without review, all five sheets | 0 of 1413 (95% upper bound 0.2%) | 0 of 1218 (95% upper bound 0.2%) | 0 | met |
| Held out: wrong strings accepted without review | 0 of 61 (95% upper bound 4.8%) | 0 of 56 (95% upper bound 5.2%) | 0 | met |
| Delta recall: titles, credits, NQF levels, terms and rules changed, and courses added or removed | 32 of 32, 100.0% (89.3% to 100.0%) | 24 of 24, 100.0% (86.2% to 100.0%) | 100% | met |
| Transcript rows recovered or flagged | 66 of 66, 100.0% (94.5% to 100.0%); 0 dropped | no judgement calls | 100%, none dropped | met |
| Transcript rows recovered alone | 66 of 66, 100.0% (94.5% to 100.0%) | no judgement calls |  | reported |
| Items accepted without review, all five sheets | 1413 of 1614, 87.5% (85.8% to 89.1%) | 1218 of 1310, 93.0% (91.5% to 94.2%) |  | reported |
| Items sent to review, all five sheets | 196 of 1614, 12.1% (10.6% to 13.8%) | 92 of 1310, 7.0% (5.8% to 8.5%) |  | reported |
| Held out: strings accepted without review | 61 of 68, 89.7% (80.2% to 94.9%) | 56 of 56, 100.0% (93.6% to 100.0%) |  | reported |
| Wording changes: flagged, though the rule didn't change | 0 | 0 |  | reported |
| False alarms: flagged, though neither rule nor wording changed | 0 | 0 |  | reported |

## Accepted without review, by sheet

An item is one labelled field of one row. It counts as reviewed when a decided review row showed it, in its year or in 2023 when unchanged since. A held-out string counts as reviewed when the grammar refused it.

| Sheet | Items | Accepted without review | Reviewed | Not stored | Wrong among accepted |
| --- | --- | --- | --- | --- | --- |
| Held out | 192 | 171 of 192, 89.1% (83.9% to 92.7%) | 21 | 0 | 0 of 171 (95% upper bound 1.7%) |
| Courses 2026 | 421 | 370 of 421, 87.9% (84.4% to 90.7%) | 51 | 0 | 0 of 370 (95% upper bound 0.8%) |
| Courses 2023 | 461 | 393 of 461, 85.2% (81.7% to 88.2%) | 68 | 0 | 0 of 393 (95% upper bound 0.8%) |
| Timetable | 300 | 295 of 300, 98.3% (96.2% to 99.3%) | 0 | 5 | 0 of 295 (95% upper bound 1.0%) |
| Complementary | 240 | 184 of 240, 76.7% (70.9% to 81.6%) | 56 | 0 | 0 of 184 (95% upper bound 1.6%) |

Without judgement calls:

| Sheet | Items | Accepted without review | Reviewed | Not stored | Wrong among accepted |
| --- | --- | --- | --- | --- | --- |
| Held out | 160 | 160 of 160, 100.0% (97.7% to 100.0%) | 0 | 0 | 0 of 160 (95% upper bound 1.9%) |
| Courses 2026 | 343 | 313 of 343, 91.3% (87.8% to 93.8%) | 30 | 0 | 0 of 313 (95% upper bound 1.0%) |
| Courses 2023 | 397 | 357 of 397, 89.9% (86.6% to 92.5%) | 40 | 0 | 0 of 357 (95% upper bound 0.8%) |
| Timetable | 290 | 290 of 290, 100.0% (98.7% to 100.0%) | 0 | 0 | 0 of 290 (95% upper bound 1.0%) |
| Complementary | 120 | 98 of 120, 81.7% (73.8% to 87.6%) | 22 | 0 | 0 of 98 (95% upper bound 3.0%) |

## Requirement trees

The held-out set is the headline: no build branch opened Chemical Engineering or Construction Economics. The course sheets are an in-sample check, as the grammar was written from their fields.

| Set | Right | Accepted without review | Wrong among them | Reviewed | Right among reviewed |
| --- | --- | --- | --- | --- | --- |
| Held out, per string | 68 of 68, 100.0% (94.7% to 100.0%) | 61 | 0 of 61 (95% upper bound 4.8%) | 7 | 7 of 7, 100.0% (64.6% to 100.0%) |
| Courses 2026, per course | 59 of 59, 100.0% (93.9% to 100.0%) | 40 | 0 of 40 (95% upper bound 7.2%) | 19 | 19 of 19, 100.0% (83.2% to 100.0%) |
| Courses 2023, per course | 65 of 65, 100.0% (94.4% to 100.0%) | 44 | 0 of 44 (95% upper bound 6.6%) | 21 | 21 of 21, 100.0% (84.5% to 100.0%) |

Without judgement calls:

| Set | Right | Accepted without review | Wrong among them | Reviewed | Right among reviewed |
| --- | --- | --- | --- | --- | --- |
| Held out, per string | 56 of 56, 100.0% (93.6% to 100.0%) | 56 | 0 of 56 (95% upper bound 5.2%) | 0 | none to count |
| Courses 2026, per course | 48 of 48, 100.0% (92.6% to 100.0%) | 37 | 0 of 37 (95% upper bound 7.8%) | 11 | 11 of 11, 100.0% (74.1% to 100.0%) |
| Courses 2023, per course | 56 of 56, 100.0% (93.6% to 100.0%) | 44 | 0 of 44 (95% upper bound 6.6%) | 12 | 12 of 12, 100.0% (75.8% to 100.0%) |

Held-out strings the grammar refused: 7. Drafts kept: 7, of which exactly right: 7 of 7, 100.0% (64.6% to 100.0%). Drafts that weren't rule trees, so a refer leaf of the printed words took their place: 0. A person reviews each refused string either way.

## Held out: right, by field

| Field | All rows | Without judgement calls |
| --- | --- | --- |
| page | 56 of 56, 100.0% (93.6% to 100.0%) | 48 of 48, 100.0% (92.6% to 100.0%) |
| requirement | 56 of 56, 100.0% (93.6% to 100.0%) | 48 of 48, 100.0% (92.6% to 100.0%) |
| requirement_tree | 56 of 56, 100.0% (93.6% to 100.0%) | 48 of 48, 100.0% (92.6% to 100.0%) |
| corequisite | 12 of 12, 100.0% (75.8% to 100.0%) | 8 of 8, 100.0% (67.6% to 100.0%) |
| corequisite_tree | 12 of 12, 100.0% (75.8% to 100.0%) | 8 of 8, 100.0% (67.6% to 100.0%) |

## Courses 2026: right, by field

| Field | All rows | Without judgement calls |
| --- | --- | --- |
| title | 59 of 59, 100.0% (93.9% to 100.0%) | 48 of 48, 100.0% (92.6% to 100.0%) |
| credits | 59 of 59, 100.0% (93.9% to 100.0%) | 48 of 48, 100.0% (92.6% to 100.0%) |
| nqf_level | 59 of 59, 100.0% (93.9% to 100.0%) | 48 of 48, 100.0% (92.6% to 100.0%) |
| term | 59 of 59, 100.0% (93.9% to 100.0%) | 48 of 48, 100.0% (92.6% to 100.0%) |
| entry_rule | 59 of 59, 100.0% (93.9% to 100.0%) | 48 of 48, 100.0% (92.6% to 100.0%) |
| page | 59 of 59, 100.0% (93.9% to 100.0%) | 48 of 48, 100.0% (92.6% to 100.0%) |
| requirement | 59 of 59, 100.0% (93.9% to 100.0%) | 48 of 48, 100.0% (92.6% to 100.0%) |
| corequisite | 7 of 7, 100.0% (64.6% to 100.0%) | 6 of 6, 100.0% (61.0% to 100.0%) |
| entry | 1 of 1, 100.0% (20.7% to 100.0%) | 1 of 1, 100.0% (20.7% to 100.0%) |

## Courses 2023: right, by field

| Field | All rows | Without judgement calls |
| --- | --- | --- |
| title | 65 of 65, 100.0% (94.4% to 100.0%) | 56 of 56, 100.0% (93.6% to 100.0%) |
| credits | 65 of 65, 100.0% (94.4% to 100.0%) | 56 of 56, 100.0% (93.6% to 100.0%) |
| nqf_level | 65 of 65, 100.0% (94.4% to 100.0%) | 56 of 56, 100.0% (93.6% to 100.0%) |
| term | 65 of 65, 100.0% (94.4% to 100.0%) | 56 of 56, 100.0% (93.6% to 100.0%) |
| entry_rule | 65 of 65, 100.0% (94.4% to 100.0%) | 56 of 56, 100.0% (93.6% to 100.0%) |
| page | 65 of 65, 100.0% (94.4% to 100.0%) | 56 of 56, 100.0% (93.6% to 100.0%) |
| requirement | 65 of 65, 100.0% (94.4% to 100.0%) | 56 of 56, 100.0% (93.6% to 100.0%) |
| corequisite | 6 of 6, 100.0% (61.0% to 100.0%) | 5 of 5, 100.0% (56.6% to 100.0%) |

## Timetable: right, by field

| Field | All rows | Without judgement calls |
| --- | --- | --- |
| course | 60 of 60, 100.0% (94.0% to 100.0%) | 58 of 58, 100.0% (93.8% to 100.0%) |
| day | 60 of 60, 100.0% (94.0% to 100.0%) | 58 of 58, 100.0% (93.8% to 100.0%) |
| start | 60 of 60, 100.0% (94.0% to 100.0%) | 58 of 58, 100.0% (93.8% to 100.0%) |
| end | 60 of 60, 100.0% (94.0% to 100.0%) | 58 of 58, 100.0% (93.8% to 100.0%) |
| term | 60 of 60, 100.0% (94.0% to 100.0%) | 58 of 58, 100.0% (93.8% to 100.0%) |

## Complementary: right, by field

| Field | All rows | Without judgement calls |
| --- | --- | --- |
| days | 40 of 40, 100.0% (91.2% to 100.0%) | 20 of 20, 100.0% (83.9% to 100.0%) |
| start | 40 of 40, 100.0% (91.2% to 100.0%) | 20 of 20, 100.0% (83.9% to 100.0%) |
| end | 40 of 40, 100.0% (91.2% to 100.0%) | 20 of 20, 100.0% (83.9% to 100.0%) |
| kind | 40 of 40, 100.0% (91.2% to 100.0%) | 20 of 20, 100.0% (83.9% to 100.0%) |
| book | 40 of 40, 100.0% (91.2% to 100.0%) | 20 of 20, 100.0% (83.9% to 100.0%) |
| page | 40 of 40, 100.0% (91.2% to 100.0%) | 20 of 20, 100.0% (83.9% to 100.0%) |

## Changes from 2023 to 2026

Labelled changes come from the two course sheets alone, on the courses they hold. Recall counts each rule field a course sheet labels: the title, ignoring case, the credits, the NQF level, the term and the rule, compared in normal form, and a course added or removed. A change is recalled when SAGE's 2026 review records a delta for that course and field, flagged or not: 32 of 32, 100.0% (89.3% to 100.0%) of all, and 24 of 24, 100.0% (86.2% to 100.0%) without judgement calls.

| Course | Field | Change | 2023 label | 2026 label | Flag | Outcome | Judgement call |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ASL1200S | course | removed |  |  | removed | recalled | no |
| CSC1016S | entry_rule | changed | {"any": [{"course": "CSC1015F", "min_mark": 45, "need": "mark"}, {"course": "CSC1017F", "min_mark": 70, "need": "mark"}]} | {"any": [{"course": "CSC1015F", "need": "pass"}, {"course": "CSC1017S", "min_mark": 60, "need": "mark"}]} | refused_mark_threshold | recalled | yes |
| CSC2001F | entry_rule | changed | {"any": [{"all": [{"course": "CSC1015F", "need": "pass"}, {"course": "CSC1016S", "need": "pass"}]}, {"all": [{"course": "CSC1010H", "need": "pass"}, {"course": "CSC1011H", "need": "pass"}]}]} | {"any": [{"all": [{"any": [{"course": "CSC1015F", "need": "pass"}, {"course": "CSC1015S", "need": "pass"}]}, {"course": "CSC1016S", "need": "pass"}]}, {"all": [{"course": "CSC1010H", "need": "pass"}, {"course": "CSC1011H", "need": "pass"}]}]} | check_failed | recalled | no |
| CSC2004Z | entry_rule | changed | {"any": [{"all": [{"course": "CSC1015F", "need": "pass"}, {"course": "CSC1016S", "need": "pass"}]}, {"all": [{"course": "CSC1010H", "need": "pass"}, {"course": "CSC1011H", "need": "pass"}]}]} | {"any": [{"all": [{"any": [{"course": "CSC1015F", "need": "pass"}, {"course": "CSC1015S", "need": "pass"}]}, {"course": "CSC1016S", "need": "pass"}]}, {"all": [{"course": "CSC1010H", "need": "pass"}, {"course": "CSC1011H", "need": "pass"}]}]} | check_failed | recalled | no |
| CSC3002F | title | changed | COMPUTER SCIENCE 3002 | NETWORKS AND OPERATING SYSTEMS | refused_or_equivalent | recalled | yes |
| CSC3002F | entry_rule | changed | {"all": [{"course": "CSC2001F", "need": "pass"}, {"course": "CSC2002S", "need": "pass"}, {"any": [{"all": [{"course": "MAM1004F", "need": "pass"}, {"course": "MAM1008S", "need": "pass"}]}, {"course": "MAM1000W", "need": "pass"}, {"all": [{"course": "MAM1031F", "need": "pass"}, {"course": "MAM1032S", "need": "pass"}]}, {"refer": "or equivalent"}]}, {"refer": "CSC2004Z is required if CSC2002S was passed after 2017."}]} | {"all": [{"course": "CSC2001F", "need": "pass"}, {"course": "CSC2002S", "need": "pass"}, {"course": "CSC2004Z", "need": "pass"}, {"any": [{"all": [{"course": "MAM1004F", "need": "pass"}, {"course": "MAM1008S", "need": "pass"}]}, {"course": "MAM1000W", "need": "pass"}, {"course": "MAM1031F", "need": "pass"}, {"refer": "or equivalent"}]}]} | refused_or_equivalent | recalled | yes |
| CSC3003S | title | changed | COMPUTER SCIENCE 3003 | ADVANCED PROGRAMMING & ALGORITHMS | refused_or_equivalent | recalled | yes |
| CSC3003S | entry_rule | changed | {"all": [{"course": "CSC2001F", "need": "pass"}, {"course": "CSC2002S", "need": "pass"}, {"any": [{"all": [{"course": "MAM1004F", "need": "pass"}, {"course": "MAM1008S", "need": "pass"}]}, {"course": "MAM1000W", "need": "pass"}, {"all": [{"course": "MAM1031F", "need": "pass"}, {"course": "MAM1032S", "need": "pass"}]}, {"refer": "or equivalent"}]}, {"any": [{"course": "INF2009F", "need": "pass"}, {"refer": "permission from the Head of Department to do compensation work to a satisfactory standard."}]}, {"refer": "CSC2004Z is required if CSC2002S was passed after 2017."}]} | {"all": [{"course": "CSC2001F", "need": "pass"}, {"course": "CSC2002S", "need": "pass"}, {"course": "CSC2004Z", "need": "pass"}, {"any": [{"all": [{"course": "MAM1004F", "need": "pass"}, {"course": "MAM1008S", "need": "pass"}]}, {"course": "MAM1000W", "need": "pass"}, {"course": "MAM1031F", "need": "pass"}, {"refer": "or equivalent"}]}]} | refused_or_equivalent | recalled | yes |
| CSC3023F | course | removed |  |  | removed | recalled | yes |
| CSC3024S | course | added |  |  | refused_or_equivalent | recalled | yes |
| EEE1006F | course | removed |  |  | removed | recalled | no |
| EEE1007S | course | removed |  |  | removed | recalled | no |
| EEE1008F | course | added |  |  |  | recalled | no |
| EEE1009S | course | added |  |  |  | recalled | no |
| EEE2046F | entry_rule | changed | {"any": [{"all": [{"course": "EEE1006F", "need": "pass"}, {"course": "CSC1015F", "need": "pass"}]}, {"all": [{"course": "EEE2042S", "need": "pass"}, {"course": "CSC1019F", "need": "pass"}]}]} | {"any": [{"all": [{"course": "EEE1006F", "need": "pass"}, {"any": [{"course": "CSC1015F", "need": "pass"}, {"course": "CSC1015S", "need": "pass"}]}]}, {"all": [{"course": "EEE2042S", "need": "pass"}, {"course": "CSC1019F", "need": "pass"}]}]} |  | recalled | yes |
| EEE2048F | course | removed |  |  | removed | recalled | no |
| EEE2048S | course | added |  |  |  | recalled | no |
| EEE2051L | course | removed |  |  | removed | recalled | no |
| EEE3088F | entry_rule | changed | {"all": [{"course": "EEE2045F", "need": "pass"}, {"course": "EEE2047S", "need": "pass"}]} | {"any": [{"course": "EEE2045F", "need": "pass"}, {"course": "EEE2046F", "need": "pass"}, {"course": "EEE2046S", "need": "pass"}]} |  | recalled | no |
| EEE3093S | entry_rule | changed | {"course": "EEE2046F", "need": "pass"} | {"any": [{"course": "EEE2046F", "need": "pass"}, {"course": "EEE2046S", "need": "pass"}]} |  | recalled | no |
| EEE3096S | entry_rule | changed | {"course": "EEE2046F", "need": "pass"} | {"any": [{"course": "EEE2046F", "need": "pass"}, {"course": "EEE2046S", "need": "pass"}]} |  | recalled | no |
| EEE3097S | entry_rule | changed | {"all": [{"course": "EEE2045F", "need": "pass"}, {"course": "EEE2047S", "need": "pass"}, {"course": "EEE3088F", "need": "pass"}]} | {"course": "EEE3088F", "need": "pass"} |  | recalled | no |
| EEE3098S | entry_rule | changed | {"all": [{"course": "EEE2045F", "need": "pass"}, {"course": "EEE2047S", "need": "pass"}, {"course": "EEE3088F", "need": "pass"}]} | {"course": "EEE3088F", "need": "pass"} |  | recalled | no |
| EEE3099S | entry_rule | changed | {"all": [{"course": "EEE2045F", "need": "pass"}, {"course": "EEE2047S", "need": "pass"}, {"course": "EEE3088F", "need": "pass"}]} | {"course": "EEE3088F", "need": "pass"} |  | recalled | no |
| EEE4022S | entry_rule | changed | {"any": [{"course": "EEE4114F", "need": "pass"}, {"course": "EEE4126F", "need": "pass"}, {"course": "EEE4117F", "need": "pass"}, {"course": "EEE4118F", "need": "pass"}, {"course": "EEE4121F", "need": "pass"}]} | {"any": [{"course": "EEE4114F", "need": "pass"}, {"course": "EEE4126F", "need": "pass"}, {"course": "EEE4117F", "need": "pass"}, {"course": "EEE4118F", "need": "pass"}, {"course": "EEE4121F", "need": "pass"}, {"course": "EEE4120F", "need": "pass"}, {"course": "EEE4119F", "need": "pass"}]} |  | recalled | no |
| EEE4105C | course | removed |  |  | removed | recalled | no |
| EEE4122C | course | removed |  |  | removed | recalled | no |
| EEE4123C | course | removed |  |  | removed | recalled | no |
| EEE4125C | entry_rule | changed |  | {"any": [{"course": "EEE3097S", "need": "pass"}, {"course": "EEE3098S", "need": "pass"}, {"course": "EEE3099S", "need": "pass"}]} |  | recalled | no |
| HUB2005F | course | removed |  |  | removed | recalled | no |
| HUB4045F | course | removed |  |  | removed | recalled | no |
| HUB4049F | course | added |  |  |  | recalled | no |

Flagged 2026 deltas where the labels show no change of rule: a wording change where the labelled requirement or co-requisite text changed, and otherwise a false alarm.

None.

## Refusals by cause

Each printed requirement and co-requisite as SAGE's handbook reader read it, through the grammar, once per course that prints it.

| Cause | Courses 2023 | Courses 2026 | Held out |
| --- | --- | --- | --- |
| read | 42 | 39 | 48 |
| refused_or_equivalent | 8 | 9 | 0 |
| refused_free_text | 1 | 0 | 6 |
| refused_mark_threshold | 2 | 2 | 0 |
| refused_school_result | 2 | 2 | 0 |
| refused_mixed_and_or | 1 | 1 | 1 |
| refused_programme | 2 | 1 | 0 |
| refused_code_without_term | 1 | 1 | 0 |
| refused_punctuation | 1 | 1 | 0 |
| refused_year_of_study | 1 | 1 | 0 |
| Refused | 19 of 61, 31.1% (20.9% to 43.6%) | 18 of 57, 31.6% (21.0% to 44.5%) | 7 of 55, 12.7% (6.3% to 24.0%) |

## The review a new department would need

Held-out entries with a printed string the grammar refused: 7 of 56, 12.5% (6.2% to 23.6%). SAGE reviews one row per distinct printed line, so Chemical Engineering's and Construction Economics' first year would bring review rows: 7. At CP2's pace of 0.72 minutes a decision (86.8 minutes over 121 decisions), that's about 5 minutes. At that rate, a department printing n entries brings about 0.12n review rows, fewer where entries share a line.

## Review minutes at CP2

`sage review` timed each sitting, and the ingestion README records them.

| Year | Sittings | Minutes | Decisions | Minutes a decision |
| --- | --- | --- | --- | --- |
| 2023 | 3 | 46.2 | 34 | 1.36 |
| 2026 | 1 | 40.6 | 87 | 0.47 |

## What changed between the approved years

From `experiments/ingestion/count_changes.py`, on both approved snapshots. Conveners aren't rules, so they're counted apart.

| Kind | Added | Removed | Changed |
| --- | --- | --- | --- |
| Entry rules | 67 | 7 | 13 |
| Curriculum rules | 0 | 0 | 13 |
| Course list entries | 136 | 55 | 0 |
| Courses | 111 | 11 | 2 |
| Equivalences | 5 | 0 | 0 |
| Conveners |  |  | 37 |

## Transcripts

Made-up records: 3, drawn with seed 4022, printed as `backend/tests/pdf.py` prints PDFs and read by SAGE's transcript reader. Unverified lines and rows covered only by their year's Term GPA warning are flagged. A row with neither, read wrongly or not at all, is dropped.

| Kind | Rows | Recovered | Unverified | GPA warning | Dropped |
| --- | --- | --- | --- | --- | --- |
| fail | 3 | 3 | 0 | 0 | 0 |
| dp_refused | 3 | 3 | 0 | 0 | 0 |
| in_progress | 9 | 9 | 0 | 0 | 0 |
| pass | 45 | 45 | 0 | 0 | 0 |
| repeat | 3 | 3 | 0 | 0 | 0 |
| supp_pending | 3 | 3 | 0 | 0 | 0 |
| All | 66 | 66 | 0 | 0 | 0 |

Lines no printed row accounts for: 0. Warnings, which a made-up record should never raise: 0.

## Not stored

Labelled items SAGE holds nothing from, such as a timetable cell whose course the 2026 manifest leaves out. Each is still scored against the reader, and counts as neither accepted nor reviewed.

| Sheet | Item | Course |
| --- | --- | --- |
| Timetable | Labs!D27 | EEE2041F |

## Not run

Reproducing a 2023 decision while 2026 is current needs the engine, so it runs in the engine milestone and is reported beside this result.

## Disagreements

Every labelled field where SAGE and the label differ. Row is the sheet's row.

None.

Every transcript row not recovered, every extra line and every warning:

None.

## Inputs

The SHA-256 of every file the run read.

| File | SHA-256 |
| --- | --- |
| `tests/acceptance/atp1/labels/courses_2026.xlsx` | `d249408e63c173e837aff238dcf7fff8566d0ff5e23dccb2fd512ef67c596027` |
| `tests/acceptance/atp1/labels/courses_2023.xlsx` | `157d223736904b034392bf7f1d3d8e38ebded36de5fb037a1677960da4978a0b` |
| `tests/acceptance/atp1/labels/timetable.xlsx` | `393ef7ce4fa5abc5f2f59c63b4d2da90ce27d99fb8a1e1c3c4b4ff40e3c7596c` |
| `tests/acceptance/atp1/labels/complementary.xlsx` | `f6c067b401fc5d690fa146896d46de8a712b48375ad0dc990be2a101aae07324` |
| `tests/acceptance/atp1/labels/held_out.xlsx` | `aa31329b2303ef0940de96ffd6652759eb05087a022ad424b37cdd1a8232e3f2` |
| `data/sources/2023/EBE_2023.pdf` | `caf79a53f82b5657e8022febc9f903c66ab56955b2a1f2bf9ced2412499a969f` |
| `data/sources/2026/EBE_2026.pdf` | `796ffd0b5754995b8c875e2cc8912fdda818077fb8c035f2f8d1fb42a26e2e9f` |
| `data/sources/2026/2026_timetable.xlsx` | `45de2ef0621f93b6974b06775f73d99d69ea8cec999c1d412c563b589a27181a` |
| `data/sources/2026/2026_Complementary_Studies_Course_Details.xlsx` | `85a1df054b9246b7c01dcb6b16bf587d78d46abda844c73a2612be96d97e829f` |
| `data/rules/2023/rulebook.json` | `a3d116935d2fd9d8bbcd2b323f971a03402c014771d3258ccc2f5aae04b84202` |
| `data/rules/2026/rulebook.json` | `27610b243e5c2e8886ccd0517581441e3187c47d97692e8e0fa9c279f1ff0066` |
| `data/rules/2023/review.json` | `f02c6eab1b98c018f5b9698ba67bcc6e7e7e09bd86d2e98ff1b8cd4086659b3f` |
| `data/rules/2026/review.json` | `fb0657ce721a7578fef86f435f6b5850a0d5c689957733ced01671069df2ea57` |
| `tests/acceptance/atp1/results/drafts.json` | `53a353976dc735aa5c256be806b7bfd6100da01f8adce010a155434d2547bec2` |
| `tests/acceptance/atp1/results/refusals.json` | `df535a5bd552ca710235614abe1c65029ad91c0a4badfaa6585a6c3be48a901f` |
