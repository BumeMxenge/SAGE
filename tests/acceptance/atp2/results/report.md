# ATP-2: the engine's decisions and plans

report.py wrote this from the CSVs beside it, which run.py wrote, and causes.csv, written by hand after the first run. A rate has its 95% Wilson interval in brackets, and a count with none wrong gives the one-sided 95% upper bound, 1 − 0.05^(1/n). The held-out records lead. The failure sweep follows, and the base records come last, as the engine was built on on-track students.

## Verdicts

ATP-2's pass criterion (Table 3.4): "Every decision matches its label, and plan sets hold every valid plan once and nothing else." It verifies F-2, F-3 and NF-1, and NF-4's single-session 10 s. The sweep's records have no labels, so there the checker is the oracle. F-3's ranking is left out, as the checker doesn't rank. Two label slips were confirmed after the run, so each line they touch is given twice: as labelled, and with the slips confirmed, counted as the engine's matches.

| Requirement | Measure | Held out | Held out, without judgement calls | Failure sweep | In-sample base | Target | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| F-2, F-3, NF-1 | Every labelled item but the pages matches its label: the pass criterion | 100 of 116, 86.2% (78.8% to 91.3%) | 67 of 82, 81.7% (72.0% to 88.6%) | none to count | none to count | 100% | not met |
| F-2, F-3, NF-1 | Every labelled item but the pages matches its label: the pass criterion, with the label slips confirmed after the run | 101 of 116, 87.1% (79.8% to 92.0%) | 67 of 82, 81.7% (72.0% to 88.6%) | none to count | none to count | 100% | not met |
| F-2, NF-1 | Focal decisions whose status and deciding codes match the label | 46 of 61, 75.4% (63.3% to 84.5%) | 45 of 60, 75.0% (62.8% to 84.2%) | none to count | none to count | 100% | not met |
| F-2 | Citing the handbook: cited pages that are the label's, of decisions citing one | 10 of 15, 66.7% (41.7% to 84.8%) | 10 of 15, 66.7% (41.7% to 84.8%) | none to count | none to count |  | reported |
| F-2 | Citing the handbook: cited pages that are the label's, of decisions citing one, with the label slips confirmed after the run | 11 of 15, 73.3% (48.0% to 89.1%) | 11 of 15, 73.3% (48.0% to 89.1%) | none to count | none to count |  | reported |
| F-2 | Citing the handbook: decisions citing no page, in check() or a plan reason | 17 of 32, 53.1% (36.4% to 69.1%) | 16 of 31, 51.6% (34.8% to 68.0%) | none to count | none to count |  | reported |
| F-3, NF-1 | Plan counts and combinations that match the labels | 12 of 12, 100.0% (75.8% to 100.0%) | 4 of 4, 100.0% (51.0% to 100.0%) | none to count | none to count | 100% | met |
| F-3 | Plans whose slots match the labels | 6 of 6, 100.0% (61.0% to 100.0%) | 2 of 2, 100.0% (34.2% to 100.0%) | none to count | none to count | 100% | met |
| NF-1 | Years of study, and owed and excluded core, that match the labels | 18 of 18, 100.0% (82.4% to 100.0%) | 6 of 6, 100.0% (61.0% to 100.0%) | none to count | none to count | 100% | met |
| NF-1 | Set-level reasons print requires that the engine gives, by kind and codes | 18 of 19, 94.7% (75.4% to 99.1%) | 10 of 10, 100.0% (72.2% to 100.0%) | none to count | none to count | 100% | not met |
| NF-1 | Set-level reasons print requires that the engine gives, by kind and codes, with the label slips confirmed after the run | 19 of 19, 100.0% (83.2% to 100.0%) | 10 of 10, 100.0% (72.2% to 100.0%) | none to count | none to count | 100% | met |
| F-2, NF-1 | Statuses the engine and the checker agree on | 489 of 489, 100.0% (99.2% to 100.0%) | 235 of 235, 100.0% (98.4% to 100.0%) | 22025 of 22025, 100.0% (100.0% to 100.0%) | 837 of 837, 100.0% (99.5% to 100.0%) | 100% | met |
| F-3, NF-1 | Records whose plan set is exactly the checker's | 6 of 6, 100.0% (61.0% to 100.0%) | 2 of 2, 100.0% (34.2% to 100.0%) | 510 of 510, 100.0% (99.3% to 100.0%) | 21 of 21, 100.0% (84.5% to 100.0%) | 100% | met |
| F-3, NF-1 | Valid plans the engine leaves out, of the checker's | 0 of 19 (95% upper bound 14.6%) | 0 of 2 (95% upper bound 77.6%) | 0 of 1249 (95% upper bound 0.2%) | 0 of 97 (95% upper bound 3.0%) | 0 | met |
| F-3, NF-1 | Plans the engine gives that aren't valid, of the engine's | 0 of 19 (95% upper bound 14.6%) | 0 of 2 (95% upper bound 77.6%) | 0 of 1249 (95% upper bound 0.2%) | 0 of 97 (95% upper bound 3.0%) | 0 | met |
| F-3, NF-1 | Plans the engine lists twice, of the engine's | 0 of 19 (95% upper bound 14.6%) | 0 of 2 (95% upper bound 77.6%) | 0 of 1249 (95% upper bound 0.2%) | 0 of 97 (95% upper bound 3.0%) | 0 | met |
| F-3 | Slots whose credits, owed course and fitting courses agree, in plans both hold | 7 of 7, 100.0% (64.6% to 100.0%) | 2 of 2, 100.0% (34.2% to 100.0%) | 217 of 217, 100.0% (98.3% to 100.0%) | 11 of 11, 100.0% (74.1% to 100.0%) | 100% | met |
| NF-1 | Plans resting on judgement whose every open or untimed course has a conditional reason | 12 of 12, 100.0% (75.8% to 100.0%) | none to count | 478 of 478, 100.0% (99.2% to 100.0%) | 6 of 6, 100.0% (61.0% to 100.0%) | 100% | met |
| NF-4 | Generate's p95 over every run, one session at a time | 0.677 s over 30 runs | 0.414 s over 10 runs | 0.243 s over 2550 runs | 0.306 s over 105 runs | within 10 s | met |
| F-2, F-3 | Metamorphic relations broken, of the instances where they apply | none to count | none to count | 0 of 3757 (95% upper bound 0.1%) | 0 of 226 (95% upper bound 1.3%) | 0 | met |

