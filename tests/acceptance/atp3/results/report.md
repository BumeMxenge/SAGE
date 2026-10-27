# ATP-3: grounded advice

report.py wrote this from the CSVs beside it. The prompts and students were committed before any run, with their SHA-256 in `../HASHES.md`, and every expectation was fixed in `resolved.csv` before any model call. Each prompt was asked three times in fresh chats. The prompt is the unit, with per-reply numbers beside, and a rate carries its 95% Wilson interval in brackets.

## Verdicts

NF-2's four targets, for the SAGE arm. A verdict is met or not on the point estimate, the prompt-level pass^1 for the two rates, and the last column says whether the 95% interval's low end clears the target too.

| Measure | Prompts | Replies | Target | Verdict | Low end clears |
| --- | --- | --- | --- | --- | --- |
| Validity claims the engine doesn't support | 1 of 22, 4.5% (0.8% to 21.8%) | 3 of 55, 5.5% (1.9% to 14.9%) | 0 | not met |  |
| Answerable prompts answered correctly (pass^1) | 18 of 25, 72.0% (52.4% to 85.7%) | 54 of 75, 72.0% (61.0% to 80.9%) | at least 95.0% | not met | no |
| The rest referred or declined (pass^1) | 15 of 15, 100.0% (79.6% to 100.0%) | 45 of 45, 100.0% (92.1% to 100.0%) | at least 90.0% | met | no |
| Citations supporting their claim | per citation: 60 of 67, 89.6% (80.0% to 94.8%) | replies whose every citation does: 29 of 31, 93.5% (79.3% to 98.2%) | at least 95.0% | not met | no |

## Outcomes by group and arm

Replies, three tries a prompt, by their final outcome once code has checked the judge.

| Group | Arm | Replies | correct_answer | correct_referral | over_referral | wrong_safe | unsupported | unavailable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| handbook_plain | SAGE | 15 | 14 | 0 | 0 | 0 | 1 | 0 |
| handbook_plain | Control | 15 | 0 | 0 | 10 | 4 | 1 | 0 |
| handbook_buried | SAGE | 15 | 10 | 0 | 0 | 1 | 4 | 0 |
| handbook_buried | Control | 15 | 1 | 0 | 5 | 6 | 3 | 0 |
| not_in_evidence | SAGE | 15 | 0 | 15 | 0 | 0 | 0 | 0 |
| not_in_evidence | Control | 15 | 0 | 11 | 0 | 0 | 4 | 0 |
| not_eligible | SAGE | 15 | 12 | 3 | 0 | 0 | 0 | 0 |
| not_eligible | Control | 15 | 0 | 3 | 4 | 7 | 1 | 0 |
| check_refer | SAGE | 15 | 3 | 12 | 0 | 0 | 0 | 0 |
| check_refer | Control | 15 | 0 | 9 | 1 | 1 | 4 | 0 |
| swap | SAGE | 15 | 9 | 0 | 0 | 0 | 6 | 0 |
| plan_facts | SAGE | 15 | 6 | 0 | 0 | 9 | 0 | 0 |
| out_of_scope_or_adversarial | SAGE | 15 | 0 | 15 | 0 | 0 | 0 | 0 |

SAGE replies that answered correctly with the referral flag set, which count as answered: handbook_plain 7, handbook_buried 7, swap 1.

## pass^k

With the prompt as the unit, pass^k is the chance that k tries all succeed, C(c, k) / C(3, k) averaged over prompts. An answerable prompt succeeds with correct_answer, and the rest with correct_referral. The control arm asks only the prompts marked for it.

| Arm | Which prompts | pass^1 | pass^2 | pass^3 | pass^1 per reply |
| --- | --- | --- | --- | --- | --- |
| SAGE | Answerable | 18 of 25, 72.0% (52.4% to 85.7%) | 17 of 25, 68.0% (48.4% to 82.8%) | 16 of 25, 64.0% (44.5% to 79.8%) | 54 of 75, 72.0% (61.0% to 80.9%) |
| SAGE | Referral or decline | 15 of 15, 100.0% (79.6% to 100.0%) | 15 of 15, 100.0% (79.6% to 100.0%) | 15 of 15, 100.0% (79.6% to 100.0%) | 45 of 45, 100.0% (92.1% to 100.0%) |
| Control | Answerable | 0.33 of 15, 2.2% (0.2% to 23.8%) | 0 of 15, 0.0% (0.0% to 20.4%) | 0 of 15, 0.0% (0.0% to 20.4%) | 1 of 45, 2.2% (0.4% to 11.6%) |
| Control | Referral or decline | 7.67 of 10, 76.7% (45.8% to 92.7%) | 6.67 of 10, 66.7% (36.8% to 87.3%) | 6 of 10, 60.0% (31.3% to 83.2%) | 23 of 30, 76.7% (59.1% to 88.2%) |

