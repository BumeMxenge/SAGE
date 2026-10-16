<!-- E2's protocol: printed requirements turned into rule trees three ways, on held-apart sets -->
# E2: requirement parsing

**Question.** How should printed requirements become rule trees, so that no wrong rule is stored unseen, with the least work for a person? And how well does each of two models draft what the grammar refuses?

## Sets

A string is a field and its text, as the same words read differently as a co-requisite.

- **Development.** The 58 distinct requirement fields of the courses the six Electrical curricula list in the 2023 and 2026 handbooks, in [data/development.csv](data/development.csv), with the course lists in [data/development-courses.csv](data/development-courses.csv). The grammar was written from them, so they count only as development evidence: E2 reports the grammar's acceptance share on them, and they decide nothing.
- **Validation.** Every distinct field the Architecture, Planning and Geomatics, Civil and Mechanical entries print in the 2026 handbook, less the development courses and any string identical to a development field: 81 strings, all labelled, in [data/labels.csv](data/labels.csv). The arms are compared on these.
- **Test.** Chemical Engineering and Construction Economics, ATP-1's held-out departments. E2 never reads their pages.

`extract.py` reads only fixed page ranges, taken from the contents pages, and none is shared with a held-out department. The three validation departments are read from their first course entries: printed pages 73 to 89, 105 to 113 and 144 to 156.

## Labels

Each tree is written from print, as JSON in the seed's shape, by the conventions in [prompt.md](prompt.md), which also govern ATP-1's labels. The prompt was committed before any validation string was extracted, and the labels before any model was called. The arms read a string as printed where the sheet gives that, and as extracted otherwise. `check_labels.py` checks every tree against `EntryRule`, never against the grammar. The finished sheet had a conformance check against print and prompt.md by an AI assistant (Claude), which changed no tree. Every judgement call is mine, and [data/labels-notes.md](data/labels-notes.md) records them.

## Arms

1. **Model only**, on Claude Haiku 5.5 and on GPT-6 Luna. Every string goes to the model with the shared prompt, schema-constrained output and default sampling, three times, and the first run's tree is stored as it is.
2. **Grammar only.** The grammar's parse is stored, and a refused string becomes a `refer` leaf.
3. **Grammar first, with each model drafting the refusals.** The parse is stored, and a refusal's first-run draft goes to a person. The drafts are the model-only arm's replies to those strings, as the request is the same.

## Measures

On the validation set, for each arm:
- **Stored unseen:** rules stored with no person looking. A `refer` at the root is a referral, not a stored rule.
- **Wrong unseen:** stored rules that differ from their label in normal form, an exact canonical match after a `refer` loses its wording, an `all` inside an `all` (or `any` in `any`) is spliced in, repeats merge, a lone child is lifted and everything is sorted. With none wrong, the one-sided 95% upper bound, 1 − 0.05^(1/n).
- **Needing a person:** strings reviewed, stored with a `refer` leaf, or left with no valid reply.
- **Leaves to type or fix:** every leaf of the label for a referral or an unusable reply, and, for a reviewed draft that's wrong, the leaves in one tree but not the other, counted both ways, at least one.
- **Model right first time,** and **the same tree on all three runs.**
- **Cost and time per pass:** one run over the strings the arm sends to a model, priced from each reply's tokens.
- **McNemar's exact test** on the two models' first-run correctness for the strings the grammar refuses, reported as a finding.

On the development fields, only the grammar's acceptance share, as development evidence.

## Rule

Applied to the validation set, in order:
1. No wrong rule stored unseen.
2. Whatever is stored unseen is the same on every run. For model only, every string's three runs must agree.
3. The fewest strings needing a person, then the fewest leaves to type or fix.
4. The lowest cost.

If a model-only arm passes the first two, the results say so plainly. A model's error is silent and can change when the provider updates the model, while a grammar's refusal is visible, so choosing grammar first over it rests on that argument.

The drafting model is provisional: C1 uses it until the advisor milestone chooses one model for drafting and the advisor. It's the one with more refusals drafted exactly right on the first run, then fewer leaves to correct, then the account I keep.

## Running it

From `experiments/ingestion/`:
1. `uv run python requirement-parsing/extract.py` writes the development fields and the label sheet, or checks that an existing sheet still holds what the handbook prints. It takes about 50 seconds.
2. `uv run python requirement-parsing/check_labels.py` checks the labels.
3. `uv run --env-file .env python requirement-parsing/drafting.py` fills `results/replies/`. It's the only step that calls a provider and costs money, it needs `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` in `.env`, and it won't start while a label is missing.
4. `uv run python requirement-parsing/score.py` prints the three tables and writes them to `results/`. It never calls a provider.
5. `uv run pytest` runs the tests, which never call a model.
