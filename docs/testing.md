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
| Unit | Each rule, on in-memory stores, with no network | `backend/tests/unit`, and the in-memory half of `backend/tests/database/test_repository_contract.py` | `make test`. CI runs it on every push |
| Integration | The Supabase adapters, the migrations, row level security and real sign-in tokens, against a rebuilt local database | `backend/tests/database` | `make check-db`, with Docker running. It wipes local data. CI runs it on every push |
| Acceptance | The finished system, against held-back cases (the ATPs) | `tests/acceptance` (planned) | Their own workflow, on demand |

## Frontend

The eight rules above apply to the frontend too. Its tests run with Vitest and Testing Library through `npm test` in `frontend/`. `make check` and CI's frontend job already call it, so there is no extra step.

| Test | What it checks | The fault it catches |
| --- | --- | --- |
| `src/styles/tokens.test.ts` | Reads `tokens.css` and `theme.css`. Every text token reaches 4.5:1 on every surface, white reaches 4.5:1 on the sign-in, accent and course fills, and the focus ring and the checkbox's border reach 3:1, in both themes. The field border reaches 3:1 in light. Dark fields have none and rely on their placeholder, which the secondary text check covers on the field fill. Decorative borders and disabled text are left out, as WCAG allows. Both themes define the same tokens | A token changed to a failing value, a new text token that fails, or a colour given a light value only, which would stay light in the dark theme. It also checks the audit's published ratios, so a broken formula can't pass |
| `src/lib/useAppearance.test.ts` | The choice survives a reload, Match System follows the system, and the page falls back to Match System when storage is blocked | The storage key drifting between `public/theme.js` and the hook, the system's setting being ignored, or a missing try/catch that breaks the page in a private window |
| `src/components/brand/Logo/Logo.test.tsx` | Two logos on one page each get their own title id and their own name, and Microsoft's mark is hidden from screen readers | svgr's `titleProp` setting being lost, so every logo keeps its file's `id="t"` and the ids clash, or the mark being read out beside the button's own name |
| `scripts/check-tsx.test.ts` | The custom lint check rejects `style=` beyond custom properties, re-exports and imports across feature boundaries | The check silently passing everything |
| `scripts/stylelint-config.test.ts` | stylelint rejects raw colours, gradients and radii in a component, and accepts them in `tokens.css` | `ignoreFunctions` drifting back to its default, which lets `rgb()` and `oklch()` through |

Each test was checked by breaking what it guards: the old secondary grey, the audit's input border, the checkbox's dark border set to the field fill, a dark value left out, a renamed storage key, a script that ignores the system's setting or stops watching the choice, a hook without its try/catch, and `ignoreFunctions` turned back on. Each made a test fail.

Not yet built: Playwright with axe, the keyboard walk and the parity screenshots. They need the local stack, so they arrive with app foundations as their own `make` target that CI doesn't run. The same branch adds a route-guard sweep that mirrors the backend's.

## How strong the tests are

| Command | What it reports | Time |
| --- | --- | --- |
| `make test` | The unit tests, then each file's lines that no unit test runs | 30 seconds |
| `make mutation` | The share of mutants the unit tests catch, written to `backend/mutation-score.txt` | 7 minutes |
| `make planted-faults` | Which of the 24 faults from my test review the unit tests catch, and the test that caught each | 4 minutes |

Line coverage counts the lines that ran during the tests, not whether anything checked what they did, so it overstates. Mutation testing checks the checking. mutmut makes 1,697 copies of the code in `api/`, `domain/`, `ingestion/` and `services/`, each with one small change, such as `<` to `<=` or `5` to `6`. It runs the unit tests against each copy and counts the copies that make a test fail. A copy that makes the tests time out counts as caught. The 24 planted faults are plausible bugs chosen by hand, while mutmut makes every small change it can, most of them easy to catch, so its score runs higher.

The score leaves out the integration tests, code outside functions (such as the transcript reader's patterns), and the storage adapters, where student isolation is enforced. The mutants that survive are listed below.

## Numbers

| | Before (6041460) | After (e60bca0) |
| --- | --- | --- |
| Test functions | 182 | 167 |
| Cases: unit and integration | 174 and 101 | 177 and 76 |
| Line coverage, unit tests | 92.8% (1,747 of 1,882 lines) | 92.8% (1,746 of 1,882 lines) |
| Mutation score | 87.8% (1,491 of 1,699 mutants) | 90.8% (1,542 of 1,699 mutants) |
| Planted faults caught | 18 of 24 | 24 of 24 |

The one line coverage lost is in the fake token checker the tests use, which only the removed test of that fake reached. Planted faults 17 and 18 are in the eligibility stand-in, and leave the count when the engine replaces it, as do the 10 tests marked `stub`.

## Mutants that survive

157 of the 1,697 mutants survive. 79 only change wording a student or developer reads (a prompt, a label, a refusal's detail, a log line) or the text inside a made-up id or cache key, which no test should pin. 16 are equivalent: no realistic input tells them apart from the code, such as reading the seed file with the platform's default encoding. Every survivor in the code the thesis's claims rest on (the transcript reader's statuses, the averages, questionnaire narrowing and student isolation) was closed with a test. The other 62 are future work:

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