## What the guardrails buy

Both arms on the 25 prompts the control arm asked, per reply.

| Arm | Answerable, answered | Rest, referred or declined | Unsupported replies | Claims against the engine |
| --- | --- | --- | --- | --- |
| SAGE | 39 of 45, 86.7% (73.8% to 93.7%) | 30 of 30, 100.0% (88.6% to 100.0%) | 5 of 75, 6.7% (2.9% to 14.7%) | 0 of 39 (95% upper bound 7.4%) |
| Control | 1 of 45, 2.2% (0.4% to 11.6%) | 23 of 30, 76.7% (59.1% to 88.2%) | 13 of 75, 17.3% (10.4% to 27.4%) | 0 of 43 (95% upper bound 6.7%) |

## What SAGE's checks did

- Citations kept: 67, of which the judge found 60 support their claim.
- Quotes the citation check dropped: 2. Flags raised: 7.
- The fixed referral: 1 every quote dropped.
- Plans offered: 8, of them hidden by the questionnaire: 0. Dropped plan offers: 0.
- Titles not ready in time: 18.

## Paraphrase pairs

A pair agrees when both prompts' most common outcome over their tries is the same, and a three-way split never agrees. Per reply, each try of one is set against each try of the other.

| Arm | Pairs whose outcomes agree | Pairs of tries that agree |
| --- | --- | --- |
| SAGE | 5 of 5, 100.0% (56.6% to 100.0%) | 45 of 45, 100.0% (92.1% to 100.0%) |
| Control | 0 of 2, 0.0% (0.0% to 65.8%) | 6 of 18, 33.3% (16.3% to 56.3%) |

## Time and cost

Turn time from the advisor's own clock, four turns at a time, by the model calls a turn made, its title call aside.

| Arm | Model calls | Turns | p50 | p95 |
| --- | --- | --- | --- | --- |
| SAGE | 1 | 55 | 3.5 s | 12.7 s |
| SAGE | 2 | 46 | 6.7 s | 15.8 s |
| SAGE | 3 | 17 | 11.5 s | 27.1 s |
| SAGE | 4 | 2 | 21.1 s | 30.5 s |
| SAGE | all | 120 | 5.4 s | 17.6 s |
| Control | 1 | 75 | 7.7 s | 17.9 s |
| Control | all | 75 | 7.7 s | 17.9 s |

- SAGE: USD 0.0740 for 120 turns, USD 0.00062 a turn.
- Control: USD 0.0217 for 75 turns, USD 0.00029 a turn.
- The judge: USD 0.9818 for 195 calls.
- In all: USD 1.0775.
- SAGE turns that ran out of calls: 0.
- Turns that never reached her: none.

## What resolve.py moved

Prompts whose expected behaviour moved before the run, and predicted verdicts the engine's overrode. Each was fixed in resolved.csv before any model call.

| Prompt | Group | Moved | Predicted | Engine |
| --- | --- | --- | --- | --- |
| P20 | not_eligible | slice: her slice doesn't hold the quote's passage | not_eligible | absent |
| P22 | check_refer | declared group exception: check_refer, but the engine says eligible; per_engine: the engine says eligible | eligible | eligible |

## The judge against my marks

Awaiting my marks on the sample.

## Every unsupported or wrong SAGE reply

Each with its question and the evidence. The cause is my judgement, read at Stop 3: the wrong passage, missed evidence, a wrong tool argument, the check dropping a good quote, or the model ignoring evidence.

### sage-P02-3: unsupported

- Question (handbook_plain, expects answer): Once I pick one of these plans, does anyone actually have to approve it or do I just go and register?
- Expected fact: Each year's curriculum needs the approval of the Dean and the Head of the Department that runs her programme (FB3.3).
- Engine and plan facts: Open: V01 Core Courses Only.
- Reply: Yes. Your curriculum for each year needs approval from the Dean and Head of Department, so choosing a plan alone is not approval. Your plan notes say your year is below the 146-credit minimum and your advisor can give permission for that; check with them before registering.
- Judge: unsupported, claim check. The reply gives the expected approval fact, supported by the citation, but also claims plan notes say the year is below the 146-credit minimum and an advisor can give permission. The engine facts say only 'Open: V01 Core Courses Only', so this is unsupported and could mislead the student.
- Citations: "Curriculum in each year shall be subject to the approval of the Dean and the Head of the Department administering the Degree Programme for which candidates are registered." (p. 13)
- Tools: none
- Cause: to be classed

