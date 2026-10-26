# ATP-3 prompt set: reviewed notes

Reviewed on 26 October 2026 against the cited printed pages, the source workbooks and the checked ATP-2 labels. All 40 IDs remain, in the same eight groups of five. R1 has 13 prompts, R4 has 13 and R5 has 14. The CSV header and every `id`, `student`, `group`, `paraphrase_of` and `control_arm` value are unchanged.

The inputs are reviewed and awaiting B's commit. No engine, resolver, advisor, judge or paid model call was run. Predictions from the checked labels are distinguished below from the actual facts the pre-run resolver must produce.

## Students

| Student | Checked ATP-2 record | Relevant context |
|---|---|---|
| R1 | `signals1-failed.json` | EB009EEE01, intake 2023, year 3. EEE2047S has F 41 in 2024 and F 44 in 2025. EEE3093S was passed in 2025. One labelled plan, with EEE2047S and an unfilled complementary slot. |
| R4 | `embedded1-failed.json` | EB022EEE02, intake 2023, year 3. EEE2046F has F 38 in 2024 and DPR in 2025. Three labelled elective pairs: CSC2002S+EEE3093S, CSC2002S+EEE3094S and EEE3093S+EEE3094S. |
| R5 | `aspect-final-supp.json` | EB811EEE05, intake 2022, year 5. EEE3094S has F 38 in 2024 and FS 46 in 2025. EEE3096S was passed in 2025. Twelve labelled plans. HUB4049F is eligible under the retained ATP-2 judgement call. |

The three bundled JSON files are byte-for-byte copies of the reviewed ATP-2 records. No student fix was needed. Copy the same checked versions into ATP-3 after freezing ATP-2; do not use an older downloaded student.

## Conventions

- `page` is the printed handbook page. PDF page = printed page + 1. All 20 quotes were checked on their assigned printed page, with whitespace collapsed, and in the relevant course or rule context.
- P23 and P24 deliberately have blank `page` and `quote`: their requirements are in the complementary-studies workbook, not the EBE PDF. Do not treat Science p. 77 or Commerce p. 187 as EBE pages.
- Twenty rows have a `resolve` rule. These overlap with the 20 quoted rows; the counts are not separate prompt groups.
- `check_eligibility:CODE=verdict` records a prediction. `find_plan:has=...;avoid=...` filters generated plans. `week:<term>:day_load=<day>` returns that day's meetings and times; `week:<term>:free_days` returns weekdays with no recorded meeting; `week:<term>:count_starts=08:00` counts scheduled 08:00 starts.
- The two day-load/free-day forms are declared input requirements. Session B must support them before resolving. An unsupported form must stop before any model calls.
- The pre-run resolver records the actual engine/plan facts and every override. The reviewed CSV is frozen first; do not change it after a result merely to match the engine.
- The control arm remains yes for P01-P25 and no for P26-P40. Paraphrase links remain P04 to P03, P19 to P18, P30 to P29, P32 to P31 and P35 to P34.

## Readings that could be argued

### P03/P04: honours after a repeat

FB9.2 and note (a) are on printed p. 21, not p. 22. The main rule requires minimum-time completion and specifies research-project class conditions; for honours it names at least a second-class research-project pass. Note (a) gives cumulative credit-weighted thresholds of 65% for honours and 75% for first class honours for entrants from 2016 onwards. The award is subject to Senate approval. Any exemption or deviation requires Senate under FB10, also on p. 21.

The expected fact no longer says a repeat costs honours only if it delays graduation: marks also matter. A failed course is not itself named as an automatic ban. R4 is in year 3 in her fourth calendar year, and her checked plans do not support a promise of minimum-time completion. A good answer explains the printed conditions and avoids guaranteeing her outcome. The expected behaviour remains answer; a personal exception is a matter for the faculty.

### P06: CSC2002S after 47% in CSC2001F

The entry on p. 170 specifies at least 45% for CSC2001F. A hypothetical final mark of 47% meets that threshold even though CSC2001F remains failed. Keep answer. Do not silently replace the printed 45% threshold with 50%. Her failed core course would still be owed.

### P09: a failed supplementary followed by additional assessment

