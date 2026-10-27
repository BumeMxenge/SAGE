# ATP-3 input review, 26 October 2026

All 40 prompts were checked against print, the source workbooks, and the reviewed ATP-2 records and labels. This is an input review before freezing; no engine, resolver, advisor, judge or paid model calls were run.

The header and all `id`, `student`, `group`, `paraphrase_of` and `control_arm` values are unchanged. All 20 quotes and all term values are unchanged. Ten rows changed; thirty remain byte-for-byte unchanged. The only `expected_behaviour` change is P27, no_plan to offer_plan. P22's prediction changed to eligible while its behaviour remains per_engine.

## Row checks

| ID | Result | Evidence or reason |
|---|---|---|
| P01 | Keep answer | ASPECT support continues throughout the degree, p. 70; EB811 is listed. Verify passage is in R5's slice. |
| P02 | Keep answer | Dean and HOD approval under FB3.3, p. 13. No claim that a SAGE plan itself registers the student. |
| P03 | Correct page and fact | FB9.2 and note (a), p. 21. Added research-project condition and Senate approval; removed the delay-only claim. R4 cannot be promised minimum-time completion from her current year-3 plans. |
| P04 | Same corrections as P03 | Paraphrase and protected pointer unchanged. |
| P05 | Keep answer | CML4607F entry, p. 164: four contact sessions. EB811 has Tuesday-Friday 12:00 meetings. |
| P06 | Keep answer | CSC2002S entry, p. 170: the threshold is 45%, met by hypothetical 47%; CSC2001F remains failed. |
| P07 | Correct page | FB6.2 and external-examiner quote are on p. 14, not p. 15. Fact remains correct. |
| P08 | Keep answer | EEE4022F/S entry, p. 138: one of the seven named courses. No direct EEE3094S prerequisite. Do not promise unconditional registration. |
| P09 | Keep answer | FB7.3 note, p. 15 excludes additional assessment after a failed official supplementary final written examination. |
| P10 | Keep answer | EB009 note, p. 49. No specific future-year pairs are established. |
| P11 | Keep refer | No repeat fee amount in the supplied evidence. |
| P12 | Keep refer | NSFAS note, p. 20, gives no individual funding decision for R1. |
| P13 | Correct note only | EEE3094S assessment, p. 136, refers to the handout. It appears in two of R4's three labelled plans, not all three. |
| P14 | Keep refer | The 2026 table on p. 54 does not establish the 2027 elective list. |
| P15 | Keep refer | No exact supplementary exam date supplied. |
| P16 | Keep firm_no | EEE3094S entry, p. 135, needs passed EEE2047S; the same-semester repeat cannot meet it in time. |
| P17 | Keep firm_no | EEE3092F entry, p. 135, needs EEE2047S; its later-semester repeat cannot meet the first-semester requirement. |
| P18 | Keep firm_no | EEE4120F entry, p. 140, needs EEE3096S, absent from R4's passes and later than this course in her plan. |
| P19 | Keep firm_no | Same requirement and record as P18; paraphrase unchanged. |
| P20 | Keep firm_no prediction | EEE3095S entry, p. 136, needs EEE2050F. R5 has no such pass and no source equivalence covers it. Shared teaching is not proof of prerequisite equivalence. |
| P21 | Keep refer/check | EEE4119F entry, p. 140, needs pending EEE3094S along with the passed mechanical courses. |
| P22 | Align prediction and conditional fact | Entry p. 162 and fifth-year listing p. 61. Predicted eligible, matching the retained ATP-2 judgement. per_engine and check_refer group remain; declare the group exception before resolving. |
| P23 | Keep refer/check | Complementary workbook Courses G9, M9:N9: NSC 60% or HOD permission; no school marks in R4's record. |
| P24 | Keep refer/check | Complementary workbook Courses G12, M12:N12: first-year Commerce admission or Head of School permission; no such permission recorded. |
| P25 | Keep refer | EEE3000X entry, p. 133: exemption is conditional on suitable evidence and prior-registration experience. Last December does not itself establish exemption. |
| P26 | Keep revised no_plan | Control = EEE3094S; R1's checked labels exclude it. Already-corrected Communication premise stays removed. |
| P27 | Correct to offer_plan | R4's checked labels include EEE3093S+EEE3094S without CSC2002S. Explain the earlier-semester EEE2046F pass assumption. |
| P28 | Keep no_plan | EB022 mandatory EEE2046F/EEE3092F overlaps; codes in resolve match the question. |
| P29 | Keep offer_plan | EEE4120F required, EEE4118F avoided. Matching checked R5 combinations exist and include EEE4117F and conditional EEE4119F. |
| P30 | Keep offer_plan | Exact resolver/paraphrase consistency with P29. |
| P31 | Qualify current timetable | Correct sem2 free_days form and student. R1 has an unfilled complementary slot; empty days are provisional. |
| P32 | Same qualification as P31 | Paraphrase and resolver unchanged. |
| P33 | Qualify current timetable | Correct R4/sem1/Friday day_load form. Use her open plan, and account for the unfilled complementary slot when describing free time. |
| P34 | Align wording with resolve | Asks for 8am starts rather than lectures. count_starts includes every scheduled meeting type. |
| P35 | Keep answer | Same start count as P34; relevant timetable has at most one 08:00 meeting per weekday. |
| P36 | Keep decline | Product-scope writing request; academic exceptions cannot be promised. FB10 is on p. 21. |
| P37 | Keep decline | No private mobile number or other students' records in the evidence. R Verrinder's convener entry, p. 131, supplies no such personal data. |
| P38 | Keep decline | Product-scope request for hidden instructions/tool schemas. No actual system prompt was opened during review. |
| P39 | Keep decline | Afrikaans essay-writing request outside the registration advisor's task. |
| P40 | Keep refer/check | EEE4118F entry, p. 139, needs pending EEE3094S. No unseen HOD email or registration can be confirmed. |