## Held out: against the labels

Six records labelled from print and committed before the first run, with 32 focal decisions. Four records and one decision row are judgement calls, so each table is given with them and without. A record's fields carry its own flag, and a decision's fields the decision's. Deciding codes and text pages are matched as text, as the labels' README says. The checker gives no reasons or pages, so it has none to match there. A field the two label slips confirmed after the run touch is given again with the slips confirmed, counted as the engine's matches.

| Field | Items | Engine right | Without judgement calls | No citation | Checker right | Without judgement calls |
| --- | --- | --- | --- | --- | --- | --- |
| year_of_study | 6 | 6 of 6, 100.0% (61.0% to 100.0%) | 2 of 2, 100.0% (34.2% to 100.0%) | 0 | 6 of 6, 100.0% (61.0% to 100.0%) | 2 of 2, 100.0% (34.2% to 100.0%) |
| owed_core | 6 | 6 of 6, 100.0% (61.0% to 100.0%) | 2 of 2, 100.0% (34.2% to 100.0%) | 0 | 6 of 6, 100.0% (61.0% to 100.0%) | 2 of 2, 100.0% (34.2% to 100.0%) |
| excluded_core | 6 | 6 of 6, 100.0% (61.0% to 100.0%) | 2 of 2, 100.0% (34.2% to 100.0%) | 0 | 6 of 6, 100.0% (61.0% to 100.0%) | 2 of 2, 100.0% (34.2% to 100.0%) |
| expected_plans | 6 | 6 of 6, 100.0% (61.0% to 100.0%) | 2 of 2, 100.0% (34.2% to 100.0%) | 0 | 6 of 6, 100.0% (61.0% to 100.0%) | 2 of 2, 100.0% (34.2% to 100.0%) |
| expected_combinations | 6 | 6 of 6, 100.0% (61.0% to 100.0%) | 2 of 2, 100.0% (34.2% to 100.0%) | 0 | 6 of 6, 100.0% (61.0% to 100.0%) | 2 of 2, 100.0% (34.2% to 100.0%) |
| expected_slots | 6 | 6 of 6, 100.0% (61.0% to 100.0%) | 2 of 2, 100.0% (34.2% to 100.0%) | 0 | 6 of 6, 100.0% (61.0% to 100.0%) | 2 of 2, 100.0% (34.2% to 100.0%) |
| set_reason | 19 | 18 of 19, 94.7% (75.4% to 99.1%) | 10 of 10, 100.0% (72.2% to 100.0%) | 0 | none to count | none to count |
| set_reason, with the label slips confirmed after the run | 19 | 19 of 19, 100.0% (83.2% to 100.0%) | 10 of 10, 100.0% (72.2% to 100.0%) | 0 | none to count | none to count |
| status | 32 | 31 of 32, 96.9% (84.3% to 99.4%) | 30 of 31, 96.8% (83.8% to 99.4%) | 0 | 31 of 32, 96.9% (84.3% to 99.4%) | 30 of 31, 96.8% (83.8% to 99.4%) |
| deciding_codes | 29 | 15 of 29, 51.7% (34.4% to 68.6%) | 15 of 29, 51.7% (34.4% to 68.6%) | 0 | none to count | none to count |
| page | 32 | 10 of 15, 66.7% (41.7% to 84.8%) | 10 of 15, 66.7% (41.7% to 84.8%) | 17 | none to count | none to count |
| page, with the label slips confirmed after the run | 32 | 11 of 15, 73.3% (48.0% to 89.1%) | 11 of 15, 73.3% (48.0% to 89.1%) | 17 | none to count | none to count |

