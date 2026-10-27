# SAGE Engine Semantics, for ATP-2

Settled at the engine's Stop 1 on 20 October 2026. Updated on 21 October after real records were run: year of study, chained covers, lines counted once, the complementary line, the credit minimum, printed meetings and the new equivalences. Updated again after the engine's Stop 3: how lines fill complementary lines and places, when a slot is conditional, what a forced section is, the under-minimum reason, untimed citations, list fragments in refer text, courses in progress on Explore Electives, recorded alternatives, and plan names. This is the specification that ATP-2's labels and its checker follow. It says what the engine decides, never how it decides it, so the checker can be written without seeing the engine. Where it differs from decisions 4 to 23 in `claude/SAGE-engine_prompt.txt`, this file wins. Lines marked **(assumption)** are readings print doesn't settle. Mark each label that depends on one, so a disagreement can be traced to its cause.

Printed page numbers are the handbook's own. The PDF's page numbers run one ahead.

## What a plan is

- One student's registration for one year, against the approved current year's rules (2026). It covers both semesters and the quarters.
- It holds every outstanding core course from her year of study and earlier years, then a minimal set of electives that meets her year's rules.
- No core course is pulled forward from a later year.
- Practical training (X courses) is never a plan member. Each one still outstanding gives a set-level conditional reason.
- Complementary credits are never plan members. Each complementary requirement is a slot (see Slots).
- Z courses, such as CSC2004Z, sit in no group, so they're never plan members.

## Her year of study