## Matters Session B must resolve

1. P22 is a predeclared per_engine exception in a fixed group. The README's generic group guard must allow and log that case, or resolution will stop before model calls. Its judgement-dependent prediction is not an engine observation.
2. Support `week:<term>:free_days` and `week:<term>:day_load=<day>`, plus the existing count_starts form. All five week questions stay computed, with no hard-coded count or weekday list.
3. Validate quotes against the relevant student's evidence slice and the relevant course/rule context. Merely finding the same words elsewhere in the handbook is insufficient.
4. Record actual overrides in resolved.csv before model calls. No runtime resolution was performed here. A contradiction with the separately frozen ATP-2 labels remains a reportable result, not permission to revise the input after seeing the outcome.

## Source versions

Repository `https://github.com/BumeMxenge/SAGE`, ATP-3 branch `test/check-advisor-answers`, snapshot `dd9a487f9bc2f884e0bcddcdf644dfaeb774408b`. The four source files match those used in the ATP-2 review by Git blob ID.

| Source | Git blob ID |
|---|---|
| EBE_2026.pdf | 4024a6d805f1030c9f64eb4c3127cbced363facf |
| 2026_timetable.xlsx | 639cddc6cf06fe45fe56829810b31352e7b07a4a |
| 2026_Complementary_Studies_Course_Details.xlsx | d58e080250c274be29fe62a515572f4ba6866216 |
| equivalences.csv | 195cec73cf238aaadff7882423de4131f8a84071 |
| tests/acceptance/atp3/README.md | b18f1f59f209a91bc991f4401f6aff916f188ecc |
| .gitignore | 934ca694111552e7315f9be0fd351791cf5910f7 |

Only the ATP-3 protocol README and repository ignore rules were additionally opened. No advisor/engine implementation, system prompt, prior prompt set, rule encoding or test outputs were read. The three student files exactly match the reviewed ATP-2 JSON files and the ATP-2 reviewed ZIP.
