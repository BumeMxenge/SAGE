<!-- What ATP-4's harness checks, how to run it, and how to read its report -->
# ATP-4: context consistency

ATP-4 asks whether the plan on screen, the chat and the advisor's context stay in step after switches, reloads and late replies (NF-3), and shows the test can fail by catching a planted fault. It calls no model: the advisor is a fake, and the API's OpenAI key is a stand-in.

## How it runs

`make atp4` runs `run.sh`, which needs Docker and local Supabase running, and ports 8001 and 3001 free. It leaves `~/SAGE`'s own servers on 8000 and 3000 alone.

1. `serve.py` starts SAGE's API on 8001, as `create_app()` builds it, with only `deps.advisor` overridden. Sign-in, the chats service and local Supabase are the real ones.
   - The fake advisor sleeps for the delay a question names, such as `[d=3.2]`, then replies with the question's id and the names of the chat's plan or pair, as the chat it was handed holds them.
   - `[offer]` makes it offer her first hidden plan by id, as a reply offers one.
   - It refuses to start unless Supabase is local and the OpenAI key is the stand-in.
2. Vite serves this worktree's frontend on 3001, with `VITE_API_URL` pointing at 8001.
3. `student.py create` makes Qhawe Vantrel (VNTQHA999), Mbali's record under a local account of her own, without Mbali's chats. Her seven shown plans and three hidden ones are Mbali's.
4. `drive.mjs` plays the six scenarios ten times each in a real browser, through the frontend's own Playwright, and writes what each run saw to `results/observations.json`.
5. `run.sh` applies `planted-fault.patch`, drives S1 and S5 ten times each again into `results/planted.json`, then reverts the patch.
6. `check.py` writes `results/runs.csv`, and `report.py` writes `results/report.md` from it.

Whatever happens, the script reverts the patch, deletes the student and stops both servers before it exits.

## The scenarios

Each run draws a delay of 0 to 8 s and a switch time inside it, from seed 4022. A question carries its run's id, such as `[S1-03-1]`, so no check confuses one run's exchange with another's. Each run asks in a new chat.

| Scenario | What the run does |
| --- | --- |
| S1 | Asks on her first plan, switches to her second at the switch time, then switches back and reloads |
| S2 | Switches to her second plan, then asks, then reloads |
| S3 | Compares her first plan with the one Compare picks, then asks, then reloads |
| S4 | Asks, reloads at the switch time, waits for the API to hold the reply, reads the screen she sees after that reload, then reloads again. The first screen counts, as it's what she sees (my decision before the run): a run whose screen lacks the exchange is inconsistent, with the cause "stale after a mid-reply reload" |
| S5 | Two tabs, on her first and second plans, ask at once, each with its own delay, then both reload |
| S6 | Asks with `[offer]`, presses Open Plan on the hidden plan the reply offers, then reloads. Her answers' plans are hidden again before the next run |

After every switch, Compare or Open Plan, the driver waits until the rail names the new plan or pair before it acts, as a person acts on what the screen shows. During a switch the address moves first, and the old plan stays on screen until the new one is drawn: in a trial run, a question sent in that moment went to the old plan's chat. After 15 s the driver goes on regardless, so a rail that never catches up still counts.

"Regenerate after a record change" is reported as not applicable, as version 1 allows no record change after setup.

`RUNS=1 make atp4` tries the harness out with one run a scenario. The result uses ten.

## The checks

A run is consistent when all four pass, on every screen it read and in the API:
- **in_right_chat**: each reply sits in a chat of the plan or pair it names.
- **exchanges_once**: each question sits in one chat, which holds exactly the exchanges asked in it, once each. A screen of a plan or pair the run asked in shows them, reloaded or not, and any other screen shows none.
- **address_matches_chat**: the rail names the plan or pair in the address, and the chat it shows is one of theirs.
- **plan_set_unchanged**: her plans are as they were, except that a hidden plan a reply offered joins the shown list.

A race is provoked when the switch or reload comes before the reply is saved, or, in S5, when both tabs' turns are in flight at once.

## The planted fault

`planted-fault.patch` changes only `AssistantRail.tsx` and is never committed to `src`. The assistant keeps the chat on screen in a ref, and writes each returned exchange into that chat's messages instead of refreshing the chat it was asked in. So a reply that lands after a switch shows in the wrong chat, and the right one shows nothing until a reload.
- S1 should catch it, as the switch comes before the reply.
- S5 may not: each tab keeps its own cache and never changes its open chat, so S5 guards against the server mixing two chats' replies instead.

The planted runs come after the scenarios, so her second plan already has chats for the fault to write into. They are numbered 51 to 60, with the same draws as runs 1 to 10, so their questions never match the scenarios' own, which her chats still hold.

## Results

| File | Holds |
| --- | --- |
| `observations.json`, `planted.json` | What each run saw: every screen's address, the rail's line and the conversation, and the API's chats and plan set, before and after |
| `runs.csv` | One row per run: scenario, run, delay, switch time, race provoked, each check's result and the planted-fault flag |
| `causes.csv` | My cause for each inconsistent run, read at Stop 3 from what the run saw |
| `report.md` | One row per scenario: runs, races provoked, inconsistent runs and pass^10, with the planted fault's rows beneath, then every inconsistent run with its cause |

pass^10, Equation 2.2, is the chance that ten runs all stay consistent, estimated as C(c, 10) / C(10, 10) from a scenario's ten runs, so it is 1 only when all ten are consistent.
