# ATP-2 source review, 26 October 2026

Reviewed all six records in the supplied order and all 32 focal decisions. In this first pass, no expected status, deciding code, year of study, exclusion, plan count, combination or judgement-call flag changed, and `records.csv` and all six student JSON files were byte-for-byte unchanged. A second check the same evening changed one deciding code and two notes; see the last section. The six student JSON files are still unchanged.

## Corrections

| File and row | Field | Before | After and evidence |
|---|---|---|---|
| `decisions.csv`, row 29, `owes-asl-dp-refused / CSC2001F` | `page` | 169 | 170. The course heading starts on printed p. 169, but the entry requirement is at the top of printed p. 170, PDF page 171. The note records this correction. |
| `decisions.csv`, row 26, `aspect-final-supp / HUB4049F` | `note` | A referral reading and a literal fourth-year-only reading both described as `check` | Referral gives `check`; a literal fourth-year-only rule gives `not_eligible` in year 5. Retained the drafted `eligible` judgement call, supported by the fifth-year elective table on p. 61. The entry wording is on p. 162. |
| `NOTES.md`, record 6 | CSC2001F references | p. 169 | p. 170 for the entry requirement. Added a review summary that distinguishes FB5's printed wording from the specification's progression interpretation. |
| `README.md` | `term` format | Omitted `other` | Added the existing `other` value used for X courses, with source pages. No student record changed. Added the review state and link to these notes. |

CSV row numbers include the header. Unchanged CSV rows retain their original bytes and quoting.

## Record coverage

| Record | Story and year-of-study check | Focal decisions checked | Plan count retained |
|---|---|---|---|
| `signals1-failed` | EEE2047S: F 41 in 2024 and F 44 in 2025. Nine of ten second-year and six of nine third-year core courses passed; year 3 under the specification. | 6, EBE pp. 132, 134, 135, 138 and complementary workbook `Courses!G26`, `M26:N26`. The failed prerequisite blocks EEE3090F, EEE3092F and EEE3094S. ECO2007S requires a check for equivalence. | 1 |
| `power-repeat-clash` | EEE2044S: F 44 in 2024 and F 38 in 2025. Nine of ten second-year and six of nine third-year core courses passed; year 3. | 5, EBE pp. 130, 134, 136, 148 and complementary workbook `Courses!G9`, `M9:N9`. EEE3096S and MEC2045S meet entry rules outside a plan; their exclusions arise from clashes. | 1 |
| `aspect-maths-physics` | MAM1020F F 36 and PHY1012F F 38 in 2024. Subsequent ASPECT passes and the stated covers complete years 1 and 2; year 3. Retained the existing historical assumptions and judgement flag. | 5, EBE pp. 130, 131, 135, 183, 184, 191 and source `equivalences.csv`. Offering and equivalence covers support the statuses. | 1 |
| `embedded1-failed` | EEE2046F: F 38 in 2024 and DPR with no mark in 2025. Nine of ten second-year and four of seven third-year core courses passed; year 3. | 5, EBE pp. 132, 135, 136, 170. EEE3096S, EEE3093S and CSC2002S fail entry rules outside a plan, although same-year prerequisites can meet them in a plan. EEE2046S remains eligible from print and documented as a known coverage gap. | 3 |
| `aspect-final-supp` | EEE3094S: F 38 in 2024 and FS 46 in 2025. The pending supplementary completes year 3 for progression under the specification; year 4 core is complete, giving year 5. | 6, EBE pp. 135, 138, 139, 140, 162. Pending EEE3094S makes EEE4118F and EEE4119F `check`; EEE4114F is met through EEE3092F. | 12 |
| `owes-asl-dp-refused` | CSC1016S: DPR with no mark in 2024 and 2025. Six of seven second-year and five of six third-year core courses passed; one fourth-year pass does not advance the year under the specification. Year 3. | 5, EBE pp. 133, 137, 168, 170. CSC2001F is blocked by CSC1016S; its semester-2 repeat cannot satisfy a semester-1 prerequisite in the same plan. | 1 |

## Clash evidence

Checked all occurrences of the named courses on the relevant curriculum sheet and on `Labs`, including merged cells and the laboratory choices.

| Record | Source cells and shared time | Result retained |
|---|---|---|
| `signals1-failed` | `EB009!K23:K24,N23:N24` EEE2047S against `K39:K40,N39:N40` EEE3094S: Monday and Thursday 10:00-11:45. | Mandatory lectures overlap. EEE3094S is excluded by its prerequisite first, so no FB3.4 reason is expected. |
| `power-repeat-clash` | `EB011!L23:L24,M23:M24` EEE2044S against `L39:L40,M39:M40` EEE3096S: Tuesday and Wednesday 10:00-11:45. `K27:K28` EEE2044S against `K43:K44` MEC2045S: Monday 14:00-15:45. | Two mandatory overlaps. EEE3096S's Wednesday/Friday lab options (`Labs!M11:M14,O11:O14`) cannot move its lectures. The repeated EEE2044S takes precedence. |
| `embedded1-failed` | `EB022!D27:D28,F27:F28` EEE2046F against `D43:D44,F43:F44` EEE3092F: Tuesday and Thursday 14:00-15:45. `D29:D30` and `D45:D46` also overlap on Tuesday 16:00-17:45. | Mandatory overlaps remain regardless of the EEE2046F lab arrangements on `Labs!D13:D14,F13:F14`. EEE3092F is left out. EEE3094S's Wednesday afternoon meeting forces EEE3096S's Friday lab when both are planned. |