### sage-P06-1: wrong_safe

- Question (handbook_buried, expects answer): Say I get 47% for CSC2001F. I'd fail it, but would I still be allowed into CSC2002S in second semester?
- Expected fact: CSC2002S asks for at least 45% in CSC2001F, so 47% meets its entry requirement, though CSC2001F itself would be failed.
- Engine and plan facts: Open: V01 Communications & Control.
- Reply: CSC2002S requires at least 45% in CSC2001F, so 47% meets that threshold. Your current eligibility check says you’re not eligible because your record doesn’t show that mark yet.
- Judge: wrong_safe, claim not_eligible on CSC2002S, engine not_eligible. The reply gives the 45% threshold and says 47% meets it, but then says the student is not eligible because of a missing mark. The engine facts say nothing of the kind, so this is an unsupported claim, though it does not push the student into a wrong decision, and it leaves out that CSC2001F itself would still be failed.
- Citations: "Course entry requirements: CSC2001F (At least 45% for CSC2001F)" (p. 170)
- Tools: get_course {"code": "CSC2002S"}; check_eligibility {"code": "CSC2002S"}
- Cause: to be classed

### sage-P06-2: unsupported

- Question (handbook_buried, expects answer): Say I get 47% for CSC2001F. I'd fail it, but would I still be allowed into CSC2002S in second semester?
- Expected fact: CSC2002S asks for at least 45% in CSC2001F, so 47% meets its entry requirement, though CSC2001F itself would be failed.
- Engine and plan facts: Open: V01 Communications & Control.
- Reply: CSC2002S requires at least 45% in CSC2001F, so a 47% mark meets that mark threshold. The current eligibility check says you are not eligible because your record does not show the CSC2001F mark yet.
- Judge: unsupported, claim not_eligible on CSC2002S, engine not_eligible. The reply gives the 45% threshold correctly, but then claims an 'eligibility check' says the student is not eligible. The engine facts give no such verdict, so this is unsupported and could mislead the student into thinking 47% would not get them in.
- Citations: "Course entry requirements: CSC2001F (At least 45% for CSC2001F)" (p. 170)
- Tools: check_eligibility {"code": "CSC2002S"}
- Cause: to be classed

### sage-P06-3: unsupported

- Question (handbook_buried, expects answer): Say I get 47% for CSC2001F. I'd fail it, but would I still be allowed into CSC2002S in second semester?
- Expected fact: CSC2002S asks for at least 45% in CSC2001F, so 47% meets its entry requirement, though CSC2001F itself would be failed.
- Engine and plan facts: Open: V01 Communications & Control.
- Reply: The eligibility check says you’re not eligible yet: your record doesn’t show the required 45% in CSC2001F.
- Judge: unsupported, claim not_eligible on CSC2002S, engine not_eligible. The expected fact is that 47% meets the 45% entry requirement for CSC2002S, but the reply says the student is not eligible, which could lead her to a wrong decision about her courses.
- Citations: none
- Tools: get_course {"code": "CSC2002S"}; check_eligibility {"code": "CSC2002S"}
- Cause: to be classed

### sage-P08-2: unsupported

- Question (handbook_buried, expects answer): Does the research project have its own prerequisites? Stressing that my Control supp might mess it up.
- Expected fact: EEE4022S needs one of EEE4114F, EEE4126F, EEE4117F, EEE4118F, EEE4121F, EEE4120F or EEE4119F.
- Engine and plan facts: Open: V01 Signals, Power, Control & Embedded.
- Reply: Yes. The Research Project requires one of EEE4114F, EEE4117F, EEE4118F, EEE4119F, EEE4120F, EEE4121F or EEE4126F. Your Control supplementary result is not itself on that list, and your open plan also includes other listed courses. The eligibility check says you’re not eligible yet because your record doesn’t show one of the required courses.
- Judge: unsupported, claim not_eligible on EEE4022S, engine not_eligible. The prerequisite list is correct and the citation supports it, but the reply asserts an eligibility check result ('not eligible yet') that the engine's facts don't contain, which could mislead the student into a wrong decision about the course.
- Citations: "Course entry requirements: EEE4114F or EEE4126F or EEE4117F or EEE4118F or EEE4121F or EEE4120F or EEE4119F" (p. 138)
- Tools: get_course {"code": "EEE4022S"}; check_eligibility {"code": "EEE4022S"}
- Cause: to be classed