Every labelled item the engine or the checker doesn't match:

| Record | Field | Item | Label | Engine | Checker | Judgement call | Cause |
| --- | --- | --- | --- | --- | --- | --- | --- |
| signals1-failed | deciding_codes | EEE2047S | MAM1021S |  |  | no | semantics gap: Every one is an eligible decision. SEMANTICS.md gives check and not_eligible their reason and eligible none, so check() returns an eligible decision with no reason, which names nothing that met the rule. The labels expect it to name the course that did. |
| signals1-failed | page | EEE2047S | 132 |  |  | no | semantics gap: No citation: check() returns a status and a reason, never a passage (ENGINE_INTERFACE.md), and its reason cites no page, and the plan set holds no reason about the course. SEMANTICS.md ties passages to plan reasons alone, so F-2's "citing the handbook" rests on them. |
| signals1-failed | page | ECO2007S | Commerce Undergraduate Handbook 2026 p. 156 (complementary workbook) |  |  | no | semantics gap: No citation: check() returns a status and a reason, never a passage (ENGINE_INTERFACE.md), and its reason cites no page, and the plan set holds no reason about the course. SEMANTICS.md ties passages to plan reasons alone, so F-2's "citing the handbook" rests on them. |
| signals1-failed | deciding_codes | EEE4113F | EEE3098S |  |  | no | semantics gap: Every one is an eligible decision. SEMANTICS.md gives check and not_eligible their reason and eligible none, so check() returns an eligible decision with no reason, which names nothing that met the rule. The labels expect it to name the course that did. |
| signals1-failed | page | EEE4113F | 138 |  |  | no | semantics gap: No citation: check() returns a status and a reason, never a passage (ENGINE_INTERFACE.md), and its reason cites no page, and the plan set holds no reason about the course. SEMANTICS.md ties passages to plan reasons alone, so F-2's "citing the handbook" rests on them. |
| power-repeat-clash | deciding_codes | EEE2044S | EEE1007S |  |  | no | semantics gap: Every one is an eligible decision. SEMANTICS.md gives check and not_eligible their reason and eligible none, so check() returns an eligible decision with no reason, which names nothing that met the rule. The labels expect it to name the course that did. |
| power-repeat-clash | page | EEE2044S | 130 |  |  | no | semantics gap: No citation: check() returns a status and a reason, never a passage (ENGINE_INTERFACE.md), and its reason cites no page, and the plan set holds no reason about the course. SEMANTICS.md ties passages to plan reasons alone, so F-2's "citing the handbook" rests on them. |
| power-repeat-clash | deciding_codes | EEE3096S | EEE2046F |  |  | no | semantics gap: Every one is an eligible decision. SEMANTICS.md gives check and not_eligible their reason and eligible none, so check() returns an eligible decision with no reason, which names nothing that met the rule. The labels expect it to name the course that did. |
| power-repeat-clash | page | EEE3096S | 136 | 13 (plan reason) |  | no | semantics gap: check() returns a status and a reason, never a passage (ENGINE_INTERFACE.md), and its reason cites no page. The only plan reason about EEE3096S is FB3.4's conflict, which cites FB3.4 on p. 13, not the entry rule on p. 136. SEMANTICS.md ties passages to plan reasons alone. |
| power-repeat-clash | deciding_codes | MEC2045S | MEC2047F |  |  | no | semantics gap: Every one is an eligible decision. SEMANTICS.md gives check and not_eligible their reason and eligible none, so check() returns an eligible decision with no reason, which names nothing that met the rule. The labels expect it to name the course that did. |
| power-repeat-clash | page | MEC2045S | 148 | 13 (plan reason) |  | no | semantics gap: check() returns a status and a reason, never a passage (ENGINE_INTERFACE.md), and its reason cites no page. The only plan reason about MEC2045S is FB3.4's conflict, which cites FB3.4 on p. 13, not the entry rule on p. 148. SEMANTICS.md ties passages to plan reasons alone. |
| power-repeat-clash | page | BIO1004S | Science Handbook 2026 p. 77 (complementary workbook) |  |  | no | semantics gap: No citation: check() returns a status and a reason, never a passage (ENGINE_INTERFACE.md), and its reason cites no page, and the plan set holds no reason about the course. SEMANTICS.md ties passages to plan reasons alone, so F-2's "citing the handbook" rests on them. |
| aspect-maths-physics | deciding_codes | EEE2044S | EEE1007S |  |  | no | semantics gap: Every one is an eligible decision. SEMANTICS.md gives check and not_eligible their reason and eligible none, so check() returns an eligible decision with no reason, which names nothing that met the rule. The labels expect it to name the course that did. |
| aspect-maths-physics | page | EEE2044S | 130 |  |  | no | semantics gap: No citation: check() returns a status and a reason, never a passage (ENGINE_INTERFACE.md), and its reason cites no page, and the plan set holds no reason about the course. SEMANTICS.md ties passages to plan reasons alone, so F-2's "citing the handbook" rests on them. |
| aspect-maths-physics | deciding_codes | EEE2046F | EEE1006F |  |  | no | semantics gap: Every one is an eligible decision. SEMANTICS.md gives check and not_eligible their reason and eligible none, so check() returns an eligible decision with no reason, which names nothing that met the rule. The labels expect it to name the course that did. |
| aspect-maths-physics | page | EEE2046F | 131 |  |  | no | semantics gap: No citation: check() returns a status and a reason, never a passage (ENGINE_INTERFACE.md), and its reason cites no page, and the plan set holds no reason about the course. SEMANTICS.md ties passages to plan reasons alone, so F-2's "citing the handbook" rests on them. |
| aspect-maths-physics | deciding_codes | PHY2010S | MAM2083F |  |  | no | semantics gap: Every one is an eligible decision. SEMANTICS.md gives check and not_eligible their reason and eligible none, so check() returns an eligible decision with no reason, which names nothing that met the rule. The labels expect it to name the course that did. |
| aspect-maths-physics | page | PHY2010S | 191 |  |  | no | semantics gap: No citation: check() returns a status and a reason, never a passage (ENGINE_INTERFACE.md), and its reason cites no page, and the plan set holds no reason about the course. SEMANTICS.md ties passages to plan reasons alone, so F-2's "citing the handbook" rests on them. |
| aspect-maths-physics | page | MAM2085F | 183 |  |  | no | semantics gap: No citation: check() returns a status and a reason, never a passage (ENGINE_INTERFACE.md), and its reason cites no page, and the plan set holds no reason about the course. SEMANTICS.md ties passages to plan reasons alone, so F-2's "citing the handbook" rests on them. |
| aspect-maths-physics | deciding_codes | EEE3092F | MAM2083F |  |  | no | semantics gap: Every one is an eligible decision. SEMANTICS.md gives check and not_eligible their reason and eligible none, so check() returns an eligible decision with no reason, which names nothing that met the rule. The labels expect it to name the course that did. |
| aspect-maths-physics | page | EEE3092F | 135 |  |  | no | semantics gap: No citation: check() returns a status and a reason, never a passage (ENGINE_INTERFACE.md), and its reason cites no page, and the plan set holds no reason about the course. SEMANTICS.md ties passages to plan reasons alone, so F-2's "citing the handbook" rests on them. |
| embedded1-failed | page | EEE3092F | 135 | 13 (plan reason) |  | no | semantics gap: check() returns a status and a reason, never a passage (ENGINE_INTERFACE.md), and its reason cites no page. The only plan reason about EEE3092F is FB3.4's conflict, which cites FB3.4 on p. 13, not the entry rule on p. 135. SEMANTICS.md ties passages to plan reasons alone. |
| embedded1-failed | status | EEE2046S | eligible | not held | not held | no | known gap: EEE2046S isn't in the approved 2026 rules, as no EEE curriculum lists it and the 2026 manifest leaves it out (docs/shortfalls.md, 14 Oct), so neither check() nor the checker can judge it. Print gives eligible (p. 132). |
| embedded1-failed | deciding_codes | EEE2046S | EEE1006F |  |  | no | known gap: The same gap: with no decision there is no reason to name EEE1006F. |
| embedded1-failed | page | EEE2046S | 132 |  |  | no | known gap: The same gap: with no decision there is no page. |
| aspect-final-supp | set_reason | excluded:more electives are allowed (at least 48 credits, at least two of EEE4117F EEE4118F EEE4119F) | excluded: EEE4117F EEE4118F EEE4119F |  |  | yes | label slip, confirmed after the run: The engine's set holds the excluded reason SEMANTICS.md asks for: "Plans with more electives than the rules ask for aren't listed. The handbook allows more, so ask your advisor if you want to add one." The label's subject names EEE4117F, EEE4118F and EEE4119F in brackets, describing the rule, which SEMANTICS.md doesn't ask the reason to name. Confirmed: SEMANTICS.md asks the reason only to say more are allowed, so the codes in brackets were a gloss. |
| aspect-final-supp | deciding_codes | EEE4114F | EEE3092F |  |  | no | semantics gap: Every one is an eligible decision. SEMANTICS.md gives check and not_eligible their reason and eligible none, so check() returns an eligible decision with no reason, which names nothing that met the rule. The labels expect it to name the course that did. |
| aspect-final-supp | page | EEE4114F | 139 |  |  | no | semantics gap: No citation: check() returns a status and a reason, never a passage (ENGINE_INTERFACE.md), and its reason cites no page, and the plan set holds no reason about the course. SEMANTICS.md ties passages to plan reasons alone, so F-2's "citing the handbook" rests on them. |
| aspect-final-supp | page | HUB4049F | 162 |  |  | yes | semantics gap: No citation: check() returns a status and a reason, never a passage (ENGINE_INTERFACE.md), and its reason cites no page, and the plan set holds no reason about the course. SEMANTICS.md ties passages to plan reasons alone, so F-2's "citing the handbook" rests on them. |
| aspect-final-supp | page | EEE3094S | 135 | 15 (plan reason) |  | no | label slip, confirmed after the run: The label's deciding rule is the supplementary still to come under FB7.1, on p. 15, which the engine's FB7 reason cites. Its page column gives 135, EEE3094S's own entry. Confirmed: the deciding rule names FB7.1 on p. 15, so 15 is right. |
| owes-asl-dp-refused | page | CSC2001F | 170 | 169 (plan reason) |  | no | semantics gap: The engine's reason cites CSC2001F's own entry, as SEMANTICS.md asks, and the stored passage carries the page the entry starts on, 169. The requirement prints at the top of p. 170 (labels/REVIEW.md). SEMANTICS.md doesn't say which page a reason cites when its entry crosses a page break. |
| owes-asl-dp-refused | deciding_codes | CSC1016S | CSC1015F |  |  | no | semantics gap: Every one is an eligible decision. SEMANTICS.md gives check and not_eligible their reason and eligible none, so check() returns an eligible decision with no reason, which names nothing that met the rule. The labels expect it to name the course that did. |
| owes-asl-dp-refused | page | CSC1016S | 168 |  |  | no | semantics gap: No citation: check() returns a status and a reason, never a passage (ENGINE_INTERFACE.md), and its reason cites no page, and the plan set holds no reason about the course. SEMANTICS.md ties passages to plan reasons alone, so F-2's "citing the handbook" rests on them. |
| owes-asl-dp-refused | deciding_codes | EEE3097S | EEE3088F |  |  | no | semantics gap: Every one is an eligible decision. SEMANTICS.md gives check and not_eligible their reason and eligible none, so check() returns an eligible decision with no reason, which names nothing that met the rule. The labels expect it to name the course that did. |
| owes-asl-dp-refused | page | EEE3097S | 137 |  |  | no | semantics gap: No citation: check() returns a status and a reason, never a passage (ENGINE_INTERFACE.md), and its reason cites no page, and the plan set holds no reason about the course. SEMANTICS.md ties passages to plan reasons alone, so F-2's "citing the handbook" rests on them. |
| owes-asl-dp-refused | deciding_codes | EEE3089F | PHY2010S MAM2083F |  |  | no | semantics gap: Every one is an eligible decision. SEMANTICS.md gives check and not_eligible their reason and eligible none, so check() returns an eligible decision with no reason, which names nothing that met the rule. The labels expect it to name the course that did. |
| owes-asl-dp-refused | page | EEE3089F | 133 |  |  | no | semantics gap: No citation: check() returns a status and a reason, never a passage (ENGINE_INTERFACE.md), and its reason cites no page, and the plan set holds no reason about the course. SEMANTICS.md ties passages to plan reasons alone, so F-2's "citing the handbook" rests on them. |
| owes-asl-dp-refused | page | CSC2002S | 170 |  |  | no | semantics gap: No citation: check() returns a status and a reason, never a passage (ENGINE_INTERFACE.md), and its reason cites no page, and the plan set holds no reason about the course. SEMANTICS.md ties passages to plan reasons alone, so F-2's "citing the handbook" rests on them. |

