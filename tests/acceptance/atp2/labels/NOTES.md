# ATP-2 labels: notes for checking (revised against the specification)

Six records, revised to follow `SEMANTICS.md` (the ATP-2 specification). Page numbers are the handbook's printed ones; the PDF runs one ahead. Timetable cells are `sheet!range` in `2026_timetable.xlsx`, merged cells expanded.

## Review completed on 26 October 2026

All six stories, their FB5 working under `SEMANTICS.md`, all 32 focal decisions, exclusions and the three named clash cases were checked. Plan counts were skimmed for plausibility, as requested. No eligibility status, deciding code, year of study, excluded course, plan count, combination or judgement-call flag was changed. The six JSON histories and `records.csv` are unchanged.

- `decisions.csv`, `owes-asl-dp-refused / CSC2001F`: corrected `page` from 169 to 170. The heading is on printed p. 169, but the entry requirement is on printed p. 170 (PDF page 171). Added the correction to its note and the corresponding references below.
- `decisions.csv`, `aspect-final-supp / HUB4049F`: corrected the note's alternative reading. Referral gives `check`; a literal fourth-year-only restriction gives `not_eligible` in year 5. Retained `eligible` and `judgement_call = yes`, supported by its fifth-year curriculum listing on p. 61.
- `README.md`: documented the existing `other` term used for X courses. No JSON term was changed.

FB5 itself says only that academic year of study is determined by expected graduation year (p. 14). The threshold of two core passes and treatment of a pending supplementary for progression are the specification's interpretation, rather than additional wording printed in FB5. All four recommended judgement-call values remain as drafted; the existing `aspect-maths-physics` flag and historical assumptions also remain.

`REVIEW.md` gives the source versions and per-record coverage. This review does not freeze the labels: B will commit them.

## Second check against print, 26 October 2026, evening

Every record, decision, plan count and clash was checked again against print and `SEMANTICS.md`. No expected status, year of study, exclusion, plan count, combination or judgement-call flag changed. These cells and files did:

- `records.csv`, `power-repeat-clash`, `note`: added that her one plan (34 credits) is under her own minimum of 50, and that it stands, as nothing in the specification makes an under-minimum plan invalid and EB011's third year has no elective to add.
- `records.csv`, `aspect-final-supp`, `note`: "(as FB5 asks)" now reads "(as the specification reads FB5)", as FB5 prints nothing about a pending supplementary (p. 14).
- `decisions.csv`, `power-repeat-clash / MEC2045S`: `deciding_codes` changed from "MEC1009F MEC2047F" to "MEC2047F". Print's rule has no brackets (p. 148), and MEC2047F is the one code every grouping needs. The note says so.
- `README.md`: the JSON example's MAM1020F now has 18 credits and the printed name (pp. 48, 178). The table now says how set reasons are separated, that `deciding_codes` may hold a printed stem such as ECO1010, and that `page` may name another handbook.
- Both CSVs now use LF line endings, as the repository's `.editorconfig` asks. Git would have converted them on add anyway.

## Read this first

**Sources opened in the original drafting pass (retained from the supplied notes).** `SEMANTICS.md`, the label format, the drafts, and these printed pages of the 2026 handbook: 10-19, 47-61, 129-141, 144-148, 162, 164, 168-171, 178-184, 187-191. Also the timetable, the complementary workbook, `equivalences.csv`, the 2026 source manifest, and the 2023 handbook's printed pp. 45-47 (for the ASL1200S and CON2026S names). Two of those pages hold Construction Economics programme tables: 2026 p. 47 and 2023 p. 45. I opened them by accident, next to the Electrical pages, and used nothing from them. Neither is in the excluded ranges (90-102, 114-126). I opened nothing under `backend/`, `experiments/`, `data/rules/`, `data/synthetic/`, `docs/` or `tests/`, and ran no backend code. The clash and eligibility checks in `rev_scripts/` are my own scripts, typed from print.

