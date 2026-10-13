<!-- Ingestion's design decisions: each one's choice, options, deciding rule, reason and cost -->
# Ingestion decisions

How SAGE turns a year's handbook into its rulebook was settled by the decisions below. Each gives the choice, the options that would work, the rule that decided it, why it won and what it costs. The costs are also rows in [docs/shortfalls.md](../../docs/shortfalls.md). Requirement parsing and the drafting model are settled by experiment E2, in [requirement-parsing/](requirement-parsing/). The rest are argued from the sources and the documentation.

## PDF extraction tool

- **Choice.** pdfplumber.
- **Options.** pdfplumber, pdfminer.six, pypdf and PyMuPDF. All four read a PDF's text layer.
- **Rule.** It must read every character of a born-digital handbook with its position on the page, so the running header can be cropped off, under a permissive licence.
- **Why it won.** The handbooks are born-digital, so each option reads the same characters, and what goes wrong is layout, such as a running header leaking into an entry. pdfplumber gives every character's position, so the readers crop the header by height. It has an MIT licence, and it already reads transcripts, so the backend keeps one PDF library. pdfminer.six, which pdfplumber is built on, and pypdf give positions only through lower-level layout code. PyMuPDF's AGPL licence would decide SAGE's own.
- **Cost.** No tool comparison was run. It reads the text layer only, so a scanned handbook would need OCR.

## Rule representation

- **Choice.** Typed rule trees stored as JSON in their rows, `courses.entry_rule` and `curriculum_rules.rule`, checked against the types in `backend/src/sage/domain/rules.py` on every load.
- **Options.** Typed trees in the rule rows; normalised tables, with one row per node and a key to its parent; or the engine's own logic facts, stored as text.
- **Rule.** It must express every printed requirement, with a `refer` leaf for wording only a person can judge. One meaning must have one form, so comparing two years finds only real changes. It mustn't depend on the engine, and it must share one store with the student data.
- **Why it won.** Typed trees meet all four. The canonical form sorts the children of `all` and `any`, so a list printed in another order isn't a change. The engine reads the trees, never the reverse, and they sit in the same Postgres as the students' plans. Normalised tables would give foreign keys inside a tree, but one requirement would become many rows, compared as sets and read back with a recursive query. Logic facts would tie the stored rules to the engine's language, which isn't built yet.
- **Cost.** A tree has no foreign keys inside it, so a check at ingestion that every course a tree names exists stands in for them. Reverse lookups, such as which courses need EEE2045F, happen in code.

## Knowledge store

- **Choice.** Supabase (Postgres 17), the same project that holds the student data.
- **Options.** Supabase; the approved snapshot as a JSON file the backend loads into memory; or SQLite shipped with the backend.
- **Rule.** A student's plans must point into the rules of their year, so the database can refuse to delete a year that a plan uses, with sign-in and row-level security in the same free service.
- **Why it won.** Only tables beside the student tables can hold foreign keys from plans into the rules. A JSON snapshot reads just as well but can't refuse a deletion, and SQLite would be a second database to secure and back up.
- **Cost.** Every request crosses to the EU, as Supabase has no African region. The free project pauses when it's idle.

## Change control

- **Choice.** A version per handbook year, reviewed by exception. Each year is compared with the year before. A person reviews only what a machine can't vouch for, and `sage approve` refuses while anything is pending.
- **Options.** Overwrite the rules each year; keep a version per year and review every item; or keep a version per year and review by exception.
- **Rule.** A plan must keep the rules of its year, and a person's time goes only where no machine can vouch for a reading.
- **Why it won.** Rules never change mid-year, so a year is the natural version, and overwriting would change the rules under a student's earlier plans. Reviewing every item would mean hundreds of rows a year, most of them unchanged. Review by exception shows only the changes and refusals, each with its cause.
- **Cost.** An approved year can't be corrected in place: a correction means approving the year again. Items accepted automatically are never seen by a person, by design, which ATP-1 measures. The number of rules that changed between 2023 and 2026 is counted at CP2, when the two years are compared.
