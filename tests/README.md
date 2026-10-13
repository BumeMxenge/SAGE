<!-- What lives in tests/: whole-system acceptance tests only -->
# Acceptance tests

Acceptance tests (ATPs) will live in acceptance/ once they are defined, one folder each, such as acceptance/atp1/. They evaluate the completed system with separate, held-back cases, so keep development cases out of the final acceptance sets. ATP-1's labels come only from print and are committed before its first run. They will run on demand through their own workflow, never on push.

Unit and integration tests live with the code they test, in backend/tests/. Design experiments live in experiments/.
