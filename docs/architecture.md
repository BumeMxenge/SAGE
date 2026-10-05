<!-- Component map and dependency rule for the whole system. The black-box architecture diagram goes here -->
# Architecture

## Where things live

| Folder | What it does |
| --- | --- |
| `backend/src/sage/api` | HTTP routes, request and response schemas, auth dependencies |
| `backend/src/sage/services` | Use cases that join the components: onboarding, planning, check-ins |
| `backend/src/sage/ingestion` | Turns handbook, transcript, timetable and electives sources into a year-versioned rule model |
| `backend/src/sage/engine` | Validates plans and generates every valid plan (clingo) |
| `backend/src/sage/advisor` | Conversational agent: engine tools, retrieval, guardrails, prompts |
| `backend/src/sage/domain` | Shared models (plan, course, rule model, student) and interfaces |
| `backend/src/sage/adapters` | Supabase and model-provider implementations of those interfaces |
| `frontend/` | React and TypeScript interface, deployed as static files |
| `supabase/` | Database migrations |
| `data/` | Raw sources and reviewed rule snapshots, by year |

## Dependency rule

Imports only point inward: `api → services → ingestion / engine / advisor → domain`.

- `adapters/` implements interfaces defined in `domain/`.
- `advisor` may call `engine` (its tools). `engine` never calls `advisor`.
- Only `adapters/` imports vendor SDKs (Supabase, model providers).
- Year and department are data, not code. Nothing in the code tree is named after a programme.

## System diagram

To add: the black-box architecture diagram from Chapter 3.