**Conventions used in every record.**
- `owed_core` lists plan members only. It leaves out X courses, which "never [are] a plan member" and get a set-level conditional reason instead, and 576-credit places, which are slots. It counts a course as passed when one of her lines covers it.
- In decisions.csv, statuses are from her record alone, outside any plan. Where a plan treats the course differently (a same-year prerequisite, or FB3.4), the note says so.
- Codes are the 2026 codes throughout (EEE1008F, EEE1009S, EEE2048S), with 2026 names, credits and NQF levels. ASL1200S and CON2026S have no 2026 entry, so their names come from 2023 p. 46: Africa: Culture, Identity & Globalisation (8, NQF 5) and Project Management for Engineers (8, NQF 6). **B to decide:** per `equivalences.csv`, a real student who registered before 2025 holds EEE1006F, EEE1007S and EEE2048F. Swapping those in changes no status, plan or reason, because those rows cover the 2026 codes. Only the `deciding_codes` notes for EEE2044S and EEE2046F would change, since their EEE1006F and EEE1007S leaves would then match directly.
- X courses use `term: "other"`. Print gives them no term: the suffix X is "not classified" (p. 11), and the entries give only "the long vacation following the year of first registration" (EEE1000X, p. 129) and "at the end of the third year" (EEE3000X, p. 133). Each X course is recorded in the year it relates to.
- "Next year's core" means the next year's core table only, not its elective-core group. The specification calls group courses electives ("then a minimal set of electives").
- FB8.10(c) (p. 19) asks a 576-credit four-year student to pass 116 credits a year. signals1-failed and power-repeat-clash passed 80 in 2025, and embedded1-failed passed 48, so each would need the Senate's permission to renew in 2026. FB8 isn't among SAGE's plan rules and changes no label.

## What changed from the drafts

- **Intake 2023** for signals1-failed, power-repeat-clash and embedded1-failed, as the revised specs ask. Each now holds third-year passes from 2025, so FB5 gives year 3.
- **Statuses are outside-plan.** EEE3096S, EEE3093S and CSC2002S in embedded1-failed are now not_eligible. EEE3096S and MEC2045S (power-repeat-clash) and EEE3092F (embedded1-failed) are now eligible: FB3.4 is a plan matter, not an entry rule. The plan context is in each note.
- **embedded1-failed** now has 3 plans: the draft's route F, with the EEE2046S route as a known gap.
- **aspect-maths-physics** now has intake 2024 and is in year 3. Print can't finish year 1 within 2024 for a mid-year switcher, so year 1 ends in 2025's first semester through MAM1024F and PHY1015F (pp. 181, 189). She's on 576 credits, so the ASL1200S place is a slot.
- **aspect-final-supp** has 12 four-elective plans, up from 10. Passed credits leave out the pending supplementary, which makes the minimum 154.
- **HUB4049F** is now eligible, read as a min_year_of_study leaf. It's a judgement call.
- **owes-asl-dp-refused** is held in year 3. The DP-refused course is now CSC1016S, not PHY2010S. Of her year-3 core, only a CSC1016S refusal excludes a course of her own year (CSC2001F), and the under-minimum wording needs such a course. The draft's FB3.4 calls on CSC2002S and EEE3096S disappear, as both are fourth-year.
- **Set reasons** now include, wherever they apply: the next-year-core included reason, the "more electives allowed" reason (with note (i) for EB022), EEE3000X's conditional reason, and the under-minimum wording on exclusions.

---

## 1. signals1-failed (EB009EEE01, intake 2023, S2)

**History.** She completed her 2023 first year and her 2024 second year except EEE2047S (F 41). In 2025 she passed EEE3088F, EEE3089F and EEE3091F (sem1) and EEE3093S, EEE3098S and EEE3100S (sem2), and failed the EEE2047S repeat (F 44). She also passed ASL1200S (2023) and CON2026S (2024). Every 2025 entry rule was met at the time: EEE3098S's EEE3088F is a same-year prerequisite, and the others rest on 2024 passes (pp. 133-138). There are no clashes in EB009's 2025 slots.

