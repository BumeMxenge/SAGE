# ATP-2 label format (reviewed against cited sources)

Files land in `tests/acceptance/atp2/labels/` on `test/check-plans-and-eligibility`.

## records/<record>.json
One file per record, in the shape of `data/synthetic/mbali.json`, with only these keys:
```json
{
  "_readme": ["One line: what this record tests, and that it is made up."],
  "students": [{"curriculum_code": "EB009EEE01", "intake_year": 2024, "onboarding_complete": true}],
  "course_history": [
    {"academic_year": 2024, "term": "sem1", "course_code": "MAM1020F", "course_name": "Mathematics 1A for Engineers",
     "credits": 18, "nqf_level": 5, "result": "2+", "mark": 72}
  ]
}
```
- `term` is one of sem1, sem2, full_year, q1, q2, q3, q4, winter, summer, or other. X courses use other because print does not assign them a semester (p. 11; EEE1000X p. 129; EEE3000X p. 133).
- `result` is a UCT symbol from the result_symbols migration: 1, 2+, 2-, 3, PA, SP, UP (pass); F, SF, UF, SM, AB, INC (fail); FS, OSS, DE (supplementary pending); DPR (DP refused); GIP, OS (in progress); CR, EX, CX (credited); EXC, ATT, LOA, EXA (not counted).
- `mark` is an integer, or null where a symbol prints none (DPR, GIP, CR and the like).
- Course names, credits and NQF levels come from the 2026 handbook entry. Marks are made up but plausible.
- Every pass needed for an on-path history is there, year by year, from the printed curriculum table. Nothing is copied from Mbali, Ziyela or any other seed.

## records.csv
One row per record.

| Column | Holds |
|---|---|
| record | The file's stem, such as `signals1-failed` |
| curriculum_code | As printed |
| intake_year | Integer |
| student_type | S1, S2, S3 or S4 (Table 3.1) |
| tests | One sentence: what it tests |
| year_of_study | The year FB5 gives under the semantics, as an integer |
| owed_core | Space-separated codes of every outstanding core course from her year and earlier, as the semantics defines it, before exclusions |
| excluded_core | Space-separated codes of core courses she can't take, by entry rule or FB3.4 |
| expected_plans | Integer, or blank where the set is too large to label by hand |
| expected_combinations | Each plan's electives as codes joined by `+`, plans separated by `;`, `none` for a plan with no electives. Blank when expected_plans is blank |
| expected_slots | Each slot as `kind:credits`, such as `complementary:18` or `place:ASL1200S:8`, separated by `;`, or blank |
| expected_set_reasons | The set-level reasons print requires, as `kind:subject`, such as `conflict:FB3.4 leaves MEC2045S out` or `conditional:FB7 supplementary in EEE3094S`, separated by `; ` (a semicolon and a space). A subject may itself hold a colon, so split each reason at its first colon |
| pages | Printed pages relied on, such as `57; 14; 132` |
| assumptions | Which semantics assumptions the labels lean on, by their wording, or blank |
| judgement_call | yes or no |
| note | Anything a checker of the labels should know |

## decisions.csv
One row per focal decision. About five a record, chosen where the answer isn't obvious.

| Column | Holds |
|---|---|
| record | As in records.csv |
| course_code | The course decided |
| course_name | As printed |
| expected_status | eligible, check or not_eligible, as the semantics' Eligibility statuses define them |
| deciding_rule | The printed rule that decides it, in plain words, naming the course codes involved |
| deciding_codes | Space-separated codes the reason must name, or blank. Where print gives a code with no term letter, such as ECO1010 in ECO2007S's rule, the printed stem is used, so match it as text |
| page | The printed page of the deciding rule. For a complementary course outside the EBE handbook, the other handbook's name and printed page, from the complementary workbook, so this column isn't always an integer |
| assumption | The semantics assumption it leans on, or blank |
| judgement_call | yes or no |
| note | Optional |

Printed page numbers are the handbook's own. The PDF's run one ahead.

## Review before freezing

All six records and all 32 focal decisions were checked against the cited sources on 26 October 2026, then checked again against print the same evening. `REVIEW.md` records the corrections from both checks, source versions, coverage and retained judgement calls. The labels have not been committed by this review. Freeze them with the ATP-2 commit before the first engine run.
