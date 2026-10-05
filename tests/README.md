<!-- What lives in tests/: whole-system acceptance tests only -->
# Acceptance tests

acceptance/ holds ATP-1 to ATP-9. These evaluate the completed system with separate, held-back cases. Keep development cases out of the final acceptance sets. They run on demand through the Acceptance tests workflow, never on push.

Unit and integration tests live with the code they test, in backend/tests/. Design experiments live in experiments/.

The .gitkeep files preserve each otherwise empty folder in Git. Replace each marker as its protocol, data and code are added.