**FB5 working.** Year 1 is complete. Year 2 has 9 of 10 core passed (EEE2047S outstanding). Year 3 has 6 of 9 passed. Year 4 has none. The latest year with two or more core passes is 3, and it's incomplete, so she's in year 3. Her lowest unfinished year is 2, which is lower, so year 3 stands.

**Labels and pages.**
- Owed core is EEE2047S (p. 48) plus EEE3090F, EEE3092F and EEE3094S (p. 49). The complementary line is the slot `complementary:18` (p. 49).
- Excluded by entry rule, each naming EEE2047S: EEE3090F ("EEE2045F and EEE2047S", p. 134), EEE3092F ("EEE2047S, MAM2083F/S", p. 135) and EEE3094S ("EEE2045F and EEE2047S and MAM2084S/F", p. 135). Their two F lines don't meet the pass leaf (the specification's result table).
- No FB3.4 reason. EEE2047S (EB009 K23:K24, N23:N24, Mon and Thu 10:00-11:45) and EEE3094S (K39:K40, N39:N40) overlap exactly, but exclusion runs first, and nothing left in her plan clashes with the repeat.
- Plan count 1 (none): EEE2047S and the slot.
- Credit minimum: 146 (p. 49) less 80 passed third-year credits = 66, less 48 excluded = 18. Plans come to 34, under both 146 and 66, so each exclusion reason carries the under-minimum wording on either reading.
- Next-year core she meets (p. 49 table; entries pp. 138, 141, 164): EEE4113F and EEE4125C through EEE3098S, EEE4124C through EEE3088F, and CML4607F (student_in). EEE4022S isn't met.
- EEE3000X is outstanding (p. 49), so it gets a conditional reason.
- Places: both are year 1 for EB009 (p. 48), and her passes meet them.
- Decisions: EEE2047S p. 132; EEE3094S, EEE3092F p. 135; EEE3090F p. 134; ECO2007S, Commerce Handbook 2026 p. 156 (refer leaf "(or equivalent)", continuing "ECO1010 or MAM1010"); EEE4113F p. 138.

**Assumptions.** "A pass in ASL1200S or CON2026S itself meets its place" (A place already met, assumption).

**Unsettled.** None for the labels.

## 2. power-repeat-clash (EB011EEE05, intake 2023, S2)

**History.** She completed her 2023 first year and her 2024 second year except EEE2044S (F 44). In 2025 she passed EEE3088F, EEE3090F, EEE3092F and MEC2047F (sem1), retook EEE2044S and failed again (F 38), and passed EEE3094S and EEE3099S (sem2). In 2025, FB3.4 kept her out of EEE3096S and MEC2045S for the same clashes as in 2026. She also passed ASL1200S (2023) and CON2026S (2024). MEC2047F's rule "MAM1021F/S, PHY1012F/S and MEC1009F/S" (p. 148) was met by her 2023-24 passes. EEE3099S rests on the same-year EEE3088F.

**FB5 working.** Year 2 has 9 of 10 core passed. Year 3 has 6 of 9 passed and is incomplete. So she's in year 3, and her lowest unfinished year is 2.

**Labels and pages.**
- Owed core: EEE2044S (p. 57) plus EEE3091F, EEE3096S and MEC2045S (p. 58). Slot `complementary:18` (p. 58).
- EEE3091F is excluded by entry rule ("EEE2044S", p. 134), with the under-minimum wording. The minimum is 146 less 80 = 66, less 16 = 50; plans come to 34.
- FB3.4 (pp. 13-14), checked section by section in EB011:
  - EEE2044S's Tue and Wed 10:00-11:45 lectures (L23:L24, M23:M24) overlap EEE3096S's lectures (L39:L40, M39:M40). EEE3096S's one choice group is its lab (Labs M11:M14 Wed or O11:O14 Fri), which can't move a lecture.
  - EEE2044S's Mon 14:00-15:45 (K27:K28) overlaps MEC2045S's (K43:K44). Neither course has a choice group.
  - These are two separate smallest conflicts, each a current-year course against the repeated EEE2044S. Each current-year course is left out with a conflict reason, and the plan stands: 1 plan (none), EEE2044S plus the slot.
  - EEE3094S and EEE3099S don't clash with EEE2044S. Both are passed anyway.
