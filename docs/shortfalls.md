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
| 11 Oct | Six of the 24 planted faults survived the tests | Missing boundaries, a seed with no curriculum-only meetings, and a stand-in that returns identical plans | A test for each rule, on rows built for it: 24 of 24 caught | None |
| 12 Oct | Mutation testing found rules no test checked, though the code was right: a record with no student number or page numbers, a printed Term GPA of 0.00, and which meetings count towards the week options | The seed has no such records, alternatives or curriculum-only meetings | A test for each | None |

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
| 12 Oct | 93% line coverage, but only 75% of the planted faults caught | Coverage counts lines run, not checks made | `make mutation` and `make planted-faults` measure the faults caught, and `docs/testing.md` reports them next to coverage | Report all three in 5.2 |
| 12 Oct | mutmut 3.8 can't be installed on my laptop | It needs libcst 1.9, which has no Intel Mac wheel for Python 3.12 | Pinned mutmut 3.7.0, with libcst below 1.9 | Lift the pin once the wheel exists, then measure again, as another version plants different mutants |
| 12 Oct | Under mutmut, every test failed to find Mbali's seed file | mutmut runs a copy of the code from `backend/mutants/`, one folder deeper, and `SEED_FILE` is found four folders up from `seed.py` | `make mutation` links `backend/data` to `data/` while it runs | None, while `SEED_FILE` depends on depth |
| 12 Oct | The mutation score covers the unit tests only | The integration tests need Docker and a rebuilt database, far too slow to run once per mutant | Each integration test cut is argued on its own | Limitation: the score says nothing about the Supabase adapters or the SQL |
| 12 Oct | mutmut leaves code outside functions alone | mutmut 3 mutates function bodies only | None | Limitation: the transcript reader's patterns and constants such as the lunch hour aren't mutated |
| 12 Oct | The guard sweep can't read the app's route table | FastAPI 0.142 wraps each included router, so `app.routes` lists no operations | The sweep lists them from the app's OpenAPI schema | A route left out of the schema would escape the sweep |
| 12 Oct | `make check-db` once failed waiting for the local storage container | It took about 50 seconds to restart after the reset, longer than the Supabase CLI waits | Ran it again, and it passed | If it recurs, skip storage with `SUPABASE_START_FLAGS`, as CI does |

## Mutants the unit tests don't catch

On 12 Oct, after the test-strength work, 157 of 1,699 mutants survived `make mutation`. 79 of them only change wording a student or developer reads (a prompt, a label, a refusal's detail, a log line) or the text inside a made-up id or cache key, which no test should pin. 16 are equivalent: no realistic input tells them apart from the code, such as reading the seed file with the platform's default encoding. Every survivor in the code the thesis's claims rest on (the transcript reader's statuses, the averages, questionnaire narrowing and student isolation) was closed with a test. The other 62:

| Where | What no unit test checks | Mutants |
| --- | --- | --- |
| Seed loader | A seed file that leaves out a table or a key | 24 |
| Seed loader | A table it doesn't know | 2 |
| Seed loader | Message citations, as the seed has none | 2 |
| Seed loader | Rows given the same id, which only the database's keys refuse | 2 |
| Seed read-back | Key order in stored JSON, which only the database changes | 3 |
| Seed read-back | A stored row that differs from the file | 4 |
| Questionnaire | Hearted courses listed first among the course options | 3 |
| Plans | The order of a course's meetings: unknown days and times last, alternatives in order | 5 |
| Plan view | Her curriculum deciding which meetings a plan shows | 1 |
| Plan view | A reason's course code, and the handbook passage it cites | 6 |
| Onboarding | Which curricula a transcript's programme matches, and their order | 4 |
| Problems | The dotted path of a nested invalid field | 1 |
| Accounts | An address with two @ signs | 1 |
| Rulebook cache | A second year in the cache, and a test clock that doesn't start at zero | 2 |
| Eligibility stand-in | A credited result counting as passed | 2 |
