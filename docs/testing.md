<!-- How the backend is tested: the rules every test follows, the levels, how to run them, and how strong they are -->
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

## How strong the tests are

| Command | What it reports | Time |
| --- | --- | --- |
| `make test` | The unit tests, then each file's lines that no unit test runs | 30 seconds |
| `make mutation` | The share of mutants the unit tests catch, written to `backend/mutation-score.txt` | 7 minutes |
| `make planted-faults` | Which of the 24 faults from my test review the unit tests catch, and the test that caught each | 4 minutes |

Line coverage counts the lines that ran during the tests, not whether anything checked what they did, so it overstates. Mutation testing checks the checking. mutmut makes 1,699 copies of the code in `api/`, `domain/`, `ingestion/` and `services/`, each with one small change, such as `<` to `<=` or `5` to `6`. It runs the unit tests against each copy and counts the copies that make a test fail. A copy that makes the tests time out counts as caught. The 24 planted faults are plausible bugs chosen by hand, while mutmut makes every small change it can, most of them easy to catch, so its score runs higher.

The score leaves out the integration tests, code outside functions (such as the transcript reader's patterns), and the storage adapters, where student isolation is enforced. The mutants that survive, and why, are listed in [shortfalls.md](shortfalls.md).

## Numbers

| | Before (6041460) | After (e60bca0) |
| --- | --- | --- |
| Test functions | 182 | 167 |
| Cases: unit and integration | 174 and 101 | 177 and 76 |
| Line coverage, unit tests | 92.8% (1,747 of 1,882 lines) | 92.8% (1,746 of 1,882 lines) |
| Mutation score | 87.8% (1,491 of 1,699 mutants) | 90.8% (1,542 of 1,699 mutants) |
| Planted faults caught | 18 of 24 | 24 of 24 |

The one line coverage lost is in the fake token checker the tests use, which only the removed test of that fake reached. Planted faults 17 and 18 are in the eligibility stand-in, and leave the count when the engine replaces it, as do the 10 tests marked `stub`.