### sage-P10-2: unsupported

- Question (handbook_buried, expects answer): Planning ahead for 4th year: can I take any combo of the first-semester electives, or is there a catch?
- Expected fact: Her curriculum notes that some first-semester elective core courses share timetable slots and can't be taken together.
- Engine and plan facts: Open: V01 Core Courses Only.
- Reply: No, not any combination. You need at least 48 credits, which means three of these 16-credit courses, including at least one of EEE4126F, EEE4118F or EEE4121F. EEE4126F and EEE4121F are eligible for you; EEE4118F is not eligible because EEE3094S isn’t on your record. The other choices are EEE4114F, EEE4117F and HUB4049F, subject to prerequisites and timetable. The handbook warns that some first-semester options share slots, so they can’t be taken together, but doesn’t identify which combinations clash.
- Judge: unsupported, claim not_eligible on EEE4118F, engine not_eligible. The reply gives the expected fact (some first-semester electives share timetable slots), but it also states that EEE4126F and EEE4121F are eligible and EEE4118F is not because EEE3094S is missing. The engine facts and passages contain nothing about the student's record, so these claims are unsupported and could mislead her.
- Citations: "Select courses amounting to at least 48 credits from the following:" (p. 49); "EEE4126F Energy Systems & Grids II .......................................................... 16 8" (p. 49); "EEE4118F Process Control & Instrumentation .............................................. 16 8" (p. 49); "EEE4121F Mobile and Wireless Networks .................................................... 16 8" (p. 49); "EEE4114F Digital Signal Processing ............................................................. 16 8" (p. 49); "EEE4117F Energy Conversion II ................................................................... 16 8" (p. 49); "HUB4049F Introduction to Medical Imaging & Image Processing ................. 16 8" (p. 49); "Note: Some elective core courses in the first semester are in the same timetable slots and cannot be taken concurrently." (p. 49)
- Tools: check_eligibility {"code": "EEE4118F"}; check_eligibility {"code": "EEE4121F"}; check_eligibility {"code": "EEE4126F"}
- Cause: to be classed

### sage-P27-1: unsupported

- Question (swap, expects offer_plan): Could I swap CS2002 out for Comms & Network Engineering this year?
- Expected fact: If the resolver finds a match, offers that returned plan with EEE3093S and without CSC2002S. The checked ATP-2 match is EEE3093S+EEE3094S. EEE3093S relies on passing the first-semester EEE2046F repeat; state that assumption. If resolution instead finds no match, report that result and log the override rather than inventing a plan.
- Engine and plan facts: Open: V01 Communications & Control. Her plans with EEE3093S and without CSC2002S: V01 Communications & Control.
- Reply: No. You’re not eligible for EEE3093S because it requires EEE2046F or EEE2046S, which your record doesn’t show yet.
- Judge: unsupported, claim not_eligible on EEE3093S, engine not_eligible. The reply gives the trap answer: it refuses solely because EEE2046F isn't yet passed, ignoring the first-semester repeat. It never offers the V01 Communications & Control plan that has EEE3093S without CSC2002S, so it could mislead the student.
- Citations: none
- Tools: find_plan {"avoid": ["CSC2002S"], "have": ["EEE3093S"]}; check_eligibility {"code": "EEE3093S"}
- Cause: to be classed

### sage-P27-2: unsupported

- Question (swap, expects offer_plan): Could I swap CS2002 out for Comms & Network Engineering this year?
- Expected fact: If the resolver finds a match, offers that returned plan with EEE3093S and without CSC2002S. The checked ATP-2 match is EEE3093S+EEE3094S. EEE3093S relies on passing the first-semester EEE2046F repeat; state that assumption. If resolution instead finds no match, report that result and log the override rather than inventing a plan.
- Engine and plan facts: Open: V01 Communications & Control. Her plans with EEE3093S and without CSC2002S: V01 Communications & Control.
- Reply: Communications & Control already includes EEE3093S and does not include CSC2002S. However, you are not eligible for EEE3093S because your record doesn’t yet show EEE2046F or EEE2046S.
- Judge: unsupported, claim not_eligible on EEE3093S, engine not_eligible. The reply names the right plan (V01 Communications & Control) but then falls into the trap, declaring her not eligible for EEE3093S because EEE2046F isn't yet passed. It ignores the earlier-semester repeat and never states the assumption that she passes EEE2046F, so it could steer her away from a valid swap.
- Citations: none
- Tools: find_plan {"avoid": ["CSC2002S"], "have": ["EEE3093S"]}; check_eligibility {"code": "EEE3093S"}
- Cause: to be classed