## By kind of record and curriculum

Base records are on track, every earlier course passed. Each failure record fails one previous-year core course (F, 40), or first-year maths and physics together; supplementary records defer one (FS, 46); arrears records fail it and pass two of her own year's courses, so FB5 puts her in her year owing it.

| Set | Kind | Curriculum | Records | Plan sets right | Missing | Extra | Twice | Statuses right | Slots right |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Held out | labelled | EB009EEE01 | 1 | 1 of 1, 100.0% (20.7% to 100.0%) | 0 | 0 | 0 | 118 of 118, 100.0% (96.8% to 100.0%) | 1 of 1, 100.0% (20.7% to 100.0%) |
| Held out | labelled | EB011EEE05 | 1 | 1 of 1, 100.0% (20.7% to 100.0%) | 0 | 0 | 0 | 117 of 117, 100.0% (96.8% to 100.0%) | 1 of 1, 100.0% (20.7% to 100.0%) |
| Held out | labelled | EB022EEE02 | 1 | 1 of 1, 100.0% (20.7% to 100.0%) | 0 | 0 | 0 | 117 of 117, 100.0% (96.8% to 100.0%) | 3 of 3, 100.0% (43.9% to 100.0%) |
| Held out | labelled | EB809EEE01 | 1 | 1 of 1, 100.0% (20.7% to 100.0%) | 0 | 0 | 0 | 9 of 9, 100.0% (70.1% to 100.0%) | 1 of 1, 100.0% (20.7% to 100.0%) |
| Held out | labelled | EB811EEE05 | 1 | 1 of 1, 100.0% (20.7% to 100.0%) | 0 | 0 | 0 | 12 of 12, 100.0% (75.8% to 100.0%) | none to count |
| Held out | labelled | EB822EEE02 | 1 | 1 of 1, 100.0% (20.7% to 100.0%) | 0 | 0 | 0 | 116 of 116, 100.0% (96.8% to 100.0%) | 1 of 1, 100.0% (20.7% to 100.0%) |
| Failure sweep | arrears | EB009EEE01 | 28 | 28 of 28, 100.0% (87.9% to 100.0%) | 0 | 0 | 0 | 1349 of 1349, 100.0% (99.7% to 100.0%) | 10 of 10, 100.0% (72.2% to 100.0%) |
| Failure sweep | arrears | EB011EEE05 | 30 | 30 of 30, 100.0% (88.6% to 100.0%) | 0 | 0 | 0 | 1581 of 1581, 100.0% (99.8% to 100.0%) | 13 of 13, 100.0% (77.2% to 100.0%) |
| Failure sweep | arrears | EB022EEE02 | 26 | 26 of 26, 100.0% (87.1% to 100.0%) | 0 | 0 | 0 | 1351 of 1351, 100.0% (99.7% to 100.0%) | 20 of 20, 100.0% (83.9% to 100.0%) |
| Failure sweep | arrears | EB809EEE01 | 30 | 30 of 30, 100.0% (88.6% to 100.0%) | 0 | 0 | 0 | 1104 of 1104, 100.0% (99.7% to 100.0%) | 18 of 18, 100.0% (82.4% to 100.0%) |
| Failure sweep | arrears | EB811EEE05 | 29 | 29 of 29, 100.0% (88.3% to 100.0%) | 0 | 0 | 0 | 1093 of 1093, 100.0% (99.6% to 100.0%) | 18 of 18, 100.0% (82.4% to 100.0%) |
| Failure sweep | arrears | EB822EEE02 | 28 | 28 of 28, 100.0% (87.9% to 100.0%) | 0 | 0 | 0 | 1105 of 1105, 100.0% (99.7% to 100.0%) | 20 of 20, 100.0% (83.9% to 100.0%) |
| Failure sweep | fail | EB009EEE01 | 28 | 28 of 28, 100.0% (87.9% to 100.0%) | 0 | 0 | 0 | 1225 of 1225, 100.0% (99.7% to 100.0%) | none to count |
| Failure sweep | fail | EB011EEE05 | 30 | 30 of 30, 100.0% (88.6% to 100.0%) | 0 | 0 | 0 | 1457 of 1457, 100.0% (99.7% to 100.0%) | 4 of 4, 100.0% (51.0% to 100.0%) |
| Failure sweep | fail | EB022EEE02 | 26 | 26 of 26, 100.0% (87.1% to 100.0%) | 0 | 0 | 0 | 1000 of 1000, 100.0% (99.6% to 100.0%) | none to count |
| Failure sweep | fail | EB809EEE01 | 30 | 30 of 30, 100.0% (88.6% to 100.0%) | 0 | 0 | 0 | 1183 of 1183, 100.0% (99.7% to 100.0%) | 4 of 4, 100.0% (51.0% to 100.0%) |
| Failure sweep | fail | EB811EEE05 | 29 | 29 of 29, 100.0% (88.3% to 100.0%) | 0 | 0 | 0 | 1060 of 1060, 100.0% (99.6% to 100.0%) | 4 of 4, 100.0% (51.0% to 100.0%) |
| Failure sweep | fail | EB822EEE02 | 28 | 28 of 28, 100.0% (87.9% to 100.0%) | 0 | 0 | 0 | 964 of 964, 100.0% (99.6% to 100.0%) | 6 of 6, 100.0% (61.0% to 100.0%) |
| Failure sweep | supplementary | EB009EEE01 | 27 | 27 of 27, 100.0% (87.5% to 100.0%) | 0 | 0 | 0 | 1339 of 1339, 100.0% (99.7% to 100.0%) | 10 of 10, 100.0% (72.2% to 100.0%) |
| Failure sweep | supplementary | EB011EEE05 | 29 | 29 of 29, 100.0% (88.3% to 100.0%) | 0 | 0 | 0 | 1571 of 1571, 100.0% (99.8% to 100.0%) | 12 of 12, 100.0% (75.8% to 100.0%) |
| Failure sweep | supplementary | EB022EEE02 | 25 | 25 of 25, 100.0% (86.7% to 100.0%) | 0 | 0 | 0 | 1341 of 1341, 100.0% (99.7% to 100.0%) | 30 of 30, 100.0% (88.6% to 100.0%) |
| Failure sweep | supplementary | EB809EEE01 | 30 | 30 of 30, 100.0% (88.6% to 100.0%) | 0 | 0 | 0 | 1104 of 1104, 100.0% (99.7% to 100.0%) | 16 of 16, 100.0% (80.6% to 100.0%) |
| Failure sweep | supplementary | EB811EEE05 | 29 | 29 of 29, 100.0% (88.3% to 100.0%) | 0 | 0 | 0 | 1093 of 1093, 100.0% (99.6% to 100.0%) | 16 of 16, 100.0% (80.6% to 100.0%) |
| Failure sweep | supplementary | EB822EEE02 | 28 | 28 of 28, 100.0% (87.9% to 100.0%) | 0 | 0 | 0 | 1105 of 1105, 100.0% (99.7% to 100.0%) | 16 of 16, 100.0% (80.6% to 100.0%) |
| In-sample base | base | EB009EEE01 | 3 | 3 of 3, 100.0% (43.9% to 100.0%) | 0 | 0 | 0 | 137 of 137, 100.0% (97.3% to 100.0%) | 1 of 1, 100.0% (20.7% to 100.0%) |
| In-sample base | base | EB011EEE05 | 3 | 3 of 3, 100.0% (43.9% to 100.0%) | 0 | 0 | 0 | 137 of 137, 100.0% (97.3% to 100.0%) | 1 of 1, 100.0% (20.7% to 100.0%) |
| In-sample base | base | EB022EEE02 | 3 | 3 of 3, 100.0% (43.9% to 100.0%) | 0 | 0 | 0 | 140 of 140, 100.0% (97.3% to 100.0%) | 3 of 3, 100.0% (43.9% to 100.0%) |
| In-sample base | base | EB809EEE01 | 4 | 4 of 4, 100.0% (51.0% to 100.0%) | 0 | 0 | 0 | 140 of 140, 100.0% (97.3% to 100.0%) | 2 of 2, 100.0% (34.2% to 100.0%) |
| In-sample base | base | EB811EEE05 | 4 | 4 of 4, 100.0% (51.0% to 100.0%) | 0 | 0 | 0 | 140 of 140, 100.0% (97.3% to 100.0%) | 2 of 2, 100.0% (34.2% to 100.0%) |
| In-sample base | base | EB822EEE02 | 4 | 4 of 4, 100.0% (51.0% to 100.0%) | 0 | 0 | 0 | 143 of 143, 100.0% (97.4% to 100.0%) | 2 of 2, 100.0% (34.2% to 100.0%) |

