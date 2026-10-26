<!-- What ATP-3's harness measures, how to run it, and how to read its report -->
# ATP-3: grounded advice

ATP-3 asks whether the advisor, frozen at 8f98a59, meets NF-2 on prompts and students it has never seen:
- no validity claim the engine doesn't support
- at least 95% of answerable questions answered
- at least 90% of the rest referred or declined
- at least 95% of citations supporting their claim

A control arm, the same model with no tools, passages, plans or checks, shows what SAGE's guardrails buy. The harness never edits what it tests: it only reads `backend/src`, `data/rules` and its own inputs.

## Inputs

| File | Holds |
| --- | --- |
| `prompts.csv` | The held-back prompts, written by me and committed before any run. For each: its student, the term on screen, its group, the expected behaviour and fact, the handbook quote and page, a spec the engine resolves, a tempting wrong answer, its paraphrase pair, and whether the control arm asks it |
| `students/` | The three held-out records from ATP-2's labels, R1, R4 and R5, as seed files |
| `control_prompt.md`, `judge_prompt.md` | The control arm's system prompt and the judge's rules, committed before any run |
| `HASHES.md` | The SHA-256 of each input, recorded before the first run |

## How it runs

1. **`make atp3-resolve`** fixes every expectation before any model call, and calls none itself.
   - Each student is prepared as `backend/scripts/ask_advisor.py --seed` prepares one: her record in the in-memory stores beside the approved 2026, her plans from the engine, and her questionnaire answered "no preference" when she has more than five, so every plan stays shown.
   - Each prompt's `resolve` spec is answered from the engine and the plan data, never from the advisor's own tools: an eligibility verdict, the plans that hold and avoid given courses, whether two courses clash, or a fact about the open plan's week.
   - Your predicted verdict is kept beside the engine's, and the engine's decides. A verdict that contradicts the prompt's group stops it, unless the prompt is `per_engine`: a declared exception, as P22's was at input review, which follows the engine and is logged.
   - `per_engine` becomes answer, refer or firm_no by the verdict.
   - A quote counts only from its own context: a passage on its printed page, or one that starts a page earlier and runs onto it, and, where the prompt is about a course, that course's entry. A sentence many entries print, such as the course handout's, never stands in for the right one.
   - An answer that rests on the handbook alone, with no verdict or plan fact behind it, becomes a referral when the student's slice doesn't hold its quote's passage: the declared referral override. A course SAGE's rulebook doesn't hold has no verdict and no passage, so the override covers it too.
   - Anything it can't resolve stops it, every problem listed, before it writes `results/resolved.csv`.
2. **`make atp3`** asks, then judges, and costs money. It stops once the run passes USD 5 across OpenAI and Anthropic.
   - `ask.py` asks every prompt three times in fresh chats through the advisor as merged (the SAGE arm), and the prompts marked for the control arm three times each through the same model with only `control_prompt.md` and the student's curriculum, year of study and course record.
   - One queue holds both arms, shuffled with seed 4022, and four turns run at a time.
   - A wrapper around the one client times every call and saves each request body before it's sent, in `results/requests/`, which git ignores. `results/requests.csv` records each body's size and SHA-256, and ATP-6 scans the local files.
   - Once `results/turns.csv` is complete, `ask.py` asks nothing again.
   - `judge.py` then marks every reply (below).
3. **`make atp3-report`** draws the human sample, reads my marks back once I've filled it in, and writes `results/report.md` from the CSVs alone. It prints no date, so a rerun reproduces it byte for byte.

## The judge