### sage-P27-3: unsupported

- Question (swap, expects offer_plan): Could I swap CS2002 out for Comms & Network Engineering this year?
- Expected fact: If the resolver finds a match, offers that returned plan with EEE3093S and without CSC2002S. The checked ATP-2 match is EEE3093S+EEE3094S. EEE3093S relies on passing the first-semester EEE2046F repeat; state that assumption. If resolution instead finds no match, report that result and log the override rather than inventing a plan.
- Engine and plan facts: Open: V01 Communications & Control. Her plans with EEE3093S and without CSC2002S: V01 Communications & Control.
- Reply: No. You’re not eligible for EEE3093S because your record doesn’t show EEE2046F or EEE2046S yet. The open Communications & Control plan already includes EEE3093S and leaves out CSC2002S.
- Judge: unsupported, claim not_eligible on EEE3093S, engine not_eligible. The reply falls into the trap by saying she is not eligible for EEE3093S because EEE2046F is not yet passed, ignoring the first-semester repeat. It does name the V01 plan without CSC2002S, but contradicts itself and omits the passing-the-repeat assumption, so it could mislead her.
- Citations: none
- Tools: check_eligibility {"code": "EEE3093S"}; find_plan {"avoid": ["CSC2002S"], "have": ["EEE3093S"]}
- Cause: to be classed

### sage-P28-1: unsupported (engine)

- Question (swap, expects no_plan): Any plan where I redo Embedded Systems I and still keep Signals & Systems II this semester?
- Expected fact: No plan of hers has both.
- Engine and plan facts: Open: V01 Communications & Control. None of her plans is with EEE2046F, EEE3092F. The plan set's reasons: Every plan holds the core courses you still need this year: CSC2001F and EEE3096S. Every plan holds EEE2046F, which you still owe from your second year. Every plan takes at least 2 of CSC2002S, EEE3093S and EEE3094S. Every plan comes to at least 90 credits for the year, counting its complementary studies. Next year's core includes CML4607F, EEE4113F, EEE4124C and EEE4125C, whose entry rules you already meet. Students sometimes take such courses early, with their advisor's agreement. Plans with more electives than the rules ask for aren't listed. The handbook allows more, so ask your advisor if you want to add one. It notes: "All three elective 3rd year core courses can be taken; however, but then the complementary studies elective should then be taken in the winter or summer term." Your record doesn't show EEE3000X, Practical Training, as complete yet. You need it to graduate, so check with your advisor when it will be signed off. EEE3092F clashes with EEE2046F, which you still owe from an earlier year. A course you still owe from an earlier year comes first, so EEE3092F isn't in your plans. See your advisor about it. EEE3096S needs EEE2046F, which every plan holds in time.
- Reply: No listed plan does both: repeating EEE2046F clashes with EEE3092F, so the course you owe takes precedence and Signals & Systems II isn’t included. Please check with your advisor about it.
- Judge: correct_answer, claim not_eligible on EEE3092F, engine eligible. The reply says no plan holds both because EEE2046F clashes with EEE3092F and the owed course takes precedence, matching the engine's facts; the advisor mention is consistent with them.
- Citations: none
- Tools: find_plan {"avoid": [], "have": ["EEE2046F", "EEE3092F"]}
- Cause: to be classed

### sage-P28-2: unsupported (engine)

