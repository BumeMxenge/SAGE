<!-- Component map and dependency rule for the whole system -->
# Architecture

## Where things live

Folders marked (planned) don't exist yet; each arrives with its first code.

| Folder | What it does |
| --- | --- |
| `backend/src/sage/api` | HTTP routes, request and response schemas, auth dependencies |
| `backend/src/sage/cli.py` | The `sage` command, such as `sage seed`, which loads the made-up student |
| `backend/src/sage/services` | Use cases that join the components: onboarding, plans and the questionnaire, electives, history and chats |
| `backend/src/sage/ingestion` | Turns sources into data: a student's transcript into her course history, a printed requirement into a rule tree (the grammar), and (planned) a year's handbook, timetable and electives workbook into an approved rulebook, through readers, checks across the sources and a review of what changed since the year before |
| `backend/src/sage/engine` (planned) | Validates plans and generates every valid plan (clingo) |
| `backend/src/sage/advisor` (planned) | Conversational agent: engine tools, scoped context (the handbook passages for her courses, with no embeddings or search), guardrails, prompts |
| `backend/src/sage/domain` | Shared models (plan, course, rule model, student) and interfaces |
| `backend/src/sage/adapters` | Supabase and (planned) model-provider implementations of those interfaces, and in-memory fakes for tests |
| `backend/tests` | Unit and integration tests. [testing.md](testing.md) has their rules and how to run them |
| `backend/scripts` | Measures the tests: the planted faults, and the line `make mutation` writes |
| `frontend/` | React and TypeScript interface, deployed as static files. Its code is in `frontend/src`, in the six folders below |
| `frontend/src/app` | The app's frame: providers, the router and the shell. Until M3's shell branch it holds only the starter page, `App.tsx` |
| `frontend/src/features/<feature>` | Everything one feature owns: its page, routes, own components, hooks, API calls, copy and tests. Deleting the folder removes the feature. `auth` exists. M3 adds (planned) onboarding, history, electives, questionnaire, plan and assistant |
| `frontend/src/components/<Name>` | Shared components, one folder each with `Name.tsx`, `Name.module.css` and any test. They are built on React Aria Components and styled from the tokens. A component is shared only if the design system lists it or two features use it |
| `frontend/src/lib` | Shared code with no markup: the appearance hook, the contrast and token helpers and the toast queue, and later the API client and query keys |
| `frontend/src/styles` | `tokens.css` (values shared by both themes) and `theme.css` (a light block and a dark block of colours), the only places a raw colour, size, radius, shadow or duration is written, and `base.css` |
| `frontend/src/design-system` | The code of the development-only review page, `frontend/design-system.html`. Nothing imports from it, and `vite build` leaves it out |
| `supabase/` | Database migrations |
| `data/` | `sources/<year>/`: each year's handbook, workbooks and equivalences, with `manifest.toml` holding each file's fingerprint. `rules/<year>/` (planned): the cached model drafts (`drafts.json`), the review sheet (`review.csv`) and the approved snapshot (`rulebook.json`). `synthetic/`: the made-up student |

## Dependency rule

Imports only point inward: `api / cli → services → ingestion / engine / advisor → domain`.

- `adapters/` implements interfaces defined in `domain/`.
- `advisor` may call `engine` (its tools). `engine` never calls `advisor`.
- Only `adapters/` imports SDKs for outside services (Supabase, model providers). Only `engine/` imports clingo.
- Year and department are data, not code. Nothing in the code tree is named after a programme.

## Frontend dependency rule

Imports run one way, and `frontend/scripts/check-tsx.ts` (run by `npm run lint`) enforces it.

- Features use `components/`, `lib/` and `styles/`. Shared code never imports a feature, features never import each other, and nothing imports `design-system/`. When two features need the same thing, it moves to shared.
- A feature's specialised component is built from the shared base through its props, never by copying the base's markup or styles.
- Every import names what it uses, from the file that defines it: `import { Button } from '@/components/Button/Button.tsx'`. There are no index files that re-export a folder, no `import * as`, and no default exports except where a tool needs one.
- `@/` points at `src/`. Imports within one folder use `./`.

## Privacy

- SAGE's own tables hold no names, email addresses or student numbers.
- Supabase Auth keeps each account's UCT email, which contains the student number. SAGE needs it to identify the account and to check that a transcript belongs to the person uploading it. Supabase Auth also keeps Microsoft's identifiers for the account, but no name: SAGE never asks Microsoft for the profile scope, which is what would bring one.
- SAGE works the student number out from the email when it needs it, and keeps no copy of its own.
- A student's name comes from Microsoft Graph at sign-in and stays in their browser.

## System diagram

To add: the black-box architecture diagram from Chapter 3.

## Future work

- Semester check-ins are in the design, but won't be built before submission.
