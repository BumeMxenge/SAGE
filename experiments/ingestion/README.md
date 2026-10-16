<!-- Ingestion's design decisions: each one's choice, options, deciding rule, reason and cost -->
# Ingestion decisions

How SAGE turns a year's handbook into its rulebook was settled by the decisions below. Each gives the choice, the options that would work, the rule that decided it, why it won and what it costs. The costs are also rows in [docs/shortfalls.md](../../docs/shortfalls.md). Requirement parsing and the drafting model are settled by experiment E2, in [requirement-parsing/](requirement-parsing/). The rest are argued from the sources and the documentation.

## PDF extraction tool

- **Choice.** pdfplumber.
- **Options.** pdfplumber, pdfminer.six, pypdf and PyMuPDF. All four read a PDF's text layer.
- **Rule.** It must read every character of a born-digital handbook with its position on the page, so the running header can be cropped off, under a permissive licence.
- **Why it won.** The handbooks are born-digital, so each option reads the same characters, and what goes wrong is layout, such as a running header leaking into an entry. pdfplumber gives every character's position, so the readers crop the header by height. It has an MIT licence, and it already reads transcripts, so the backend keeps one PDF library. pdfminer.six, which pdfplumber is built on, and pypdf give positions only through lower-level layout code. PyMuPDF's AGPL licence would decide SAGE's own.
- **Cost.** No tool comparison was run. It reads the text layer only, so a scanned handbook would need OCR.

## Requirement parsing

- **Choice.** Grammar first: the grammar reads what it can, and a model drafts each string it refuses, for a person to check.
- **Options.** A model alone, its tree stored as it answers; the grammar alone, a refused string becoming a `refer` leaf; or grammar first, with model drafts.
- **Rule.** E2's, applied in order to 81 strings from three other departments: no wrong rule stored unseen; whatever is stored unseen is the same on every run; the fewest strings needing a person, then the fewest leaves a person must type or fix; the lowest cost.
- **Why it won.** Only the three arms that start with the grammar stored no wrong rule unseen. Each stored the grammar's 48 parses, all right, so its error rate is below 6.1% with 95% confidence. A model alone stored wrong rules unseen, 5 of 71 for Claude Haiku 5.5 and 11 of 71 for GPT-6 Luna, mostly a DP read as a pass, and neither gave the same tree on every run for every string. The three that remained all send the grammar's 33 refusals to a person, so the leaves to type or fix decided it: 14 with Haiku's drafts, 21 with Luna's and 99 with none. The full tables are in [results/tables.md](results/tables.md).
- **Cost.** The yearly job depends on a model provider, whose update can change the next year's drafts. Another department's wording is refused more often than Electrical's: the grammar reads 48 of the 81 strings (59%), against 39 of the 58 Electrical fields it was written from (67%), so a new department's review is heavier. Every draft still needs a person, and 6 of Haiku's 33 needed correcting.

## Drafting model

- **Choice.** Claude Haiku 5.5, provisionally. C1 uses it until the advisor milestone chooses the one model SAGE uses for drafting and the advisor.
- **Options.** Claude Haiku 5.5 and GPT-6 Luna, at the same price per token.
- **Rule.** More of the grammar's refusals drafted exactly right on the first run, then fewer leaves to correct, then the account I keep. McNemar's exact test is reported as a finding, not a decision.
- **Why it won.** Haiku drafted 27 of the 33 refusals exactly right, with 14 leaves to correct, against Luna's 22 with 21. McNemar's exact test can't separate the two: 7 refusals only Haiku drafted right and 2 only Luna, p = 0.180. So 33 strings favour Haiku without showing that it's the better drafter.
- **Cost.** Haiku's structured output can't compile a rule tree deeper than three levels, and printed trees go to five, so Haiku drafts without a schema and each draft is checked against `EntryRule` once it arrives. All 243 of its E2 replies passed. A draft depends on one provider's model, so a cached draft is kept, not redrawn.

## Rule representation

- **Choice.** Typed rule trees stored as JSON in their rows, `courses.entry_rule` and `curriculum_rules.rule`, checked against the types in `backend/src/sage/domain/rules.py` on every load.
- **Options.** Typed trees in the rule rows; normalised tables, with one row per node and a key to its parent; or the engine's own logic facts, stored as text.
- **Rule.** It must express every printed requirement, with a `refer` leaf for wording only a person can judge. One meaning must have one form, so comparing two years finds only real changes. It mustn't depend on the engine, and it must share one store with the student data.
- **Why it won.** Typed trees meet all four. The canonical form sorts the children of `all` and `any`, so a list printed in another order isn't a change. The engine reads the trees, never the reverse, and they sit in the same Postgres as the students' plans. Normalised tables would give foreign keys inside a tree, but one requirement would become many rows, compared as sets and read back with a recursive query. Logic facts would tie the stored rules to the engine's language, which isn't built yet. E2's labels bear the first point out: every one of its 81 strings from three other departments fits the types.
- **Cost.** A tree has no foreign keys inside it, so a check at ingestion that every course a tree names exists stands in for them. Reverse lookups, such as which courses need EEE2045F, happen in code. Wording no type expresses becomes a `refer` leaf, which the engine can't check: 21 of E2's 81 strings need one, and 11 of them ask for a DP, the first leaf another department would need.

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