Every listed exclusion is explained by a focal decision or these clashes. The relevant ASPECT timetable rows and final-year meetings were also checked against the notes.

## Judgement calls and scope

Retained all four recommended values and their flags: 12 plans for `aspect-final-supp`, `eligible` for HUB4049F in year 5, under-minimum wording for `owes-asl-dp-refused`, and 3 plans for `embedded1-failed` using 154 from the printed 154-162 range. The existing `aspect-maths-physics` flag and all documented historical assumptions also remain.

The FS line is not a passed-credit line under the specification. The final-year record contains 422 passed credits, giving a 154-credit floor. This is a check of the stated arithmetic, not a new plan enumeration.

FB5's printed rule on p. 14 refers to expected graduation year. The two-core-course threshold, treatment of pending results and offering covers are specification interpretations. This review does not describe them as extra words in the handbook.

Plan counts were checked for plausibility only. The combinations were not re-enumerated. No engine, backend, checker or `show_plans.py` was run, and no prohibited implementation or rule files were opened. The standalone EEE2046S coverage gap remains documented, so an engine omission must be reported rather than relabelled to match it.

## Source versions

Repository: `https://github.com/BumeMxenge/SAGE`.

Specification branch: `test/check-plans-and-eligibility`, snapshot `8a995acf6effe3e563db668b72e71f00ef26fd3e`. Source files match the checked `main` snapshot `6c2e311ec983a9eb559e9e822f85ebf6c81ce0bf` byte-for-byte by Git blob ID.

| Source | Git blob ID |
|---|---|
| `tests/acceptance/atp2/SEMANTICS.md` | `e15e4a351ea0d986a10ce36c2e2c65ce09b71ad4` |
| `data/sources/2026/EBE_2026.pdf` | `4024a6d805f1030c9f64eb4c3127cbced363facf` |
| `data/sources/2026/2026_timetable.xlsx` | `639cddc6cf06fe45fe56829810b31352e7b07a4a` |
| `data/sources/2026/2026_Complementary_Studies_Course_Details.xlsx` | `d58e080250c274be29fe62a515572f4ba6866216` |
| `data/sources/2026/equivalences.csv` | `195cec73cf238aaadff7882423de4131f8a84071` |

The external Commerce and Science entry requirements were checked in the supplied source workbook, as instructed. No new claim of checking their original PDFs is made. No historical-code conversion or full audit of every passed history line was undertaken.

## Second check against print, 26 October 2026, evening

A separate check read the handbook, timetable, complementary workbook, `equivalences.csv` and `SEMANTICS.md` at the snapshot above, and nothing else in the repository beyond the record shape. Its source fingerprints match the table above.

**What it confirmed.** Every mark lies in its symbol's band, and FS 46 meets FB7.1's 45% (p. 15). Every history's past entry rules and timetables hold. All six years of study, all 32 statuses and their pages, and every exclusion hold. All three clashes hold on the EB009, EB011 and EB022 sheets. The 12 `aspect-final-supp` combinations are exactly the four-course sets with at least two of EEE4117F, EEE4118F and EEE4119F, and none clashes on EB811's fifth-year sheet. The `embedded1-failed` count is 3 at 154 and 2 at 162 without lowering. The passed-credit totals (80, 80, 48, 72 and 422) are right.

| File and row | Field | Before | After and evidence |
|---|---|---|---|
| `records.csv`, `power-repeat-clash` | `note` | No mention of her own minimum | Added that her one plan (34 credits) is under her own minimum of 50 (146 less 80, less 16 for EEE3091F; p. 58) and still stands, as nothing in the specification makes an under-minimum plan invalid and EB011's third year has no elective to add. The label is 1 plan on either reading of FB3.4 left-outs. |
| `records.csv`, `aspect-final-supp` | `note` | "(as FB5 asks)" | "(as the specification reads FB5)". FB5 prints nothing about a pending supplementary (p. 14). |
| `decisions.csv`, row 11, `power-repeat-clash / MEC2045S` | `deciding_codes` | MEC1009F MEC2047F | MEC2047F. Print's "MEC1009F/S and MEC2023F/S or MEC2047F/S" has no brackets (p. 148), and MEC2047F is the one code every grouping needs. The note says so. |
| `README.md` | JSON example | MAM1020F at 16 credits, "For Engineers" | 18 credits, "for Engineers" (pp. 48, 178). |
| `README.md` | Column table | Set reasons "separated by `;`"; codes and pages described as codes and printed pages only | Set reasons are separated by a semicolon and a space and split at their first colon; `deciding_codes` may hold a printed stem such as ECO1010; `page` may name another handbook. |
| Both CSVs | Line endings | CRLF | LF, as the repository's `.editorconfig` asks. Git's `* text=auto` would have converted them on add. |

Every other CSV row keeps its original bytes and quoting, apart from the line ending.

The labels are reviewed and awaiting B's commit. They are not frozen until that commit is made.
