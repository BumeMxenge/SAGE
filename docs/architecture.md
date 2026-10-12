<!-- Component map and dependency rule for the whole system -->
# Architecture

## Where things live

Folders marked (planned) don't exist yet; each arrives with its first code.

| Folder | What it does |
| --- | --- |
| `backend/src/sage/api` | HTTP routes, request and response schemas, auth dependencies |
| `backend/src/sage/cli.py` | The `sage` command, such as `sage seed`, which loads the made-up student |
| `backend/src/sage/services` | Use cases that join the components: onboarding, plans and the questionnaire, electives, history and chats |
| `backend/src/sage/ingestion` | Turns sources into data: a student's transcript into her course history, and (planned) the handbook, timetable and electives into a year-versioned rule model |
| `backend/src/sage/engine` (planned) | Validates plans and generates every valid plan (clingo) |
| `backend/src/sage/advisor` (planned) | Conversational agent: engine tools, retrieval, guardrails, prompts |
| `backend/src/sage/domain` | Shared models (plan, course, rule model, student) and interfaces |
| `backend/src/sage/adapters` | Supabase and (planned) model-provider implementations of those interfaces, and in-memory fakes for tests |
| `backend/tests` | Unit and integration tests. [testing.md](testing.md) has their rules and how to run them |
| `backend/scripts` | Measures the tests: the planted faults, and the line `make mutation` writes |
| `frontend/` | React and TypeScript interface, deployed as static files |
| `supabase/` | Database migrations |
| `data/` | Raw sources and reviewed rule snapshots by year, and the made-up student in `synthetic/` |

## Dependency rule

Imports only point inward: `api / cli → services → ingestion / engine / advisor → domain`.

- `adapters/` implements interfaces defined in `domain/`.
- `advisor` may call `engine` (its tools). `engine` never calls `advisor`.
- Only `adapters/` imports SDKs for outside services (Supabase, model providers). Only `engine/` imports clingo.
- Year and department are data, not code. Nothing in the code tree is named after a programme.

## Privacy

- SAGE's own tables hold no names, email addresses or student numbers.
- Supabase Auth keeps each account's UCT email, which contains the student number. SAGE needs it to identify the account and to check that a transcript belongs to the person uploading it. Supabase Auth also keeps Microsoft's identifiers for the account, but no name: SAGE never asks Microsoft for the profile scope, which is what would bring one.
- SAGE works the student number out from the email when it needs it, and keeps no copy of its own.
- A student's name comes from Microsoft Graph at sign-in and stays in their browser.

## System diagram

To add: the black-box architecture diagram from Chapter 3.

## Future work

- Semester check-ins are in the design, but won't be built before submission.
