# E2 results

From score.py, on 81 labelled validation strings.

## 1. The arms

| Arm | Stored unseen | Wrong unseen | Needing a person | Leaves to type or fix | Model right first time | Model same on 3 runs | Cost per pass (USD) | Time per pass (s) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Grammar only | 48 | 0 (below 6.1%) | 33 | 99 |  |  | 0.0000 | 0.0 |
| Model only: Claude Haiku 5.5 | 71 | 5 (7.0%) | 21 | 10 | 75 of 81 | 78 of 81 | 0.0351 | 142.7 |
| Model only: GPT-6 Luna | 71 | 11 (15.5%) | 25 | 10 | 66 of 81 | 73 of 81 | 0.0077 | 213.5 |
| Grammar first, Claude Haiku 5.5 drafts | 48 | 0 (below 6.1%) | 33 | 14 | 27 of 33 | 30 of 33 | 0.0171 | 78.8 |
| Grammar first, GPT-6 Luna drafts | 48 | 0 (below 6.1%) | 33 | 21 | 22 of 33 | 31 of 33 | 0.0048 | 114.0 |

Leaves are counted after the normal form merges repeated refer leaves. Counted with each refer apart, the leaves to type or fix are: Grammar only, 105; Model only: Claude Haiku 5.5, 13; Model only: GPT-6 Luna, 11; Grammar first, Claude Haiku 5.5 drafts, 14; Grammar first, GPT-6 Luna drafts, 21. The verdict is the same.
Rule 1, no wrong rule stored unseen: Grammar only; Grammar first, Claude Haiku 5.5 drafts; Grammar first, GPT-6 Luna drafts.
Rule 2, whatever is stored unseen is the same on every run: Grammar only; Grammar first, Claude Haiku 5.5 drafts; Grammar first, GPT-6 Luna drafts.
Rule 3, fewest strings needing a person, then fewest leaves to type or fix: Grammar first, Claude Haiku 5.5 drafts, with 33 strings and 14 leaves.
Verdict: Grammar first, Claude Haiku 5.5 drafts.
Drafting model, provisional for C1 until the advisor milestone: Claude Haiku 5.5. On their first runs over the 33 refusals, Claude Haiku 5.5 drafted 27 exactly right with 14 leaves to correct, and GPT-6 Luna 22 with 21.
McNemar's exact test, a finding rather than a decision: 7 refusals only Claude Haiku 5.5 drafted right and 2 only GPT-6 Luna, p = 0.180. It can't separate the models.

## 1b. The arms without the judgement rows

| Arm | Stored unseen | Wrong unseen | Needing a person | Leaves to type or fix | Model right first time | Model same on 3 runs | Cost per pass (USD) | Time per pass (s) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Grammar only | 48 | 0 (below 6.1%) | 19 | 58 |  |  | 0.0000 | 0.0 |
| Model only: Claude Haiku 5.5 | 61 | 3 (4.9%) | 12 | 6 | 64 of 67 | 65 of 67 | 0.0280 | 111.3 |
| Model only: GPT-6 Luna | 61 | 9 (14.8%) | 16 | 6 | 54 of 67 | 61 of 67 | 0.0056 | 163.3 |
| Grammar first, Claude Haiku 5.5 drafts | 48 | 0 (below 6.1%) | 19 | 10 | 16 of 19 | 17 of 19 | 0.0101 | 47.3 |
| Grammar first, GPT-6 Luna drafts | 48 | 0 (below 6.1%) | 19 | 19 | 10 of 19 | 19 of 19 | 0.0027 | 63.8 |

With the 14 judgement rows in labels-notes.md left out (rows 8, 12, 24, 33, 42, 46, 56, 58, 59, 60, 62, 75, 76, 79), 67 strings remain, and the verdict is the same: Grammar first, Claude Haiku 5.5 drafts.

## 2. Refusals by the grammar's ten causes

| Cause | Development (of 58) | Validation (of 81) | Claude Haiku 5.5 drafts right | GPT-6 Luna drafts right |
| --- | --- | --- | --- | --- |
| refused_school_result | 2 | 0 | 0 | 0 |
| refused_programme | 2 | 0 | 0 | 0 |
| refused_year_of_study | 1 | 2 | 1 | 2 |
| refused_mark_threshold | 3 | 0 | 0 | 0 |
| refused_or_equivalent | 7 | 2 | 2 | 2 |
| refused_code_without_term | 1 | 0 | 0 | 0 |
| refused_free_text | 1 | 20 | 16 | 11 |
| refused_punctuation | 1 | 4 | 4 | 4 |
| refused_mixed_and_or | 1 | 5 | 4 | 3 |
| refused_other | 0 | 0 | 0 | 0 |
| All refusals | 19 | 33 | 27 | 22 |

The grammar reads 48 of the 81 validation strings (59.3%) and refuses 33, most for refused_free_text (20).
Development evidence only: it reads 39 of the 58 fields it was written from (67.2%).

## 3. Node kinds in the labels

| Node | Strings using it | Nodes in the labels |
| --- | --- | --- |
| all | 40 | 42 |
| any | 21 | 33 |
| course, need pass | 45 | 131 |
| course, need concurrent | 22 | 36 |
| course, need mark | 0 | 0 |
| student_in | 0 | 0 |
| min_year_of_study | 1 | 1 |
| refer | 21 | 28 |
| refer asking for a DP | 11 | 16 |
| no rule (null) | 1 | 1 |

Every one of the 81 labels fits the CP0 node types. 21 strings (25.9%) need a refer leaf, and 11 of them ask for a DP, the first leaf SAGE would need for another department.
