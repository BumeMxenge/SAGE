<!-- What lives in tests/: whole-system acceptance tests only -->
# Acceptance tests

Acceptance tests (ATPs) will live in acceptance/ once they are defined. They evaluate the completed system with separate, held-back cases, so keep development cases out of the final acceptance sets. They will run on demand through their own workflow, never on push.

Unit and integration tests live with the code they test, in backend/tests/. Design experiments live in experiments/.