- Next-year core (p. 58 table): EEE4113F, EEE4125C (through EEE3099S), EEE4124C (through EEE3088F) and CML4607F.
- EEE3000X gets a conditional reason.
- Places are year 2 for EB011 (p. 57) and met by passes.
- Decisions: EEE2044S p. 130 (EEE1007S only through equivalences.csv's EEE1009S row); EEE3091F p. 134; EEE3096S p. 136; MEC2045S p. 148 (met however "MEC1009F/S and MEC2023F/S or MEC2047F/S" groups, so its deciding code is MEC2047F alone); BIO1004S, Science Handbook 2026 p. 77 (NSC and permission wording, all refer leaves).

**Assumptions.** "'Repeated' means a course with a failed line (assumption)": EEE2044S has two F lines, so the conflict reasons call it repeated. Also "A pass in ASL1200S or CON2026S itself meets its place".

**Unsettled.** The specification says a core course left out "because she can't take it yet" lowers the minimum. I've read that as entry-rule exclusions only, not FB3.4 left-outs. Her minimum is then 50, and her one plan comes to 34, under it. The plan still stands: nothing in the specification makes an under-minimum plan invalid, and EB011's third year has no elective that could close the gap. If FB3.4 left-outs did lower it, the minimum would be 18 and the plan would meet it. Either way the label is 1 plan.

## 3. aspect-maths-physics (EB809EEE01, intake 2024, S4)

**History.**
- 2024 sem1, four-year curriculum: CSC1015F and EEE1008F passed; MAM1020F F 36 and PHY1012F F 38.
- She then moved at the second opportunity printed on p. 50 ("after the first semester's final examinations").
- 2024 sem2: EEE1009S, MAM1023S and PHY1014S, the second-semester offerings of the five-year first-year courses (pp. 180, 189). EEE1000X over the long vacation.
- 2025 sem1: MAM1024F and PHY1015F, which finish year 1 (pp. 181, 189), plus EEE2045F and MEC1003F.
- 2025 sem2: CSC1016S, EEE2047S, MAM2084S, MAM2085S (p. 184) and CON2026S.

**Does print fit year 1 into calendar 2024? No.** MAM1024S needs "MAM1020F/S or MAM1023F/S" (p. 181) and PHY1015S needs "PHY1014F/S or PHY1012F/S" (p. 190). After failing in semester 1, she can only take MAM1023S and PHY1014S in semester 2, so year 1 ends mid-2025.

**Entry rules met at the time.**
- MAM1024F, through MAM1023S.
- PHY1015F, through PHY1014S, with the MAM1023S co-requisite.
- EEE2045F, through the EEE1008F to EEE1006F equivalence.
- EEE2047S, through MAM1024F.
- MAM2084S: MAM1024F covers MAM1024S (other offering), and MAM1024S counts as MAM1021S (equivalence).
- MAM2085S: "MAM1023 and MAM1024".
- PHY1014S's co-requisite: the concurrent MAM1023S.

**Two 2025 points for B.**
1. MAM2085S prints "Monday-Friday 1st period" (p. 184). The 2026 EEE timetable puts MAM2084S at Tue-Fri 08:00. MAM2084S's own entry prints no period (p. 183), and 2025's timetable isn't in print, so taking both assumes they fitted, or the Head of Department's permission under FB3.4.
2. CON2026S has no 2026 entry, so its 2025 pass assumes the course still ran. The alternative, a complementary course filling the year-2 place, hangs on whether "her complementary lines" includes EB809's fourth-year line, which the specification doesn't settle. A direct pass avoids that.

**FB5 working.**
- Year 1 is complete through covers: MAM1023S covers MAM1023F, PHY1014S covers PHY1014F, MAM1024F covers MAM1024S and PHY1015F covers PHY1015S, plus EEE1008F and EEE1009S.
- Year 2 is complete: CSC1015F, EEE2045F, MEC1003F, CSC1016S, EEE2047S, MAM2084S, and MAM2085F through the MAM2085S cover. The CON2026S place is met.
- Year 3 has no passes. The latest year with two or more passes is 2, and it's complete, so she's in year 3. Her lowest unfinished year is also 3.
- Without the offering covers, year 2 would count as incomplete and she'd be in year 2. That is the cover test.

**Labels and pages.**
- Owed core (p. 51): EEE2046F, EEE3090F, MEC1009F, EEE2044S, EEE2048S, EEE3094S and PHY2010S. It must not list MAM1020F, PHY1012F, MAM1023F, PHY1014F, MAM1024S, PHY1015S or MAM2085F.
- No exclusions:
  - EEE2046F through EEE1008F to EEE1006F (p. 131).
  - EEE2044S through EEE1009S to EEE1007S (p. 130).
  - PHY2010S: its MAM2083F/S leaf is met only through MAM2085S to MAM2085F (offering) to MAM2083F (equivalence) (p. 191).
  - EEE3090F (p. 134), EEE3094S (p. 135), MEC1009F (p. 145) and EEE2048S (p. 132) directly.
- No clashes (EB809 rows 39-46 and Labs). EEE3090F's Labs Friday sessions meet nothing of hers.
- 1 plan (none).
- Slot: ASL1200S's place is year 3 for EB809 (p. 51 footnote; specification table), so `place:ASL1200S:8`.
- Credits are 104 plus 8, against the printed 104 (p. 51). Not under.
- Next-year core (p. 51): EEE3088F (EEE2045F), EEE3092F (EEE2047S plus the MAM2085S two-step cover) and CML4607F. EEE3089F, EEE3091F, EEE3093S, EEE3098S and EEE3100S aren't met.
- No X reason: EEE3000X is fourth-year core in EB809 (p. 51), and EEE1000X is passed.
- No pp. 49/51 note, as she isn't in her final year.
- Decisions: EEE2044S p. 130; EEE2046F p. 131; PHY2010S p. 191; MAM2085F p. 183 (already passed through the cover); EEE3092F p. 135.

**Assumptions.** "A pass covers the other offering when the first seven characters match and her line's credits equal the other offering's credits in the year's rules ... No handbook prints this rule (assumption)". Every year-1 and year-2 completion and the MAM2083F/S leaves rest on it. Also "A pass in ASL1200S or CON2026S itself meets its place".

**Unsettled.**
- The specification ties the X reason to "each one still outstanding" without naming a year. I've applied it to X courses from her year and earlier. If the engine lists every outstanding X course, add `conditional:EEE3000X`.
- The two 2025 points above.

## 4. embedded1-failed (EB022EEE02, intake 2023, S2)

**History.** She completed her 2023 first year and her 2024 second year except EEE2046F (F 38). In 2025 she retook EEE2046F and was refused a DP (DPR). Alongside it she passed EEE3088F, EEE3089F and EEE3090F, none of which needs EEE2046F/S (pp. 133-134); EEE3088F is met through EEE2045F. She didn't take EEE3092F, which clashes with EEE2046F. In 2025 sem2 she passed EEE3097S, through the same-year EEE3088F. She deferred CSC2001F, the elective pair and the complementary course to 2026. She also passed ASL1200S (2023) and CON2026S (2024); both places are year 1 for EB022 (pp. 52-53).

**FB5 working.** Year 2 has 9 of 10 passed (EEE2046F outstanding). Year 3 has 4 of 7 core passed and is incomplete. So she's in year 3, and her lowest unfinished year is 2.

**Labels and pages.**
- Owed core: EEE2046F (p. 53, second year) plus CSC2001F, EEE3092F and EEE3096S (p. 53). Two of CSC2002S, EEE3093S and EEE3094S are needed (p. 53). Slot `complementary:18`.
- FB3.4 (pp. 13-14): EEE2046F is repeated (F line). Its EB022 D27:D28, F27:F28 and D29:D30 meetings, plus Labs D13:D14, overlap EEE3092F's D43:D44, F43:F44 and D45:D46 exactly, and there's no choice group. EEE3092F is left out with a conflict reason. Its own entry rule is met (p. 135).
- Same-year prerequisites inside every plan:
  - EEE3096S and EEE3093S ("EEE2046F/S", pp. 136, 135) through the semester-1 EEE2046F.
  - CSC2002S ("CSC2001F (At least 45% for CSC2001F)", p. 170) through the semester-1 CSC2001F: a mark leaf of 45, which is "50 or less".
  - Each gets an included reason. From her record alone, all three are not_eligible.
- Plans: the pairs CSC2002S+EEE3093S, CSC2002S+EEE3094S and EEE3093S+EEE3094S.
  - In the pairs with EEE3094S, its Wed 14:00-15:45 (M43:M44) rules out EEE3096S's Wednesday lab (Labs M11:M14), so the Friday lab is used. The other pair can use either.
  - CSC2001F's Fri 14:00-15:45 practical (G43:G44) doesn't touch the repeat.
- No CSC day pairs arise. CSC2001F and CSC2002S use the timetable's practical slot (the specification's printed-meetings section), and no CSC3xxx course is third-year.
- Credit minimum: printed "154-162" (p. 53), taken as 154, less 48 passed = 106. Plans come to 106 (EEE3093S+EEE3094S) or 114. So two electives meet the rule and the minimum, and a third would be spare.
- Note (i) (p. 53), quoted in the "more electives allowed" reason: "All three elective 3rd year core courses can be taken; however, but then the complementary studies elective should then be taken in the winter or summer term."
- Next-year core (p. 54): EEE4113F and EEE4125C (EEE3097S), EEE4124C (EEE3088F) and CML4607F.
- EEE3000X gets a conditional reason.
- Decisions: EEE3096S p. 136; EEE3093S p. 135; CSC2002S p. 170; EEE3092F p. 135; EEE2046S p. 132.