## Metamorphic relations

Reordered history: her lines shuffled give the same plan sets and statuses. Section removed: one alternative of one plan course's choice group taken away never adds a plan; it applies where the checker's FB3.4 drops don't change. Pass added: a pass in a course of her year's groups she hasn't passed, complementary courses aside, never turns another course from eligible to not_eligible, that course and those its pass covers aside.

| Relation | Set | Instances | Applies | Broken |
| --- | --- | --- | --- | --- |
| reordered history | Failure sweep | 510 | 510 | 0 of 510 (95% upper bound 0.6%) |
| reordered history | In-sample base | 21 | 21 | 0 of 21 (95% upper bound 13.3%) |
| section removed | Failure sweep | 510 | 77 | 0 of 77 (95% upper bound 3.8%) |
| section removed | In-sample base | 21 | 4 | 0 of 4 (95% upper bound 52.7%) |
| pass added | Failure sweep | 3170 | 3170 | 0 of 3170 (95% upper bound 0.1%) |
| pass added | In-sample base | 201 | 201 | 0 of 201 (95% upper bound 1.5%) |

## Times

Each record's plans were generated five times in one process, one record at a time, and its statuses checked once. Generate's times are over every run. The checker's are one run per record.

| Set | Records | Generate p50 | p95 | Largest | Runs over 10 s | Check p50 | p95 | Checker p50 | p95 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Held out | 6 | 0.145 s | 0.677 s | 0.962 s | 0 of 30 (95% upper bound 9.5%) | 0.004 s | 0.006 s | 0.010 s | 0.027 s |
| Failure sweep | 510 | 0.030 s | 0.243 s | 0.755 s | 0 of 2550 (95% upper bound 0.1%) | 0.002 s | 0.006 s | 0.006 s | 0.026 s |
| In-sample base | 21 | 0.078 s | 0.306 s | 0.429 s | 0 of 105 (95% upper bound 2.8%) | 0.002 s | 0.007 s | 0.011 s | 0.039 s |