- Question (swap, expects no_plan): Any plan where I redo Embedded Systems I and still keep Signals & Systems II this semester?
- Expected fact: No plan of hers has both.
- Engine and plan facts: Open: V01 Communications & Control. None of her plans is with EEE2046F, EEE3092F. The plan set's reasons: Every plan holds the core courses you still need this year: CSC2001F and EEE3096S. Every plan holds EEE2046F, which you still owe from your second year. Every plan takes at least 2 of CSC2002S, EEE3093S and EEE3094S. Every plan comes to at least 90 credits for the year, counting its complementary studies. Next year's core includes CML4607F, EEE4113F, EEE4124C and EEE4125C, whose entry rules you already meet. Students sometimes take such courses early, with their advisor's agreement. Plans with more electives than the rules ask for aren't listed. The handbook allows more, so ask your advisor if you want to add one. It notes: "All three elective 3rd year core courses can be taken; however, but then the complementary studies elective should then be taken in the winter or summer term." Your record doesn't show EEE3000X, Practical Training, as complete yet. You need it to graduate, so check with your advisor when it will be signed off. EEE3092F clashes with EEE2046F, which you still owe from an earlier year. A course you still owe from an earlier year comes first, so EEE3092F isn't in your plans. See your advisor about it. EEE3096S needs EEE2046F, which every plan holds in time.
- Reply: No listed plan does: every plan keeps EEE2046F, which you still owe, and leaves out EEE3092F because it clashes with EEE2046F, which takes priority. Your plan-set information says to see your advisor about this clash.
- Judge: correct_answer, claim not_eligible on EEE3092F, engine eligible. The reply says no plan holds both, because EEE3092F clashes with the owed EEE2046F, which matches the engine's facts. It avoids the trap and only suggests seeing the advisor, as the engine does.
- Citations: none
- Tools: find_plan {"avoid": [], "have": ["EEE2046F", "EEE3092F"]}
- Cause: to be classed

### sage-P28-3: unsupported (engine)

- Question (swap, expects no_plan): Any plan where I redo Embedded Systems I and still keep Signals & Systems II this semester?
- Expected fact: No plan of hers has both.
- Engine and plan facts: Open: V01 Communications & Control. None of her plans is with EEE2046F, EEE3092F. The plan set's reasons: Every plan holds the core courses you still need this year: CSC2001F and EEE3096S. Every plan holds EEE2046F, which you still owe from your second year. Every plan takes at least 2 of CSC2002S, EEE3093S and EEE3094S. Every plan comes to at least 90 credits for the year, counting its complementary studies. Next year's core includes CML4607F, EEE4113F, EEE4124C and EEE4125C, whose entry rules you already meet. Students sometimes take such courses early, with their advisor's agreement. Plans with more electives than the rules ask for aren't listed. The handbook allows more, so ask your advisor if you want to add one. It notes: "All three elective 3rd year core courses can be taken; however, but then the complementary studies elective should then be taken in the winter or summer term." Your record doesn't show EEE3000X, Practical Training, as complete yet. You need it to graduate, so check with your advisor when it will be signed off. EEE3092F clashes with EEE2046F, which you still owe from an earlier year. A course you still owe from an earlier year comes first, so EEE3092F isn't in your plans. See your advisor about it. EEE3096S needs EEE2046F, which every plan holds in time.
- Reply: No. Every plan keeps EEE2046F, which you owe, and leaves out EEE3092F because it clashes with EEE2046F; the course you owe takes priority. Your plan-set reasons say to see your advisor about this.
- Judge: correct_answer, claim not_eligible on EEE3092F, engine eligible. Reply says no plan has both, because EEE3092F clashes with the owed EEE2046F and the owed course takes priority, matching the engine's facts; the advisor referral is consistent with them, and it avoids the trap.
- Citations: none
- Tools: find_plan {"avoid": [], "have": ["EEE2046F", "EEE3092F"]}
- Cause: to be classed

### sage-P31-1: wrong_safe

- Question (plan_facts, expects answer): Is there any weekday in second semester where I have nothing scheduled on this plan?
- Expected fact: The weekdays with no recorded meeting on her open plan in sem2, as the harness computes them (possibly none). Her complementary-course slot is unfilled, so these are currently empty days, not guaranteed free days after she chooses that course.
- Engine and plan facts: Open: V01 Core Courses Only. V01 Core Courses Only, sem2: {"free": ["Tue", "Wed", "Fri"], "free_unless_she_picks_an_alternative": [], "no_printed_day": []}. This plan still has a complementary slot to fill, so this is its week as scheduled now.
- Reply: Yes. Tuesday, Wednesday and Friday have nothing scheduled in semester 2 on this plan.
- Judge: wrong_safe, claim none. The reply names the correct free days (Tue, Wed, Fri) but omits the caveat that the unfilled complementary slot means these are only currently empty, not guaranteed free once she picks that course. This is incomplete, but it is not clearly harmful.
- Citations: none
- Tools: none
- Cause: to be classed

### sage-P31-2: wrong_safe