**EEE2046S, a known gap.** Print offers EEE2046S with the same rule as EEE2046F (p. 132), and she meets it through EEE1008F and CSC1015F, so print's answer is eligible. SAGE's approved rules don't hold it (the 2026 manifest excludes it from the timetable). Print's EEE2046S route would keep EEE3092F, but couldn't open EEE3096S or EEE3093S, which are in the same semester and not an earlier term.

**Assumptions.** "'Repeated' means a course with a failed line (assumption)": the F 38 line makes EEE2046F repeated despite the later DPR. Also "A pass in ASL1200S or CON2026S itself meets its place".

**Judgement call.** If the engine reads "154-162" as 162 and doesn't lower the minimum for the FB3.4 left-out EEE3092F, the minimum is 114. The EEE3093S+EEE3094S plan (106) then fails it, and adding CSC2002S makes EEE3093S spare, so only 2 plans remain.

**Unsettled.** Whether an FB3.4 left-out course also gets the under-minimum wording (on the printed reading, plans of 106-114 are under 154). I've expected none, reading "can't take it yet" as entry rules only.

## 5. aspect-final-supp (EB811EEE05, intake 2022, S4)

**History.** This is the draft's revised history.
- 2022: year 1.
- 2023: year 2, plus CON2026S and EEE1000X.
- 2024: year 3 with ASL1200S on the "ASL1200S equivalent" row (p. 60), and EEE3094S failed (F 38).
- 2025: year 4, with BUS1007S filling the 18-credit complementary line and EEE3000X, plus the EEE3094S repeat, on which she got FS 46 (supplementary pending; FB7.1 needs a DP and at least 45%, p. 15).
- Rechecked against 2026 rules: MEC2047F (2025) is met through MAM1024S to MAM1021S and PHY1014F to PHY1012F (equivalences), with MEC1009F. EEE3092F and PHY2010S rest on the MAM2085F to MAM2083F equivalence.
- 2025 sem2 fits EB811 with EEE3096S's Friday lab.

