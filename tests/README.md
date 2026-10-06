<!-- What lives in tests/: whole-system acceptance tests only -->
# Acceptance tests

acceptance/ holds ATPs yet to come. These evaluate the completed system with separate, held-back cases. Keep development cases out of the final acceptance sets. They run on demand through the Acceptance tests workflow, never on push.

Unit and integration tests live with the code they test, in backend/tests/. Design experiments live in experiments/.