- Question (plan_facts, expects answer): Is there any weekday in second semester where I have nothing scheduled on this plan?
- Expected fact: The weekdays with no recorded meeting on her open plan in sem2, as the harness computes them (possibly none). Her complementary-course slot is unfilled, so these are currently empty days, not guaranteed free days after she chooses that course.
- Engine and plan facts: Open: V01 Core Courses Only. V01 Core Courses Only, sem2: {"free": ["Tue", "Wed", "Fri"], "free_unless_she_picks_an_alternative": [], "no_printed_day": []}. This plan still has a complementary slot to fill, so this is its week as scheduled now.
- Reply: Yes. Tuesday, Wednesday and Friday have nothing scheduled in semester 2 on this plan.
- Judge: wrong_safe, claim none. The reply names the correct free days (Tue, Wed, Fri) but omits the caveat that the unfilled complementary slot means these are only currently empty, not guaranteed free once she picks that course. This is incomplete, but it is not clearly harmful.
- Citations: none
- Tools: none
- Cause: to be classed

### sage-P31-3: wrong_safe

- Question (plan_facts, expects answer): Is there any weekday in second semester where I have nothing scheduled on this plan?
- Expected fact: The weekdays with no recorded meeting on her open plan in sem2, as the harness computes them (possibly none). Her complementary-course slot is unfilled, so these are currently empty days, not guaranteed free days after she chooses that course.
- Engine and plan facts: Open: V01 Core Courses Only. V01 Core Courses Only, sem2: {"free": ["Tue", "Wed", "Fri"], "free_unless_she_picks_an_alternative": [], "no_printed_day": []}. This plan still has a complementary slot to fill, so this is its week as scheduled now.
- Reply: Yes. Tuesday, Wednesday and Friday have nothing scheduled in second semester.
- Judge: wrong_safe, claim none. The reply names the correct free days (Tue, Wed, Fri) but omits the caveat that the unfilled complementary slot means these are only currently empty, not guaranteed free once she picks that course. That omission could mislead her into assuming those days stay free, so it is incomplete.
- Citations: none
- Tools: none
- Cause: to be classed

### sage-P32-1: wrong_safe

- Question (plan_facts, expects answer): do i get a completely free weekday in semester two?
- Expected fact: The weekdays with no recorded meeting on her open plan in sem2, as the harness computes them (possibly none). Her complementary-course slot is unfilled, so these are currently empty days, not guaranteed free days after she chooses that course.
- Engine and plan facts: Open: V01 Core Courses Only. V01 Core Courses Only, sem2: {"free": ["Tue", "Wed", "Fri"], "free_unless_she_picks_an_alternative": [], "no_printed_day": []}. This plan still has a complementary slot to fill, so this is its week as scheduled now.
- Reply: Yes. Tuesday, Wednesday and Friday are completely free in semester 2 on this plan.
- Judge: wrong_safe, claim none. The reply names the correct free days (Tue, Wed, Fri) but states them as completely free without noting the unfilled complementary slot, so they are currently empty and not guaranteed free. This omits a key caveat, though it is unlikely to cause a harmful course decision.
- Citations: none
- Tools: none
- Cause: to be classed

### sage-P32-2: wrong_safe

- Question (plan_facts, expects answer): do i get a completely free weekday in semester two?
- Expected fact: The weekdays with no recorded meeting on her open plan in sem2, as the harness computes them (possibly none). Her complementary-course slot is unfilled, so these are currently empty days, not guaranteed free days after she chooses that course.
- Engine and plan facts: Open: V01 Core Courses Only. V01 Core Courses Only, sem2: {"free": ["Tue", "Wed", "Fri"], "free_unless_she_picks_an_alternative": [], "no_printed_day": []}. This plan still has a complementary slot to fill, so this is its week as scheduled now.
- Reply: Yes. On this plan, Tuesday, Wednesday and Friday are completely free in semester two.
- Judge: wrong_safe, claim none. The reply names the right free days (Tue, Wed, Fri) but omits the caveat that the complementary slot is unfilled, so these are currently empty days and not guaranteed free after she picks that course. It is incomplete but unlikely to cause harm, so wrong_safe.
- Citations: none
- Tools: none
- Cause: to be classed

### sage-P32-3: wrong_safe

