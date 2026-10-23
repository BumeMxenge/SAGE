<a id="readme-top"></a>

<!-- PROJECT HEADER -->
<div align="center">
  <a href="#about-the-project">
    <img src="assets/brand/sage-readme-banner.webp" alt="SAGE logo reveal: Student Advisor for Guided Enrolment" width="900">
  </a>

  <p align="center">
    A registration-planning prototype that connects course choices, university rules and grounded advice.
  </p>
</div>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li><a href="#about-the-project">About the Project</a></li>
    <li><a href="#capabilities">Capabilities</a></li>
    <li><a href="#technical-direction">Technical Direction</a></li>
    <li><a href="#project-status">Project Status</a></li>
    <li><a href="#contributor">Contributor</a></li>
  </ol>
</details>

<!-- ABOUT THE PROJECT -->
## About the Project

SAGE stands for **Student Advisor for Guided Enrolment**. It is being designed to help an enrolled student construct, understand and refine a valid course selection for the coming academic year.

The initial scope is the three degrees administered by UCT's Department of Electrical Engineering, including mainstream and ASPECT routes. A student's academic record, curriculum rules, course offerings, timetable and preferences all affect which plans are possible. SAGE is intended to show valid options and explain when a proposed course cannot fit.

The design has one firm boundary: a deterministic engine decides validity. The conversational advisor uses engine results and handbook passages to explain decisions, and refers questions without evidence to a human advisor. SAGE generates every valid plan up front, each with its reasons. The student browses and compares those plans, and the advisor explains them. Students never edit a plan. When they ask about a change, the advisor points to an existing plan that has it.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Capabilities

Built so far: importing and confirming the academic record, the yearly handbook ingestion with its review of changes, the planning engine, which builds every valid plan for a student's year with the reasons behind it, the API behind plan exploration and comparison, and the advisor, which answers a student's questions about her plans from the handbook and the engine.

- **Academic record:** Import and confirm the student's record before planning.
- **Rule and timetable checks:** Check entry requirements, credit rules, course offerings and clashes.
- **Plan exploration:** Generate valid annual plans and filter them by student preferences, with any search limit made clear.
- **Explanations:** Give structured reasons for exclusions or conditional choices, with source citations where appropriate.
- **Grounded advisor:** Answer in the context of the current plan and point to an existing plan when the student asks about a change.
- **Plan workspace:** View each plan as a timetable or course list per term, and compare two plans side by side.
- **Annual updates:** Review handbook-year rule changes before an administrator activates them.
- **Human hand-off:** Save, recheck and export a plan for review with a faculty advisor.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- TECHNICAL DIRECTION -->
## Technical Direction

These are the technologies SAGE is built with. The backend, its database, sign-in, the planning engine and the advisor run on them today.

**Interface**

[![React][React.js]][React-url] [![TypeScript][TypeScript]][TypeScript-url]

**Backend**

[![Python][Python]][Python-url]

**Knowledge store**

[![Supabase][Supabase]][Supabase-url] [![PostgreSQL][PostgreSQL]][PostgreSQL-url]

**Development and deployment**

[![VS Code][VSCode]][VSCode-url] [![GitHub Actions][GitHubActions]][GitHubActions-url] [![Docker][Docker]][Docker-url]

Python runs the plan service, transcript reading, handbook ingestion, deterministic rule evaluation and the advisor's tools. Supabase Postgres stores the versioned rules, the handbook passages and the plans. The FastAPI backend runs as a container on Azure Container Apps, the React interface is deployed separately as static files, and Supabase (EU) holds the data and handles sign-in.

pdfplumber reads the transcripts and the handbooks, and clingo generates plans. GPT-6 Luna, chosen in design experiment E4, is the advisor's language model, through OpenAI's API.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- STATUS -->
## Project Status

The backend API behind every planned screen is built, tested and deployed. Handbook ingestion is built too, with the 2023 and 2026 handbooks approved for all six of the department's curricula, so the API runs on the real 2026 rules. Mbali, a made-up student, holds the only student data. The planning engine builds each student's plans from her own record, and the advisor answers her questions through GPT-6 Luna, from her slice of the handbook and the engine's facts, checking every quote before she sees it. The onboarding flow, the registration planner and their loading and error states have interactive HTML prototypes with mock data. How the backend is tested is in [docs/testing.md](docs/testing.md), and its known gaps are in [docs/shortfalls.md](docs/shortfalls.md). The implementation roadmap below covers the application only.

| Stage | Implementation work | Status |
| --- | --- | --- |
| 1. Interface prototypes | Explore the onboarding and planning flows with mock data. | ✅ Complete |
| 2. Data foundation | Ingest handbook and timetable sources, verify extracted rules and build the versioned knowledge store. | 🚧 In progress: the store, its security, transcript reading and handbook ingestion are built, with 2023 and 2026 approved. ATP-1, which measures ingestion's accuracy, is next. |
| 3. Planning engine | Implement eligibility checks, valid plan search and structured explanations. | 🚧 In progress: eligibility checks, plan search and explanations are built. ATP-2, which checks them, is next. |
| 4. Advisor | Add handbook retrieval, engine tools, grounded answers and student-confirmed proposals. | 🚧 In progress: the advisor is built, with its citation check and guardrails. ATP-3, which tests it, is next. |
| 5. Interface | Connect the React interface to the plan service and the advisor. | 🚧 In progress: the API serves every planned screen. The React screens are next. |
| 6. Deployment and system checks | Deploy the integrated application and run end-to-end, load, access and usability checks. | 🚧 In progress: the backend and frontend deploy on every merge to main. The system checks come last. |

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTRIBUTOR -->
## Contributor

- **Bume Mxenge:** [GitHub](https://github.com/BumeMxenge) &middot; [LinkedIn](https://www.linkedin.com/in/bume-mxenge/)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- BADGE LINKS -->
[React.js]: https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB
[React-url]: https://react.dev/
[TypeScript]: https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white
[TypeScript-url]: https://www.typescriptlang.org/
[Python]: https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white
[Python-url]: https://www.python.org/
[Supabase]: https://img.shields.io/badge/Supabase-3FCF8E?style=for-the-badge&logo=supabase&logoColor=white
[Supabase-url]: https://supabase.com/
[PostgreSQL]: https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white
[PostgreSQL-url]: https://www.postgresql.org/
[VSCode]: https://img.shields.io/badge/VS_Code-007ACC?style=for-the-badge&logo=visualstudiocode&logoColor=white
[VSCode-url]: https://code.visualstudio.com/
[GitHubActions]: https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white
[GitHubActions-url]: https://github.com/features/actions
[Docker]: https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white
[Docker-url]: https://www.docker.com/
