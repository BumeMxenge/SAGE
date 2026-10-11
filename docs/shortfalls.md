<!-- Every known gap, workaround and limitation, logged as it's found, for the thesis's evaluation -->
# Shortfalls

What SAGE can't do yet, the defects caught before acceptance testing, and the limitations that last. Entries are added as they're found. All dates are in 2026.

## Open: must close before the build freezes

| Found | What happened | Cause | What was done | Limitation or future work |
| --- | --- | --- | --- | --- |
| 11 Oct | Every student gets Mbali's 10 plans | The engine isn't built | `SeededPlanGenerator` stands in for it | The engine replaces it before ATP-2 |
| 11 Oct | 21 of 41 electives say "check with your advisor" | `InterimEligibility` can't evaluate entry rules | The stand-in refers them to an advisor | The engine replaces it |
| 11 Oct | Every question gets a fixed referral reply | The advisor isn't built | `FixedAdvisor` stands in, with no retrieval or citations, and `passages` is empty | The advisor replaces it before ATP-3 |
| 11 Oct | The rulebook comes only from the seed, with one curriculum (Mechatronics) and 52 courses | Handbook ingestion isn't built, and `data/rules/2026` and `data/sources/2026` are empty | None yet | Needed for ATP-1, and for S1 to S4 in three programmes |
| 11 Oct | No delta review rows | Handbook ingestion isn't built | None yet | Needed for ATP-1's 2023 to 2026 check |
| 11 Oct | Six of the 24 planted faults survive the tests | Missing boundaries, a seed with no curriculum-only meetings, and a stand-in that returns identical plans | None yet | The test-strength branch |
| 11 Oct | No frontend tests | No test script, and the M3 screens aren't built yet | None yet | Needed for ATP-4 |
| 11 Oct | No ATP harness or load scripts | `tests/` holds only a README | None yet | Build before 14 Oct |
| 11 Oct | The design experiments aren't in the repo | `experiments/` holds only a README | None yet | Add them, or say where they live |

## Found and fixed during development

Defects caught before acceptance testing, for Section 5.2.

| Found | What happened | Cause | What was done | Limitation or future work |
| --- | --- | --- | --- | --- |
| 11 Oct | A questionnaire retry after a failed save showed only the plans both answers kept, and every later answer got 409 | `hide_plans` only ever hid plans, so the failed attempt's hiding stayed | `hide_plans` now sets every plan in the set, shown or hidden (36578eb) | None |
| 11 Oct | A forged token naming the project's key raised `InvalidKeyError`, a 500 | PyJWT raises its own error when an RS256 check meets the project's elliptic-curve key | Caught as `not_signed_in` (36578eb) | None |
| 11 Oct | A token that isn't ASCII raised a bare `ValueError`, a 500 | The claims were read before the token's characters were checked | Refused before the claims are read (36578eb) | None |
| 11 Oct | Credits above 32,767 failed the insert after Finish setup had started writing | `course_history.credits` is a smallint, and the request accepted any number | Capped, and refused with a 422 before any write (36578eb) | None |
| 11 Oct | A body that isn't UTF-8 raised a `KeyError` | FastAPI's own 400 had no problem code to map to | Mapped to `invalid_request` (36578eb) | None |
| 11 Oct | A PDF with `/Rotate /X` raised a `TypeError`, a 500 | Only a list of pdfplumber's errors counted as unreadable, and pdfminer fails on malformed files in many other ways | Any PDF library failure now counts as unreadable (cf57593) | None |
| 11 Oct | An impossible issue date such as 31/02/2026 crashed the reader | Building the date raised a `ValueError` that nothing caught | Read as an empty `issued_on` (36578eb) | None |
| 11 Oct | A record with no "Beginning of Undergraduate Record" line read as having no courses, so it showed the first-year message | The reader decided "no course history" from that line | `transcript_unreadable` instead, with "no course history" decided by the rows (c224040, cf57593) | None |

## Lasting: for the thesis

| Found | What happened | Cause | What was done | Limitation or future work |
| --- | --- | --- | --- | --- |
| Oct | Transcript reading is tested on a typed fixture and generated PDFs, not on real PDF quirks | No real transcripts may be stored (POPIA) | The fixture copies the real layout | Limitation. My own transcript counts only as development evidence |
| Oct | The first real transcript test read 39 of 44 rows | Current-year rows have no mark or NQF level | Fixed with the in-progress status | A development finding |
| 11 Oct | One unreadable row rejects the whole transcript | A strict reader, to avoid silent errors | The student falls back to manual entry | Limitation |
| Oct | Only 37 of 66 complementary offerings have machine-readable times | Handbooks print periods, days or "by arrangement" | Plans stay conditional, with "ask your advisor" | Limitation |
| 11 Oct | Meetings with no printed day or time don't count towards the week options | Unknown times can't be placed | They count towards neither option | Limitation |
| Sep | Literal 2026 rules shut ASPECT students out of some courses | The rules name only mainstream codes | None yet | An equivalence table, which needs administrator approval |
| Sep | The grammar accepted 56% of other departments' strings | Prose conditions and mixed and/or | None yet | More review per new department. Future work is model drafting |
| Oct | No administrator screens or ACA09 export | Time | Delta review runs in the terminal | Future work |
| Oct | The database is in the EU and the backend in South Africa | Supabase has no African region | None | Latency on every request, measured in ATP-5 |
| Oct | All test students are synthetic | POPIA and ethics scope | None | Limitation of the evaluation |
| 12 Oct | 93% line coverage, but only 75% of the planted faults caught | Coverage counts lines run, not checks made | Both reported in 5.2 | None |