**FB5 working.** Years 1, 2 and 4 are complete. Year 3 is complete once the pending EEE3094S counts as passed ("A core result ... with a supplementary pending, counts as passed for her year of study"). The latest year with two or more passes is 4 and it's complete, so she's in year 5, her final year.

**Labels and pages.**
- Owed core: EEE4113F, CML4607F, EEE4125C, EEE4124C and EEE4022S (p. 60). EEE3094S isn't owed, as plans assume she passes it.
- Electives (pp. 60-61): at least 48 credits, at least two of EEE4117F, EEE4118F and EEE4119F; the others are EEE4114F, EEE4120F and HUB4049F.
- Credit minimum: the printed 138 (p. 61), and in her final year at least 576 less her passed credits. Passed credits are "pass and credited lines": 422. The FS line is neither, so 576 - 422 = 154. With 90 core credits, she needs 64 elective credits, which is four courses. Three give 138, under 154; a fifth would be spare.
- Plans: of the 15 four-course sets, 3 have only one group-A course, which leaves 12. None clashes (EB811 rows 69-78; EEE4125C is q3 and meets in sem2).
- Statuses (outside plan):
  - EEE4118F and EEE4119F are check: the leaf on EEE3094S is unknown (pp. 139, 140).
  - EEE4114F is eligible: "EEE3092F or EEE3094S" is met through EEE3092F (p. 139).
  - EEE4117F and EEE4120F are eligible (pp. 139, 140).
  - HUB4049F is eligible (p. 162; judgement call below).
  - EEE3094S is not_eligible, with a result still to come (p. 135).
  - EEE4022S is not_eligible from her record (p. 138). In every plan its rule is met by the plan's semester-1 group-A electives, with an included reason.
