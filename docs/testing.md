<!-- How SAGE is tested: the rules every test follows, the levels, how to run them, how strong the backend's tests are, and the frontend's tests -->
# Testing

A test is worth keeping if it catches a fault. So the backend's suite is kept small, and its strength is measured by the faults it catches, not by how many tests pass.

## Rules for every test

1. A test earns its place by catching a plausible fault that no other test catches, or by protecting a requirement where failure is serious: security, privacy (POPIA) or data loss. Otherwise it goes.
2. Expected values come from an independent source: the handbook, the printed transcript, my report, a hand calculation shown in a comment, or an independent oracle. Never paste in what the code returned.
3. Test boundaries on both sides, for example 5 and 6 plans, and meetings that touch as well as overlap.
4. Test each rule once, at the lowest level that can see it. A refusal the transcript reader raises is tested in the reader's tests, and the API tests check only that one reaches the client as its problem code.
5. Guards (signed out, outside UCT, staff, setup unfinished, questionnaire pending and another student's data) are checked once, in a sweep over every route the app serves, in `backend/tests/unit/api/test_guards.py`. A new route that forgets a guard fails it automatically.
6. No count snapshots of seed data unless the number is a stated requirement. The seed's own counts are checked once, in the seed tests.
7. Tests of a stand-in in `services/stubs.py` are marked `@pytest.mark.stub("engine")` or `("advisor")`, naming the component that replaces it. They prove wiring, never correctness, and are deleted when the real component lands.
8. Every workaround, cut or known limitation goes in [shortfalls.md](shortfalls.md) as it's found.

## Levels

| Level | What it checks | Where | How to run |
| --- | --- | --- | --- |
| Unit | Each rule, on in-memory stores holding the approved 2026 rulebook, with no network | `backend/tests/unit`, and the in-memory half of `backend/tests/database/test_repository_contract.py` | `make test`. CI runs it on every pull request and every push to main |
| Integration | The Supabase adapters, the migrations, row level security and real sign-in tokens, against a rebuilt local database holding both approved years | `backend/tests/database` | `make check-db`, with Docker running. It wipes local data. CI runs it on every pull request and every push to main |
| Acceptance | The finished system, against held-back cases (the ATPs). ATP-1 measures ingestion against labels written from print and committed before any run, including two departments no build branch opened | `tests/acceptance` (planned: ATP-1's label sheets and harness arrive from branch E) | `make atp1`, and their own workflow on demand, which holds the model key, as held-out wording needs fresh drafts |

## Ingestion tests

The yearly job's tests build each source inside the test: typed page text in the printed layout, a small workbook in the real one's layout, or a few CSV rows. None reads the real handbook, which takes 34 seconds, and none calls a model, as a fake or a cached draft stands in. Their expected values come from the printed page, or the workbook as Excel shows it.

| Stage | Where | The faults they catch |
| --- | --- | --- |
| Collect | `ingestion/test_sources.py` | A source read although its fingerprint changed |
| Read | `ingestion/test_handbook.py`, `test_curricula.py`, `test_timetable.py`, `test_complementary.py`, `test_equivalences.py`, `test_names.py` | A running header leaking into an entry, prose taken for a heading or an entry, a passage cut at the wrong heading, a curriculum table read into the wrong groups or totals, a meeting timed off the period key or stored twice, a cell or row that fits no reading let through, an equivalence not flagged for a person, and a name cased against CP0's rule |
| Translate | `ingestion/test_grammar.py`, `test_translate.py`, `adapters/test_anthropic.py` | Wording with more than one reading accepted, a refusal without its cause, a draft that isn't a rule tree kept, a cached draft asked for again, and a model's answer misread or not asked for as E2 asked |
| Check | `ingestion/test_checks.py` | A check that misses its one planted inconsistency, fires on the row that agrees, or fails a settled exclusion |
| Review | `ingestion/test_review.py` | A first year that isn't all new, an unchanged row not carried over, a removal let through unseen, a decision kept after its reading changed or counted before it's usable, and a check that fails on the year as decided without stopping approval |
| Approve and load | `services/test_ingest.py` | Approval with a row pending, a snapshot that doesn't survive its round trip, a kept removal lost, and a load that rewrites a year held exactly or replaces one held differently unasked |

## Frontend

The eight rules above apply to the frontend too. Its tests run with Vitest and Testing Library through `npm test` in `frontend/`. `make check` and CI's frontend job already call it, so there is no extra step.

| Test | What it checks | The fault it catches |
| --- | --- | --- |
| `src/styles/tokens.test.ts` | Reads `tokens.css` and `theme.css`. Every text token reaches 4.5:1 on every surface, danger and warning text reach it on their tints, white reaches 4.5:1 on the sign-in, accent and course fills, and the focus ring and the checkbox's border reach 3:1, in both themes. The field border reaches 3:1 in light. Dark fields have none and rely on their placeholder, which the secondary text check covers on the field fill. Decorative borders and disabled text are left out, as WCAG allows. Both themes define the same tokens | A token changed to a failing value, a new text token that fails, or a colour given a light value only, which would stay light in the dark theme. It also checks the audit's published ratios, so a broken formula can't pass |
| `src/lib/useAppearance.test.ts` | The choice survives a reload, Match System follows the system, and the page falls back to Match System when storage is blocked | The storage key drifting between `public/theme.js` and the hook, the system's setting being ignored, or a missing try/catch that breaks the page in a private window |
| `src/components/brand/Logo/Logo.test.tsx` | Two logos on one page each get their own title id and their own name, and Microsoft's mark is hidden from screen readers | svgr's `titleProp` setting being lost, so every logo keeps its file's `id="t"` and the ids clash, or the mark being read out beside the button's own name |
| `scripts/check-tsx.test.ts` | The custom lint check rejects `style=` beyond custom properties, re-exports and imports across feature boundaries | The check silently passing everything |
| `scripts/stylelint-config.test.ts` | stylelint rejects raw colours, gradients and radii in a component, and accepts them in `tokens.css` | `ignoreFunctions` drifting back to its default, which lets `rgb()` and `oklch()` through |
| `src/app/routes.test.ts` | The guard sweep, like the backend's in `test_guards.py`. Every page in the real route table is opened by every kind of visitor in a memory router: signed out, a session the API refuses, an account from outside UCT, staff, a student who hasn't finished setup, and an onboarded student. `GET /v1/me` is answered through the real client. Who may open each page, and where each visitor belongs, are written out by hand, and a page with no line there fails. `/` sends every visitor home, every redirect replaces the address, the guard asks `/v1/me` again once Finish Setup has refreshed it, and it waits for a sign-in in the address bar | A page with no rule or the wrong one, a redirect that traps the Back button, a cached `/v1/me` that sends every new student back to onboarding, or a sign-in sent away before its session exists |
| `src/lib/api.test.ts` | A refusal reaches the caller as an `ApiError` with its code, status and extra fields, from a request that carries the session's token and keeps the PDF's body and type through the time limit. A failed fetch, a timeout and an error page in front of the API each get their client-side code | A refusal losing its code or its student numbers, a gateway's HTML page breaking the client, or a request going out unsigned or without its body |
| `src/lib/queryKeys.test.ts` | Each refresh rule invalidates exactly the cached reads written out by hand | A hand-written key that matches no read, so its refresh silently does nothing, or a rule that refreshes too little or too much |
| `src/lib/queryClient.test.ts` | A read is retried after a network failure, a timeout or a 5xx, three times and no more, and never after a refusal | Retrying refusals, which would hold every 4xx state back by 7 seconds, or retrying without end |

Each test was checked by breaking what it guards: the old secondary grey, the audit's input border, the checkbox's dark border set to the field fill, a dark value left out, a renamed storage key, a script that ignores the system's setting or stops watching the choice, a hook without its try/catch, and `ignoreFunctions` turned back on. Then, for the app's plumbing: `redirect()` in place of `replace()`, a guard that doesn't wait for the sign-in, a `/v1/me` cached past Finish Setup, a hand-named key, a sent message that refreshed every chat, a gateway's page passed through as data, and refusals retried. Each made a test fail.

That the error map has words for every code is TypeScript's job, not a test's: `satisfies` fails the build when one is missing. The tests that send a request run in Vitest's node environment, as Node's `Request` refuses jsdom's `AbortSignal`. Their settings are made up, on `.test` hosts that never resolve, so no test reads `frontend/.env` or reaches a real service.

### UI checks

`make check-ui` runs Playwright against the local stack: local Supabase, the backend (`make dev` in `~/SAGE`) and this worktree's frontend on `PORT`, 3000 by default, which Playwright starts if it isn't running. If Supabase or the backend isn't running, it stops with one plain line saying which. The first run downloads Playwright's Chromium.

CI never runs it. It needs that stack, and screenshots differ between operating systems, so the parity images are compared by eye on my Mac. CI still type-checks and lints every spec and helper through `make check`.

- **Projects.** Light and dark, at 1280 by 820. A setup project signs Mbali in once per run with `make sign-in`'s link, and keeps her session in the git-ignored `frontend/e2e/.auth/`.
- **Made-up visitors.** Staff, an account from outside UCT and a student who hasn't finished setup are Mbali's session with a made-up answer from `GET /v1/me`, built from `api-types.ts`. So no check resets a real account, as every worktree runs these checks against one local database.
- **Helpers**, in `frontend/e2e/`:
  - `axe.ts` runs axe-core with the audit's tags: wcag2a, wcag2aa, wcag21a, wcag21aa and wcag22aa. The bar is zero violations.
  - `keyboard.ts` tabs through a page and checks that every stop shows the focus ring. It returns the stops in order.
  - `parity.ts` drives a prototype to a state through its own controls and writes it beside React.
  - `visitors.ts` holds the made-up visitors and the `freshStudent` fixture.
- **Specs.** They end `.spec.ts` and sit in feature folders beside the Vitest tests, which end `.test.ts`, so neither runner loads the other's files. `src/app/routes.spec.ts` checks every page in the route table, as its visitor, with axe and the keyboard walk.
- **Parity images.** Each feature keeps its cases in its own folder. The images land in `frontend/parity/<feature>/<case>-<theme>.png`, with `-hover` for the hover state. Where a prototype has no dark design, the dark image shows React alone.
- **The fresh account.** `make sign-in-new` deletes and signs in again Ilvane Qorthu (QRTILV999), a made-up student who hasn't finished setup, and `make transcript` writes `local/transcript.pdf` with her student number. A spec that goes through onboarding asks for the `freshStudent` fixture, which runs `make sign-in-new`, in a file whose tests run one at a time. Nothing else in `make check-ui` touches her account.

## How strong the tests are

| Command | What it reports | Time |
| --- | --- | --- |
| `make test` | The unit tests, then each file's lines that no unit test runs | 30 seconds |
| `make mutation` | The share of mutants the unit tests catch, written to `backend/mutation-score.txt` | 12 minutes |
| `make planted-faults` | Which of the 26 planted faults the unit tests catch, and the test that caught each: the 24 from my test review, and two in the review and approval the thesis rests on | 7 minutes |

Line coverage counts the lines that ran during the tests, not whether anything checked what they did, so it overstates. Mutation testing checks the checking. mutmut makes 5,247 copies of the code in `api/`, `domain/`, `ingestion/` and `services/`, each with one small change, such as `<` to `<=` or `5` to `6`. It runs the unit tests against each copy and counts the copies that make a test fail. A copy that makes the tests time out counts as caught. The 26 planted faults are plausible bugs chosen by hand, while mutmut makes every small change it can, most of them easy to catch, so its score runs higher.

The score leaves out the integration tests, code outside functions (such as the transcript reader's patterns), and the storage adapters, where student isolation is enforced. The mutants that survive are listed below.

## Numbers

| | 12 Oct (e60bca0) | 18 Oct (fb4a050) | Branch D (de6b976) |
| --- | --- | --- | --- |
| Test functions | 167 | 237 | 241 |
| Cases: unit and integration | 177 and 76 | 337 and 78 | 343 and 78 |
| Line coverage, unit tests | 92.8% (1,746 of 1,882 lines) | Not measured | 91.4% (3,417 of 3,738 lines) |
| Mutation score | 90.8% (1,542 of 1,699 mutants) | 93.0% (4,917 of 5,286 mutants) | 93.4% (4,901 of 5,247 mutants) |
| Planted faults caught | 24 of 24 | 24 of 24 | 26 of 26 |

Between 12 and 18 Oct, C1 and C2 added the ingestion code and its tests, which trebled the mutants. On 18 Oct three test runs crashed in pytest's clean-up and counted as caught, so that score was at worst 4,914; each test session now has a temporary folder of its own. Branch D moved the tests onto the approved 2026, removed the seed's rulebook code and two tests that caught nothing alone, and added five. Line coverage counts the Supabase adapters and the `sage` command too, which only the integration tests run. Planted faults 17 and 18 are in the eligibility stand-in, and leave the count when the engine replaces it, as do the 10 tests marked `stub`. Faults 25 and 26 are in the review and approval.

## Mutants that survive

346 of the 5,247 mutants survive. 96 only change wording a student or developer reads (a prompt, a label, a check's name, a refusal's detail, a log line) or the text inside a made-up id or cache key, which no test should pin. 119 are equivalent: no realistic input tells them apart from the code, such as a file read with this Mac's default encoding, a path given in other capitals on its case-blind disk, a reader's state set before it's ever used, or zip's strict flag where both sides always match. 17 only change how `drafts.json`, `review.json` or `rulebook.json` is laid out. Every survivor in the code the thesis's claims rest on (the transcript reader's statuses, the averages, questionnaire narrowing, student isolation, and a year's review and approval) was closed with a test. The other 114 are future work. The readers' gaps are layouts the test pages don't print, which ATP-1 measures on the real sources instead:

| Where | What no unit test checks | Mutants |
| --- | --- | --- |
| Curriculum reader | Layouts the test pages don't print: notes set out otherwise, instructions over two lines, the "Further" table's number and casing, an optional course's credits, and the page a group starts on | 20 |
| Timetable reader | A quarter's course on a semester sheet, the title row's width and a block's first row at their boundaries, several links or differences at once, and a course no curriculum takes | 17 |
| Handbook reader | Gaps and type sizes at their exact boundaries, a heading printed twice, a clause or section cut at its edges, and an entry the book ends inside | 15 |
| Complementary reader | A row shorter than the header, and passage order within one handbook | 4 |
| Checks | A full-year course on a semester sheet, and a skipped workbook row before one that disagrees | 3 |
| Names | A title already in mixed case, and how punctuation leaves a word | 2 |
| Translation | Counts past one drafted or reused string | 2 |
| Ingest service | A year with no timetable or workbook, as 2023 has none, meetings that need curriculum links, and this year's own drafts counted as an earlier year's | 4 |
| Equivalences reader | A file whose columns are wrong | 1 |
| Seed loader | A seed file that leaves out a table or a key | 22 |
| Seed loader | Message citations, as the seed has none | 2 |
| Seed loader | Rows given the same id, which only the database's keys refuse | 2 |
| Questionnaire | Hearted courses listed first among the course options, as all six of hers are hearted | 3 |
| Plans | The order of a course's meetings: unknown days and times last, alternatives in order | 5 |
| Plan view | A reason's course code, and the handbook passage it cites, as no seeded reason cites one yet | 6 |
| Problems | The dotted path of a nested invalid field | 1 |
| Accounts | An address with two @ signs | 1 |
| Rulebook cache | A second year in the cache, and a test clock that doesn't start at zero | 2 |
| Eligibility stand-in | A credited result counting as passed | 2 |