- FB5 (p. 14) sets it by the year she's expected to graduate. The engine reads that as the latest year from which she has passed at least two core courses, or the year after it when that year's core is complete. It's never earlier than her lowest unfinished year. X courses don't count **(assumption: the threshold of two keeps one course taken early, such as EEE4124C, from moving her up a year)**.
- A gap in an earlier year is arrears, so it doesn't lower her year. A student who still owes MEC1009F from second year but has passed three third-year core courses is in third year, with MEC1009F owed.
- Nothing passed gives year 1.
- Every year complete gives no plan, and a set-level conflict reason.
- A core result still in progress, or with a supplementary pending, counts as passed for her year of study (see Courses she can't take yet).

## The year's rules

- **Group rules.** Courses she has passed in a group count towards its rule, so the rule asks only for what's left. "Choose n" and "n credits" both mean at least. Each line of her record counts once, however many codes it covers, so a pass in PHI2043F is one complementary course, not two (PHI2043F and PHI2043S).
- **Owed rules.** An earlier year's unmet choose, credits or complementary rule joins this year's.
- **Minimal sets.** A plan has no spare elective. An elective is spare when the plan still meets every year rule and the credit minimum without it. An elective that only another course's entry rule needs doesn't count as needed **(assumption, with no 2026 case)**.
- **More electives allowed.** Every choose or credits rule says "at least", so each set with one carries a set-level excluded reason saying more are allowed. For EB022 and EB822, that reason also quotes note (i) (pp. 53 and 56). All three electives can be taken, but the complementary course then goes in winter or summer.
- **The credit minimum.**
  - The base is the year's printed "Total credits per year (minimum)", less her courses of that year she has already passed, and less the credits of each of that year's complementary lines a passed approved course already fills. One course fills a line, so a 15-credit pass takes a full 18 off an 18-credit line. If the core's credits are more, the core's credits are the minimum.
  - A core course of her year left out because she can't take it yet lowers the minimum by its credits. When her plans can then come to less than the printed minimum, its reason says her year is now under that minimum, and that her advisor can give permission. In a final year the degree's total can keep plans above it, and then the reason doesn't say so.
  - Slots and 576-credit places count towards it.
  - In her final year it's also at least the degree's total less the credits she has passed. The degree total is 560 or 576, by her intake (see 576-credit places). Passed credits are pass and credited lines.
  - There's no maximum, as none is printed. FB8.10 is a readmission threshold, not a load limit.

## Courses she can't take yet

- **A core course whose entry rule she doesn't meet** is left out, with an excluded reason naming what's missing. A prerequisite is a course a student "must have completed in order to gain admission" (p. 12).
  - Exclusion repeats until nothing changes. A course that needs an excluded course goes too.
  - The year's totals drop by each excluded course's credits.
  - The set tells her to see her advisor.
- **A core course with a result still in progress or a supplementary pending.** Plans assume she passes it, for her year and her outstanding core. Each one gives a set-level conditional reason, citing FB7 for a supplementary. Entry-rule leaves on that course still read it as unknown.
- A plan set is never empty without a set-level conflict reason saying why.
- **Courses from next year.** Plans never pull a later year's core forward. A set-level included reason lists next year's core courses whose entry rules she already meets, such as EEE4124C and EEE4125C, and says students sometimes take them early with their advisor's agreement.

## Entry rules

Each rule is met, not met or unknown. A course with an unknown rule is conditional. An unknown rule never blocks a course. It tells her to check with her advisor.

- **all** is met when every child is met, not met when any child is not met, and otherwise unknown.
- **any** is met when any child is met, not met when every child is not met, and otherwise unknown.
- **A refer leaf** is unknown, never a fail. Its reason quotes the printed text. When the text only continues a list, such as "or equivalent", the reason also names the list it continues, so CSC3002F's reason names the maths courses its "or equivalent" refers to.
- **student_in** is met when her curriculum is listed.
- **min_year_of_study** is met at that year or later.

### What each result means on a leaf

Any of her attempts can meet a leaf.

| Outcome | Pass leaf | Mark leaf |
|---|---|---|
| pass | Met | Met when the final mark is at least min_mark |
| credited | Met | Unknown (no mark) |
| fail | Not met | Met when the final mark is at least min_mark, pass or not |
| dp_refused, not_counted | Not met | Not met |
| in_progress | Unknown | Unknown |
| supp_pending | Unknown | Unknown if min_mark is 50 or less, not met above 50 **(assumption)** |

- Exactly min_mark meets a mark leaf.
- An SP line (supplementary pass) counts as 50 on a mark leaf, as the app's average does.
- A pass printed with no mark, such as PA or UP, is unknown on a mark leaf.
- The supplementary cap is **(assumption)**. FB7.3 (p. 15) caps an additional assessment at 50%. No 2026 page caps a supplementary. Course entries on pp. 180 to 190 say only that one is "usually granted for a final grade in the range 45-49%".
- UCT's symbols map to outcomes through the `result_symbols` table in the migrations. For example, SP is a pass, FS, OSS and DE are a pending supplementary, GIP and OS are in progress, and DPR is DP refused.

### Covers

A pass in one code can meet a leaf on another, through at most one equivalence step and one offering step, in either order. So PHY1013F covers PHY1013S (offering) and then PHY1015S (equivalence), and PHY1014S covers PHY1014F and then PHY1012F.

- **Equivalences.** A pass covers every code the year's equivalences say it counts as, including the ASPECT mappings. At 2026's next approval five rows join them, so a student who moves between the 4-year and 5-year curricula keeps her maths and physics: MAM1021S counts as MAM1024S, PHY1013S as PHY1015S, MAM2083F as MAM2085F, PHY1015S as PHY1013S and MAM1023F as MAM1020F. Labels follow them.
- **The other semester's offering.** A pass covers the other offering when the first seven characters match and her line's credits equal the other offering's credits in the year's rules, such as ECO1010F and ECO1010S. An offering the rules don't hold gives no cover. No handbook prints this rule **(assumption)**.
- Mark leaves read covering lines too.
- "Already passed", which makes a course not eligible, uses covers as well.

### Co-requisites and same-year prerequisites

- **A co-requisite** ("registered together with (i.e. concurrently)", p. 12) is met by an earlier pass, or by the course in the same plan when it starts no later than the course that needs it.
- **A same-year prerequisite.** A pass leaf on a course in an earlier term of the same plan is met by the plan, assuming she passes, as when EEE3097S needs EEE3088F from the first semester. The course gets an included reason saying so. The same applies to a mark leaf of 50 or less.
- A mark leaf above 50 on a course in an earlier term of the same plan is unknown, so the course is conditional.
- **Outside a plan**, as in Explore Electives, an unmet co-requisite is unknown, as she could take it alongside.

### Eligibility statuses

- **eligible** when the rule is met.
- **check** when it's unknown, with the reason.
- **not_eligible** when it's not met, or she has already passed the course or one that covers it, or has a result still to come on one, as plans count that as passed. Each comes with its reason.

## Clashes

- **When two meetings clash.** They share a day, they overlap in time, and their terms overlap. Meetings that only touch, where one ends as the other starts, don't clash.
- **Term overlap.** q1 and q2 sit inside sem1, and q3 and q4 inside sem2. full_year overlaps both semesters and every quarter. winter and summer overlap only themselves.
- Only her curriculum's meetings count. A meeting linked to curricula belongs to those curricula alone.
- A plan with a clash isn't valid (FB3.4, pp. 13 and 14).
- **Alternatives.** Where a course has alternative sections, any one per choice group may be used to avoid a clash. The choice must work for the whole plan at once: one section of each course, together, with no clash anywhere. Testing courses two at a time isn't enough, as each pair can have a section that works while no single choice works for all. Plans with the same courses but different sections are one plan.
- **Untimed meetings.** A meeting with no printed day or time can't clash, but makes its course conditional. Its reason cites FB3.4, or the course's own entry when the entry prints the meeting as by arrangement, as CSC3024S's does.
- **No meetings.** A course with no meetings makes no clash and is not conditional.
- **Precedence (FB3.4).** It gives precedence to courses "being repeated or undertaken in arrears". "Repeated" means a course with a failed line **(assumption)**.
  - When one repeated or arrears course clashes with one current-year course, the current-year course is left out with a conflict reason.
  - Any other clash among core courses leaves no plan, and the set carries a conflict reason naming the smallest set of courses that conflict.
- **Printed meetings the department's timetable leaves out.** The Electrical Engineering timetable holds CSC3002F's lectures only, and nothing for CSC3003S or CSC3024S. Their course entries (EBE p. 171, and the same entries in the Science handbook) print the rest. Those meetings count like any other:

| Course | Lectures | Practicals |
|---|---|---|
| CSC3002F Networks and Operating Systems | Monday to Friday, 2nd period (09:00), from the timetable | Two 4-hour practicals a week, 14:00 to 18:00, on two different weekdays |
| CSC3003S Advanced Programming & Algorithms | Monday to Friday, 2nd period (09:00) | Two 4-hour practicals a week, 14:00 to 18:00, on two different weekdays |
| CSC3024S Introduction to C++ Programming | Monday to Friday, 3rd period (10:00) | Two 4-hour practicals a week, "by arrangement", so untimed |

  - Which two afternoons hold the practicals is open, like a choice group. A plan is valid when two different weekdays work for the whole plan at once.
  - CSC3024S's practicals are untimed, so a plan with it is conditional.
  - The Science handbook's Schedule of Courses (p. 240) prints CSC3024S at 4th period on Monday, Thursday and Friday. Both course entries and its Courses by Lecture Period (p. 248) print 3rd period, Monday to Friday, so that is used **(assumption)**.
- **Complementary meetings corrected in the source workbook** at 2026's next approval: AGE1002S The Human Planet gains a Friday 5th-period meeting (12:00 to 12:45) and untimed tutorials, from the Science handbook's Schedule of Courses (p. 237) and Courses by Lecture Period (p. 250). SLL1069F French Communication gains its Thursday and Friday tutorials, untimed. Humanities' meridian runs 13:00 to 14:00. Until then, labels follow the corrected meetings.
  - For CSC2001F and CSC2002S, the timetable already gives the department's practical slot, so it stands.
- **The note on pp. 49 and 51** (Electrical, EB009 and EB809). It says "Some elective core courses in the first semester are in the same timetable slots and cannot be taken concurrently", but it names no courses. The approved timetable shows none of them overlapping, so the engine doesn't guess pairs. Final-year plan sets for those curricula carry a set-level conditional reason quoting the note **(assumption)**.

## 576-credit places

- Each curriculum's opening page gives 560 credits for "a candidate who registers in 2025" and 576 for one who registered before. So under the 2026 rules an intake before 2025 is on 576, and the degree total follows.
- **The places.** In the 576-credit curriculum, ASL1200S and CON2026S are core. A student who still owes one registers instead for an approved complementary course of at least 8 credits, timetable permitting. A place is owed when its course is outstanding, in a year at or before hers. The footnote marks place them:

| Curriculum | ASL1200S | CON2026S |
|---|---|---|
| EB009EEE01 | year 1 (p. 48) | year 1 (p. 48) |
| EB022EEE02 | year 1 (p. 52) | year 1 (p. 53). It's marked on years 1 and 2, and the earlier is taken |
| EB011EEE05 | year 2 (p. 57) | year 2 (p. 57) |
| EB809EEE01 | year 3 (p. 51) | year 2 (p. 50) |
| EB811EEE05 | year 3 (p. 60) | year 2 (p. 59) |
| EB822EEE02 | year 3 (p. 55) | year 2 (p. 55) |

- **Each owed place is a slot** for one complementary course of at least 8 credits. Two places take two different courses. A place where nothing fits is conditional.
- **A place already met** **(assumption)**:
  - Her passed approved complementary courses first fill her complementary lines, one course a line, whatever its credits.
  - Each course left over fills one owed place, earliest place first.
  - A pass in ASL1200S or CON2026S itself meets its place.
- **2023's rules** hold ASL1200S and CON2026S as ordinary core, with 576 credits for everyone (2023 FB3.2, p. 14). So there are no places under 2023.

## Slots

- There's one slot per complementary credit rule and one per owed place.
- **One approved course fills a complementary line**, whatever its credits, as pp. 42 and 44 ask for "at least one course from a list of approved electives". A course worth less than the line, such as SLL1016S's 15 against 18, is listed and marked as needing a check, and filling the line with one is conditional **(assumption)**. The degree's credit total still counts its real credits.
- **Each slot is a plan reason.**
  - Its kind is included, or conditional when no course fits or every course that fits is worth fewer credits than the line.
  - Its course_code is null.
  - Its message says what to add and how many courses fit.
  - Its details hold the credits, the fitting codes, the untimed codes, the codes worth fewer credits than the line, and for each fitting code the sections that fit and any section of the plan's own courses it forces. In EB011's third year, SLL1002S Word Power fits only in its 16:00 section and only with EEE3096S's Friday lab, and ECO1010F only in lecture group A.
  - **A forced section.** A listed course forces a section of a plan course when its own meetings rule out the other sections of that group, and every clash-free way of attending the plan with it added uses that section. It's reported even when the plan alone already uses that section. A course can only force a section in a term that overlaps its own, so ECO1010F, a first-semester course, never forces EEE3096S's second-semester lab.
- **What the list holds.** The complementary courses that fit the plan's timetable when that one course is added. A course fits when one choice of sections, for every course in the plan and the added course together, avoids every clash (see Alternatives).
  - It leaves out a course she has passed, or one a pass covers.
  - It leaves out a course whose entry rule she doesn't meet.
  - It keeps a course whose rule is unknown.
  - It lists a course with an untimed meeting, and marks it.
- **Not yet shown by the API.** The list sits in the reason's details, and a plan's credit total leaves slots out.
- **Under 2023's rules**, slots are conditional with nothing listed, as 2023 has no timetable or complementary list.

## Recorded alternatives

A plan records, for each choice group, every alternative that some clash-free way of attending the whole plan uses. One alternative left means every way uses it, so it's fixed. CSC3002F's practicals, for example, list only the day pairs that work with the rest of the plan. Labels still compare plans by their courses, not by their sections.

## Ranking, cap and names

- **Ranking.** Fewest conditional courses first, then fewer credits, then the plans' sorted course codes compared in order.
- **The cap.** At most 50 plans, with a log line when the cap is hit.
- **Combination.** The electives' codes in code order, joined with " · ", such as "EEE4117F · EEE4118F · EEE4119F". None when the plan has no electives.
- **Name.** One theme word per elective, in the same order, written "Power, Control & Robotics", "Power & Imaging" or "Imaging". A word two electives share appears once. A plan with no electives is "Core Courses Only". The words are B's, not print: EEE3093S Communications, EEE3094S Control, CSC2002S Computing, EEE4114F Signals, EEE4117F Power, EEE4118F Control, EEE4119F Robotics, EEE4120F Embedded, EEE4121F Wireless, EEE4126F Grids, HUB4049F Imaging, CSC3002F Networks, CSC3003S Algorithms and CSC3024S C++. An elective with no word is named by its printed course name.

## Reasons and their passages

- **Kinds.** excluded, conflict, conditional and included. A reason sits on the set or on one plan, and may name a course.
- **Passages.** Each reason points at the passage it rests on:
  - a course's own entry, for an entry rule
  - the group's table, found by its label, for a year rule
  - the year's last table, where the total prints, for the credit minimum
  - FB rules by number, such as FB3.4 or FB7
  - the footnote's table, for a 576 place
- **Likely null.** A course whose entry the handbook never prints, and "every year complete".

## Known gaps a label may meet

- **CSC2004Z.** Plans never add it. CSC3xxx's approved entry rules need a pass in it, so an EC student without it gets CSC3xxx excluded, with a reason naming CSC2004Z. Note (ii) (pp. 53 and 56) says an EC student must "register for and pass" it, which may allow taking it alongside.
- **The 576-credit places live in the engine's code**, not in the rulebook, as no rule shape can hold them.
- **2023 has no timetable**, so its plans carry a set-level reason that clashes weren't checked.