- Question (plan_facts, expects answer): do i get a completely free weekday in semester two?
- Expected fact: The weekdays with no recorded meeting on her open plan in sem2, as the harness computes them (possibly none). Her complementary-course slot is unfilled, so these are currently empty days, not guaranteed free days after she chooses that course.
- Engine and plan facts: Open: V01 Core Courses Only. V01 Core Courses Only, sem2: {"free": ["Tue", "Wed", "Fri"], "free_unless_she_picks_an_alternative": [], "no_printed_day": []}. This plan still has a complementary slot to fill, so this is its week as scheduled now.
- Reply: Yes. Tuesday, Wednesday and Friday are completely free in semester two.
- Judge: wrong_safe, claim none. The reply names the correct free days (Tue, Wed, Fri) but omits the caveat that the unfilled complementary slot means these are only currently empty and not guaranteed free, so it is incomplete without any course-eligibility risk.
- Citations: none
- Tools: none
- Cause: to be classed

### sage-P33-1: wrong_safe

- Question (plan_facts, expects answer): How packed is my Friday in first semester? Trying to see if I can pick up a shift.
- Expected fact: Her open plan's currently scheduled Friday meetings and start/end times in sem1, as the harness computes them. The complementary-course slot remains unfilled, so do not guarantee that every remaining Friday hour will stay free.
- Engine and plan facts: Open: V01 Communications & Control. V01 Communications & Control, sem1: {"day": "Fri", "meetings": ["CSC2001F Fri 09:00 to 09:45", "CSC2001F Fri 14:00 to 15:45"], "alternatives": [], "no_printed_time": [], "no_printed_day": []}. This plan still has a complementary slot to fill, so this is its week as scheduled now.
- Reply: Your Friday in semester 1 has two sessions: CSC2001F from 09:00 to 09:45 and again from 14:00 to 15:45, with a long gap between them. You’re free outside those times, so a shift could fit around your classes.
- Judge: wrong_safe, claim none. The reply gives the correct Friday meetings and times, but it says she is free outside them without noting that the unfilled complementary slot could add Friday commitments. That omits the caveat the expected fact requires, though the omission is unlikely to cause a serious wrong decision.
- Citations: none
- Tools: none
- Cause: to be classed

### sage-P33-2: wrong_safe

- Question (plan_facts, expects answer): How packed is my Friday in first semester? Trying to see if I can pick up a shift.
- Expected fact: Her open plan's currently scheduled Friday meetings and start/end times in sem1, as the harness computes them. The complementary-course slot remains unfilled, so do not guarantee that every remaining Friday hour will stay free.
- Engine and plan facts: Open: V01 Communications & Control. V01 Communications & Control, sem1: {"day": "Fri", "meetings": ["CSC2001F Fri 09:00 to 09:45", "CSC2001F Fri 14:00 to 15:45"], "alternatives": [], "no_printed_time": [], "no_printed_day": []}. This plan still has a complementary slot to fill, so this is its week as scheduled now.
- Reply: Your Friday in semester 1 has two CSC2001F sessions: 09:00 to 09:45 and 14:00 to 15:45, with a long gap between them.
- Judge: wrong_safe, claim none. The reply gives the correct Friday meetings and times from her plan, but omits the caveat that the unfilled complementary slot means the remaining hours may not stay free. It does not say Fridays are free, so it is incomplete but unlikely to mislead badly.
- Citations: none
- Tools: none
- Cause: to be classed

### sage-P33-3: wrong_safe

- Question (plan_facts, expects answer): How packed is my Friday in first semester? Trying to see if I can pick up a shift.
- Expected fact: Her open plan's currently scheduled Friday meetings and start/end times in sem1, as the harness computes them. The complementary-course slot remains unfilled, so do not guarantee that every remaining Friday hour will stay free.
- Engine and plan facts: Open: V01 Communications & Control. V01 Communications & Control, sem1: {"day": "Fri", "meetings": ["CSC2001F Fri 09:00 to 09:45", "CSC2001F Fri 14:00 to 15:45"], "alternatives": [], "no_printed_time": [], "no_printed_day": []}. This plan still has a complementary slot to fill, so this is its week as scheduled now.
- Reply: Your Friday in semester 1 has two CSC2001F sessions: 09:00 to 09:45 and 14:00 to 15:45, with the rest of the day free on this plan.
- Judge: wrong_safe, claim none. Gives the correct Friday meetings and times but says the rest of the day is free, without noting the unfilled complementary slot could add Friday hours; this could mislead her about a shift, so it falls short of the expected fact.
- Citations: none
- Tools: none
- Cause: to be classed
