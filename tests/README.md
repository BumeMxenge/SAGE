<!-- What lives in tests/: whole-system acceptance tests only -->
# Acceptance tests

Acceptance tests (ATPs) live in acceptance/, one folder each, such as acceptance/atp1/. They evaluate the completed system with separate, held-back cases, so keep development cases out of the final acceptance sets. ATP-1's labels come only from print and are committed before its first run. They run on demand from a laptop, never on push: ATP-1 with `make atp1`, from the held-out drafts its first run cached.

Unit and integration tests live with the code they test, in backend/tests/. Design experiments live in experiments/.