- Set reasons: `conditional:FB7` for EEE3094S, and "more electives allowed". There's no note (i) (EB811), no pp. 49/51 note (that's EB009 and EB809 only), no X reason (both passed) and no next-year reason (final year).
- Complementary and places: BUS1007S fills the one year-4 line (p. 60). ASL1200S (year-3 place, p. 60) and CON2026S (year-2 place, p. 59) are passed.

**Assumptions.** "Her passed approved complementary courses first fill her complementary lines, one course a line, whatever its credits" (BUS1007S), and "A pass in ASL1200S or CON2026S itself meets its place".

**Judgement calls.**
- If the engine counts the pending supplementary's 16 credits as passed (438), the minimum falls to 138, and the set is the draft's 10 three-elective plans. I've followed the specification's "Passed credits are pass and credited lines".
- HUB4049F's "Students must be in their fourth year of study" is read as a min_year_of_study 4 leaf, "met at that year or later". If it's held as a refer leaf, it's check and still planned, so the count is unchanged. A literal "in their fourth year" would make it not_eligible and leave 5 plans, but her own curriculum lists it as a fifth-year elective (p. 61).
- EEE4124C prints only "Students also take EEE4124C, but this is purely online (5552)" (EB811 K80). I read that as no meetings, so it's neither clashing nor conditional. If ingestion made it an untimed meeting, add `conditional:EEE4124C untimed (FB3.4)`.

## 6. owes-asl-dp-refused (EB822EEE02, intake 2023, S4)