- Claude Sonnet 5.5, through the `anthropic` SDK. Its key goes in `tests/acceptance/atp3/.env` as `ANTHROPIC_API_KEY`, which git ignores.
- **It can't run at temperature 0.** Claude Sonnet 5.5 accepts only the default temperature, and answers any other value with an error. So it runs with no sampling setting, adaptive thinking at low effort and a strict JSON schema.
- **The cache fixes its marks.** Each reply is kept in `results/judge/` under the SHA-256 of its request, so a rerun reads the cache and gets the same marks without a call, and a crash resumes where it stopped.
- It has no refusal fallback, so it stays one model throughout. A refusal stops the run.
- For each reply it sees:
  - the question, the resolved expected behaviour, the expected fact, the quote and page, and the tempting wrong answer, labelled as a trap
  - the engine's and the plan data's facts, and the reply's words
  - for the SAGE arm, each citation with its passage
- It never sees the arm's name or the referral flag. It gives an outcome, the validity claim with the course it's about, whether each citation supports its claim, and a one-line reason.
- Outcomes:
  - **correct_answer**: the expected answer in substance
  - **correct_referral**: refers or declines where the prompt expects it
  - **over_referral**: refers where the prompt is answerable
  - **wrong_safe**: wrong or incomplete, but misleading on nothing that matters
  - **unsupported**: states what the evidence contradicts or doesn't support, in a way that could mislead her, or does work it should decline
  - Code adds **unavailable** for a turn that never reached her.

Code then overrides the judge wherever a field can be checked exactly:
1. A validity claim of eligible or not_eligible that differs from the engine's verdict on that course is unsupported. A "check" claim contradicts nothing.
2. A plan offered outside the plans a `find_plan` prompt resolved to, or any offer where it resolved to no plan, is unsupported.
3. SAGE arm, on an answerable prompt:
   - The fixed referral, or a reply with the referral flag that doesn't give the expected answer, is over_referral.
   - A right answer with the flag set stays correct_answer, and the report tallies these apart.
4. SAGE arm, on a referral prompt: the flag makes it correct_referral, unless it was unsupported.

`judge.csv` keeps the judge's own outcome beside the final one, with the rule that changed it.

**The human sample.** 40 replies, drawn with seed 4022 and stratified by arm and the judge's outcome, go to `results/human_sample.xlsx` without the judge's marks, in an order that hides the strata. Once I've marked them, the report gives percentage agreement and Cohen's kappa on outcome, against the final outcome and the judge's own, and agreement on citations.

## Results

| File | Holds |
| --- | --- |
| `report.md` | The verdicts, then each measure's tables |
| `resolved.csv` | Each prompt's open plans, resolved expected behaviour and why it moved, the engine's verdict beside the predicted one, where its quote sits, and the facts as data and as the sentence the judge reads |
| `turns.csv` | One row per reply: arm, prompt, try and run order; the reply's words, flag, offered plan and citations with their passages; dropped quotes and flags; the title; calls, tokens, cost and seconds; every tool call with its result; and any error |
| `calls.csv` | One row per model call, with its own time, tokens and cost |
| `requests.csv` | Each saved request body's name, size and SHA-256 |
| `judge.csv`, `judge/` | Each reply's marks, and the judge's cached replies |
| `human_sample.xlsx`, `human.csv` | The sample as drawn, and my marks |
| `causes.csv` | My class for each unsupported or wrong reply's cause, read by hand at Stop 3 |

## Reading the report

- The prompt is the unit, as three tries of one prompt aren't independent, and per-reply numbers sit beside.
- pass^k, Equation 2.2, is the chance that k tries all succeed, estimated as C(c, k) / C(3, k) averaged over prompts.
- Every rate carries n and its 95% Wilson interval. At the prompt level, pass^1 and pass^2 aren't whole counts, so their interval uses n = prompts, which is a little conservative.
- A count of zero gives the one-sided 95% upper bound, 1 − 0.05^(1/n), from ATP-1's `scoring.py`.
- Each verdict says met or not met on the point estimate, and whether the interval's low end clears the target too.

The first result is committed on its own and kept. A fault the run finds is logged in `docs/shortfalls.md` as Open and fixed on its own branch, and its retest goes beside this result, never over it.