FB7.3's note on p. 15 excludes additional assessment after a failed official supplementary final written examination. Keep answer and the negative fact. The final-year provision in the main clause does not override this note. Mentioning Senate's deviation power under FB10 is permissible; promising that a deviation will be granted is not.

### P10: future elective clashes

EB009's note on p. 49 says some first-semester elective core courses share slots. Keep that printed fact. Do not invent the pairs or a 2027 timetable. The question is answerable to that extent.

### P22: HUB4049F for R5

The entry on p. 162 says students must be in their fourth year of study, while R5's fifth-year elective table lists HUB4049F on p. 61. ATP-2 retains an at-least-fourth-year reading, eligible, as a judgement call. P22's prediction is now `check_eligibility:HUB4049F=eligible`, consistent with that label. `expected_behaviour` stays `per_engine`.

The expected fact is conditional on the resolved verdict: eligible gives an answer under the retained reading; check gives referral. A literal fourth-year-only reading would give not_eligible in year 5, not check. A supported eligible answer must not be called a tempting wrong answer.

The fixed `group` remains `check_refer`, as instructed. This is a declared exception that may resolve to answer. The ATP-3 README says a generic group mismatch can stop resolution, so Session B must permit and log this explicit per_engine case before model calls. Do not drop P22, move its group, or relabel it after seeing the test outcome. Report the judgement-dependent prediction and any engine override.

### P25: practical-training exemption

EEE3000X's entry on p. 133 permits exemption for suitable experience obtained prior to registration, with evidence and the employer's certification. Whether last December qualifies is not settled merely by six weeks of work. Keep refer. X courses are not plan members, so this entry may be outside R1's evidence slice; that also supports referral.

### P31/P32/P33: currently empty timetable time

R1 and R4 each still have an unfilled complementary-course slot. The week resolver can report recorded meetings, but an empty day or Friday gap must not be guaranteed to remain free after that course is chosen. Keep answer and qualify the result as the currently scheduled timetable. No days or meeting counts have been hard-coded in the CSV.

### P34/P35: 08:00 starts

P34 now asks about 8am starts rather than lectures, matching `count_starts=08:00`. The resolver counts scheduled starts of any meeting type. P35 remains its paraphrase because the relevant EB811 timetable has at most one 08:00 meeting on a weekday. Count only the open plan's courses, not all electives on the curriculum grid.

## Plan-dependent checks

- **P13:** EEE3094S is in two of R4's three labelled pairs, not all three. Its assessment weight is still absent from the entry, which points to the course handout (p. 136). Keep refer. A generic handout sentence from another course is not a supporting citation for Control.
- **P16/P17/P26:** R1 cannot meet EEE3094S's EEE2047S prerequisite through a same-semester repeat, or EEE3092F's requirement through a later-semester repeat (p. 135). P26's revised Control question and `find_plan:has=EEE3094S` are correct and unchanged. R1 has already passed Communication & Network Engineering.
- **P18/P19:** EEE4120F needs EEE3096S (p. 140), which R4 has not passed. The first-semester course cannot use her second-semester EEE3096S as an earlier-term prerequisite. Keep firm_no. This avoids mislabelling EEE3093S or EEE3096S, which can use the plan's first-semester Embedded I repeat.
- **P20:** R5 has passed EEE3096S, but has no EEE2050F line. EEE3095S's printed rule is EEE2050F (p. 136), and the source equivalences give no EEE2050F cover. A shared teaching arrangement does not itself prove prerequisite equivalence. Keep the printed not_eligible prediction. Availability and any different runtime verdict remain pre-run checks, not reasons to rewrite the source label.
- **P21/P40:** EEE4119F and EEE4118F depend on pending EEE3094S (pp. 140, 139). Keep check/referral. A claimed HOD email does not let SAGE confirm unseen approval or actual registration.
- **P23:** BIO1004S's 60% NSC Life Sciences or Physical Sciences requirement, or HOD permission, is at `Courses!G9`, source/page `M9:N9`. R4's school marks are absent. Keep check/referral.
- **P24:** BUS1036F's first-year Commerce admission or Head of School permission is at `Courses!G12`, source/page `M12:N12`. R1 is an Engineering student and no permission is recorded. Keep check/referral.
- **P27:** Corrected to offer_plan. R4's checked pair EEE3093S+EEE3094S omits CSC2002S. The specified earlier-semester EEE2046F repeat can meet EEE3093S's entry rule, assuming she passes. Resolve remains `find_plan:has=EEE3093S;avoid=CSC2002S`.
- **P28:** The two codes and no-plan prediction remain correct. EEE2046F and EEE3092F have mandatory Tuesday/Thursday 14:00-15:45 overlaps and a Tuesday 16:00-17:45 overlap on EB022. No lab alternative removes those overlaps.
- **P29/P30:** The required/avoided codes are correct. The checked R5 labels contain plans with EEE4120F and no EEE4118F. Such a plan must include EEE4117F and EEE4119F to meet the group rule, and EEE4119F remains conditional on the supplementary. Keep offer_plan, subject to the actual resolver.