**History.**
- 2023: five-year year 1 (p. 55).
- 2024: year 2, with CSC1016S DP-refused (DPR), plus CON2026S and EEE1000X.
- 2025: EEE2046F, MEC1009F, EEE2044S, EEE2048S and PHY2010S from year 3. PHI2042F (20 credits, sem1, "At least second year status", Humanities Handbook 2026 p. 367) for the year-3 complementary line. EEE3088F, a fourth-year course, taken a year early. CSC1016S again, DP-refused again.
- She has never met the ASL1200S place.
- 2025 entry rules: EEE2046F through EEE1008F to EEE1006F; EEE2044S through EEE1009S to EEE1007S; PHY2010S through PHY1014F, PHY1015S and MAM2085F to MAM2083F, with the passed MAM2084S as its co-requisite; EEE3088F through EEE2045F.
- No 2025 clashes (EB822, Labs). The draft's AGE1002S was dropped: its Tue 12:00 meets CSC1016S's.
- Credits passed: 96, 98 and 100, each at least the 96 FB8.10 asks of the five-year 576-credit curriculum (p. 19).

**FB5 working.** Year 1 is complete. Year 2 has 6 of 7 passed (CSC1016S outstanding). Year 3 has 5 of 6 core passed and is incomplete (CSC2001F, and the ASL1200S place). Year 4 has 1 (EEE3088F), under the threshold of two. The latest year with two or more passes is 3, and it's incomplete, so she's in year 3. Her lowest unfinished year is 2. In her fourth calendar year, FB5 holds her in year 3.

**Labels and pages.**
- Owed core: CSC1016S (p. 55, second year) and CSC2001F (p. 55, third year).
- CSC2001F is excluded. Its rule "(CSC1015F/S and CSC1016S) or (CSC1010H and CSC1011H)" (p. 170; the entry starts on p. 169) isn't met: her two DPR lines don't meet the pass leaf. The repeat is in semester 2, later than CSC2001F's semester 1, so the same-year rule can't help.
- 1 plan (none): CSC1016S (EB822 L25, M27:M28) and the slot `place:ASL1200S:8`. ASL1200S's place is year 3 for EB822 (p. 55; specification table). PHI2042F fills her only complementary line (year 3, p. 55), so there's no complementary slot and nothing left over for the place.
- Under-minimum: 114 (p. 55) less 72 passed third-year credits, less 18 for the filled line = 24, less 24 for CSC2001F = 0. Plans come to 26, under the printed 114, so CSC2001F's reason carries the wording.
- Next-year core (pp. 55-56): EEE3089F (PHY2010S plus MAM2085F to MAM2083F, p. 133), EEE3090F (p. 134), EEE3092F (p. 135), CML4607F (p. 164), EEE3096S (EEE2046F, p. 136) and EEE3097S (EEE3088F, p. 137). EEE3088F is passed, so not listed.
- No X reason: EEE3000X is fourth-year in EB822 (p. 56).
- Decisions: CSC2001F p. 170; CSC1016S p. 168; EEE3097S p. 137; EEE3089F p. 133; CSC2002S p. 170.

**Assumptions.**
- "(assumption: the threshold of two keeps one course taken early, such as EEE4124C, from moving her up a year)": EEE3088F.
- "Her passed approved complementary courses first fill her complementary lines, one course a line, whatever its credits. Each course left over fills one owed place, earliest place first.": PHI2042F fills the line, so the ASL1200S place stays owed.
- "A pass in ASL1200S or CON2026S itself meets its place": CON2026S.
- CSC1016S has DPR lines only, so it's "undertaken in arrears", not repeated. Nothing clashes with it, so that makes no difference.

**Judgement call.** The under-minimum wording is expected on the reading that compares plans with "the printed minimum" (114). If the engine compares plans with her own minimum before the exclusion (24), plans of 26 aren't under it, and the wording doesn't appear. No history makes both readings agree here: the owed CSC1016S (18) and the place (8) outweigh CSC2001F's 24.

**Unsettled.** The judgement call above. The specification's "printed minimum" wording favours the label as written.