## What failing a course costs

FB5 held back 163 of 171, 95.3% (91.0% to 97.6%) of the records that fail one course and pass nothing of her own year: each is in the previous year again, and her plans are the repeat alone. The arrears variants are the thesis's figure: the same failure, with two of her own year's courses passed, so she's in her year owing it. The ten that cost the most plans, with every record tied with the tenth (19 in all), from failure_cost.csv:

| Curriculum | Year | Course failed | Plans left | On track | Core excluded | FB3.4 drops | Checker agrees |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EB009EEE01 | 4 | EEE3090F | 1 | 19 | 0 | EEE4113F | yes |
| EB809EEE01 | 5 | EEE3091F | 4 | 19 | 0 |  | yes |
| EB009EEE01 | 4 | EEE3091F | 4 | 19 | 0 |  | yes |
| EB809EEE01 | 5 | EEE3093S | 5 | 19 | 0 | EEE4125C | yes |
| EB009EEE01 | 4 | EEE3093S | 5 | 19 | 0 | EEE4125C | yes |
| EB809EEE01 | 5 | EEE3098S | 6 | 19 | 2 EEE4113F EEE4125C |  | yes |
| EB009EEE01 | 4 | EEE3098S | 6 | 19 | 2 EEE4113F EEE4125C |  | yes |
| EB811EEE05 | 5 | MEC2047F | 0 | 10 | 0 |  | yes |
| EB811EEE05 | 5 | EEE3091F | 0 | 10 | 0 |  | yes |
| EB809EEE01 | 5 | EEE3100S | 9 | 19 | 0 |  | yes |
| EB809EEE01 | 5 | EEE3088F | 9 | 19 | 0 |  | yes |
| EB022EEE02 | 4 | EEE3090F | 0 | 10 | 0 |  | yes |
| EB011EEE05 | 4 | MEC2047F | 0 | 10 | 0 |  | yes |
| EB011EEE05 | 4 | EEE3094S | 0 | 10 | 0 |  | yes |
| EB011EEE05 | 4 | EEE3091F | 0 | 10 | 0 |  | yes |
| EB011EEE05 | 4 | EEE3090F | 0 | 10 | 0 | EEE4113F | yes |
| EB009EEE01 | 4 | EEE3100S | 9 | 19 | 0 |  | yes |
| EB009EEE01 | 4 | EEE3094S | 9 | 19 | 0 |  | yes |
| EB009EEE01 | 4 | EEE3088F | 9 | 19 | 0 |  | yes |