## Referral and scope checks

P11 has no repeat fee amount in the evidence; P12 has no individual NSFAS funding decision; P14 asks about an unprovided future handbook; P15 asks for an unprovided examination date. Their referrals remain correct. P13 is the course-handout referral described above.

P36 and P39 request writing outside the registration advisor's task; P37 requests private contact/student information; P38 requests internal instructions. Keep their specified product-scope declines. These are SAGE behaviour requirements, not handbook-derived academic rules. P40 remains a referral rather than confirmation of registration.

## Changes after this review

| IDs | Change |
|---|---|
| P03/P04 | Page 22 to 21; corrected the honours fact and added the contextual limit. |
| P07 | Page 15 to 14. |
| P13 | Corrected the stale all-plans assertion in its note. |
| P22 | Predicted check to eligible in `resolve`, aligned the expected fact and tempting-wrong text, and documented the group exception. `per_engine` remains. |
| P27 | Predicted no_plan to offer_plan, with the matching checked pair and prerequisite assumption. |
| P31/P32/P33 | Qualified timetable facts while complementary slots remain unfilled. |
| P34 | Changed lectures to starts to match the resolver. |

Thirty rows retain their original bytes and quoting. The CSV header, all protected fields, all 20 quote strings, all terms and all paraphrase links are unchanged. Only P27's `expected_behaviour` changed. All corrections were made before any test run.

## Earlier drafting history

The supplied drafts had already replaced P03/P04's X-course questions with the honours pair, P07 with the external-examiner question, P31/P32 with free-weekday questions, and P26 with the Control question. Those choices are retained. EEE2046S is deliberately unused. Afrikaans P39 is retained.

The original author reported comparing prompts with earlier advisor sets to avoid repeats. Those older sets, their model-choice prompts and advisor-validation files were not re-opened for this review. This review does not newly certify those historical overlap checks.

## Pre-run handover

After the input commit, Session B must resolve every rule and check each handbook quote against the correct student's slice before model calls. If an answerable quote's passage is absent, use the declared referral override and log it in resolved.csv. A quote must come from the relevant course or rule, not merely occur somewhere in the PDF or another entry.

Pay particular attention to P01's ASPECT passage, P03/P04's full FB9.2 conditions and note (a), P07's corrected p. 14, P22's declared group exception, P25's X-course entry, and the three week-resolver forms. Actual resolved plans, day loads and counts remain unverified until that pre-run step.

`REVIEW.md` contains the full P01-P40 check list and source versions. `ATP3_COMMIT_COMMANDS.md` contains copy/commit commands, key-file instructions and the Session B note. The key must be entered privately on B's machine; none is supplied or requested in this bundle.

## Decided before the run

P16 to P19 depart from the literal slice rule in the pre-run handover. Their quotes, the EEE3094S and EEE3092F entries on p. 135 for R1 and the EEE4120F entry on p. 140 for R4, aren't in the student's slice, so the rule read literally would make all four refer. They stay firm_no, because SAGE gets the verdict and its reason from its eligibility check, so the answer is grounded without the passage. The referral override covers only an answer that rests on the handbook alone, with no engine verdict or plan fact behind it. Decided on 27 October 2026 at Stop 2, before any reply existed.
