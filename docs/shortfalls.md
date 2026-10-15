<!-- Every known gap, workaround and limitation, logged as it's found, for the thesis's evaluation -->
# Shortfalls

What SAGE can't do yet, the defects caught before acceptance testing, and the limitations that last. Entries are added as they're found. All dates are in 2026.

## Open: must close before the build freezes

| Found | What happened | Cause | What was done | Limitation or future work |
| --- | --- | --- | --- | --- |
| 11 Oct | Every student gets Mbali's 10 plans | The engine isn't built | `SeededPlanGenerator` stands in for it | The engine replaces it before ATP-2 |
| 11 Oct | 21 of 41 electives say "check with your advisor" | `InterimEligibility` can't evaluate entry rules | The stand-in refers them to an advisor | The engine replaces it |
| 11 Oct | Every question gets a fixed referral reply | The advisor isn't built | `FixedAdvisor` stands in, with no retrieval or citations, and `passages` is empty | The advisor replaces it before ATP-3 |
| 11 Oct | The rulebook comes only from the seed, with one curriculum (Mechatronics) and 52 courses | Handbook ingestion isn't built: the 2023 and 2026 sources are in `data/sources/`, but nothing reads them yet | None yet | Needed for ATP-1, and for S1 to S4 in three programmes |
| 11 Oct | No delta review rows | Handbook ingestion isn't built | None yet | Needed for ATP-1's 2023 to 2026 check |
| 11 Oct | No frontend tests | No test script, and the M3 screens aren't built yet | 14 Oct: Vitest runs tests of the tokens' contrast, the saved appearance, the lint guards and the logo's title ids. The other components and the screens have none | Each M3 screen branch adds its own, and app foundations adds Playwright with axe. Needed for ATP-4 |
| 11 Oct | No ATP harness or load scripts | `tests/` holds only a README | None yet | Build before 14 Oct |
| 11 Oct | The design experiments aren't in the repo | `experiments/` holds only a README | None yet | Add them, or say where they live |
| 12 Oct | ATP-5's load test can't sign its test accounts in on the hosted project | The hosted Email provider is off, the backend counts only Microsoft sign-ins there, and Microsoft's sign-in page can't be automated | `ACCEPT_EMAIL_SIGN_IN` lets the backend count email-provider accounts during a test window | Follow the ATP-5 checklist below, then switch everything back |
| 12 Oct | The privacy page and the privacy note don't say where chat questions go | The advisor is a stand-in, `FixedAdvisor`, which sends nothing anywhere | None yet | When the real advisor replaces it, update `frontend/public/privacy.html` and the privacy note in `docs/architecture.md` to say that chat questions, and the evidence sent with them, go to the chosen model provider, and where it processes them |
| 13 Oct | A mark leaf has no rule yet for a pending supplementary exam | A supplementary can change the final mark a mark leaf tests, as in CSC2002S's "At least 45% for CSC2001F" | None yet | The engine milestone decides how a pending supplementary meets a mark leaf |
| 14 Oct | The starter page fails the new frontend guards | `App.tsx` has a nested ternary and a `role="status"` that should be `output`, and it default-exports because `main.tsx` imports it that way. `global.css` has raw colours | `.oxlintrc.json` and `stylelint.config.js` exempt those two files from only those rules, each with a comment | The shell branch replaces the starter page and removes the exemptions |
| 14 Oct | The old leaf, `frontend/public/sage-symbol.svg`, is still in the app | The starter page in `App.tsx` shows it. The favicon and the logo set are the new SVGs | Kept, so the starter page still works | The shell branch deletes it with the starter page |

**ATP-5 test window checklist.** Before the load test:

1. In the Supabase dashboard (Authentication → Sign In / Providers), turn off **Allow new users to sign up**, then turn on the **Email** provider. Closing sign-ups also stops new students joining through Microsoft until step 6.
2. Make the test accounts with the admin API and the secret key, never through sign-up.
3. Switch the setting on: `az containerapp update --resource-group rg-sage --name ca-sage-api --set-env-vars ACCEPT_EMAIL_SIGN_IN=true`. The backend's log then shows a warning at every start.

After the load test:

4. Switch the setting off: `az containerapp update --resource-group rg-sage --name ca-sage-api --remove-env-vars ACCEPT_EMAIL_SIGN_IN`. Deploys never touch it, so it stays on until removed.
5. Delete the test accounts, then turn the **Email** provider off.
6. Turn **Allow new users to sign up** back on.

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
| 12 Oct | Supabase Auth held my name for my hosted account, in `full_name` and `preferred_username` | My first hosted sign-in, on 3 Oct, came before the frontend and asked Microsoft for more than the email, and Supabase Auth keeps metadata keys that later sign-ins don't send | Removed both keys on 12 Oct. A fresh hosted sign-in stored no name, as SAGE asks Microsoft only for the email and `User.Read` | None |

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
| 12 Oct | Clones still download the old brand files | Git keeps every committed version, and the 3.9 MB banner GIF and the logo sources were committed before they were replaced or moved out | The banner is a 418 KB WebP now, and the sources sit outside the repo | Only rewriting history would shrink clones, which isn't worth the risk |
| 12 Oct | 157 of 1,699 mutants survive the unit tests | 79 only change wording or a made-up id, 16 are equivalent, and 62 are gaps outside the code the thesis's claims rest on | Every survivor in that code was closed with a test | The 62 are future work, named in `docs/testing.md` |
| 12 Oct | Automated checks can't sign in through Microsoft | Microsoft's sign-in page can't be automated, and the frontend's PKCE sign-in refuses the magic link Supabase's admin API makes | `make sign-in` prints a one-time link for Mbali's made-up account, whose token the frontend swaps for a session on local Supabase | Limitation: automated checks never go through Microsoft, so that path is checked by hand |
| 12 Oct | Microsoft's consent screen shows SAGE as "unverified" | Only Microsoft publisher verification removes the label, and SAGE's app registration isn't verified | Explained in the user-study briefing | Limitation, for the user study |
| 13 Oct | During CP0, Claude Code read about ten DP lines from APG, CHE, CIV and MEC entries in the 2023 and 2026 handbooks | It searched both handbooks whole for DP and co-requisite wording, before the held-out departments were chosen | No rule, leaf or grammar change followed. The leaf set comes from the EEE entries alone, and DP stays out of it | A held-out department among these is reported in ATP-1 with this note |
| 13 Oct | Only the 2023 and 2026 handbooks are ingested; the 2024 and 2025 ones are left out | 2023 and 2026 sit either side of the 2025 curriculum change, so comparing them is the hardest test of change control, and I started in 2023. Planning needs only the current year: the 2026 handbook prints the rules for students who registered before 2025, such as the 576-credit curriculum and FB8.10's separate thresholds, and transcripts carry the earlier years. Each extra year adds a review sitting | None | 2026 is compared with 2023, a three-year jump, so a yearly review would see fewer changes than ATP-1 measures. Adding 2024 and 2025 later needs no code change |
| 13 Oct | While preparing the 2026 manifest, Claude Code printed the top of printed page 126, which ends the Construction Economics entries: CON3053S and CON3054S, with their outlines and CON3054S's requirement line (CON3053S prints none) | The Electrical Engineering department section starts partway down that page, and the page was printed from its top | No rule, leaf or grammar change followed. Comma lists were already read from EEE3089F's and EEE3092F's requirements. Three Construction Economics courses leave ATP-1's held-out set: CON3053S and CON3054S, seen here, and CON2026S, whose entry C1 reads because the EEE curricula name it | ATP-1 reports Construction Economics without those three courses |
| 14 Oct | `npm audit` reports 8 high advisories after adding stylelint | stylelint 17.16's glob packages (`braces`, `micromatch`, `fast-glob`, `globby`) have a denial-of-service advisory on deeply nested patterns | None. They are dev-only, and stylelint reads only the repo's own CSS | Limitation: lift it when stylelint updates those packages |
| 14 Oct | `typescript/no-unnecessary-condition`, which catches needless `?.` and `??`, is experimental in oxlint | oxlint files it under "nursery" | It is switched on, and `make check` fails if it fires | Limitation: it may miss cases or change between releases |
| 14 Oct | The toasts use React Aria's `UNSTABLE_` API | React Aria Components 1.22.1 still marks its toast parts unstable, and only those. A toast is `role="alertdialog"` and has no enter or exit animation | `src/lib/toastQueue.ts` and `ToastRegion.tsx` are the only files that name it, so a rename touches two files | Limitation: a React Aria update may rename or change it |
| 14 Oct | The selected segment, select option and nav item differ from their surroundings by only 1.18:1 | The parity file shows the selected state as a fill (`#FFFFFF` on `#ECECEE`) with no border or shadow, and keeps it | The state also shows through weight (600 against 500), text colour, and what screen readers announce (`aria-checked`, `aria-selected`, `aria-current`) | Limitation: whether WCAG 1.4.11 needs more than a fill here is a judgement call, left for the thesis to discuss |