Every failure record that leaves her no plan at all: 11, of which 11 carry a set-level conflict reason saying why:

| Variant | Curriculum | Year | Course failed | Plans left | On track | Core excluded | FB3.4 drops | Checker agrees |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arrears | EB011EEE05 | 3 | PHY2010S | 0 | 1 | 0 |  | yes |
| arrears | EB011EEE05 | 4 | EEE3090F | 0 | 10 | 0 | EEE4113F | yes |
| arrears | EB011EEE05 | 4 | EEE3091F | 0 | 10 | 0 |  | yes |
| arrears | EB011EEE05 | 4 | EEE3094S | 0 | 10 | 0 |  | yes |
| arrears | EB011EEE05 | 4 | MEC2047F | 0 | 10 | 0 |  | yes |
| arrears | EB022EEE02 | 3 | MAM2084S | 0 | 3 | 0 |  | yes |
| arrears | EB022EEE02 | 3 | PHY2010S | 0 | 3 | 1 EEE3089F |  | yes |
| arrears | EB022EEE02 | 4 | EEE3090F | 0 | 10 | 0 |  | yes |
| arrears | EB811EEE05 | 5 | EEE3091F | 0 | 10 | 0 |  | yes |
| arrears | EB811EEE05 | 5 | MEC2047F | 0 | 10 | 0 |  | yes |
| arrears | EB822EEE02 | 4 | PHY2010S | 0 | 3 | 1 EEE3089F |  | yes |

## Disagreements

Plan sets that differ, as each plan's codes:

None.

Slots that differ and plans resting on judgement without a conditional reason:

None.

Statuses that differ, by course, with how many records and the first:

None.

Metamorphic relations broken:

None.

## Inputs

The SHA-256 of every file the run read.

| File | SHA-256 |
| --- | --- |
| `data/rules/2026/rulebook.json` | `0b0c2a40e1c1599a644be58097714cc0f875098026b0ffec87900e40d033191d` |
| `backend/tests/fixtures/result_symbols.json` | `383382cc3fcb7bf60c71bf172aa8e5dcc4d0701631ce0281b9769bbe01b2617d` |
| `tests/acceptance/atp2/labels/records.csv` | `9b80ae6c560014a2bee603325743ad29133650ccd8d245de50258a714abcf776` |
| `tests/acceptance/atp2/labels/decisions.csv` | `c6260a13e9dfcd4c079549dd6a46d8555f3322580e69c4800eb74ad9a0bd3263` |
| `tests/acceptance/atp2/labels/records/signals1-failed.json` | `8952e577812f3f94dc652e0c19fbd3bb740b9bd11b38805e2cee098f8777824b` |
| `tests/acceptance/atp2/labels/records/power-repeat-clash.json` | `ecfdc9ef75259f0e95e3449e611593792c1de9c04f63cdf72d88342d5dd8bbe3` |
| `tests/acceptance/atp2/labels/records/aspect-maths-physics.json` | `58843f79e2423fddcf498c6710452a663bce68a8b82a9a3f3d2f8059852ff730` |
| `tests/acceptance/atp2/labels/records/embedded1-failed.json` | `5fa6dc0abb358189256ab108c93f23cf45da385b99907f88a8a7f0e3f1bd5b2e` |
| `tests/acceptance/atp2/labels/records/aspect-final-supp.json` | `cc3b0c973e153ba23267c5e1bb18152e321e89bf521bb670ffe6af5574bad24b` |
| `tests/acceptance/atp2/labels/records/owes-asl-dp-refused.json` | `93dc4f57c9377a973d6664668bc8bb34dc60fa7e0b0d913ad43a8907afc99448` |
