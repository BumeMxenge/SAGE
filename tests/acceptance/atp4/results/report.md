# ATP-4: context consistency

report.py wrote this from runs.csv, one row per run. Each scenario ran ten times, with delays of 0 to 8 s and switch times drawn inside them from seed 4022. A run is consistent when all four checks pass: each reply sits in the chat of the plan or pair it names, each chat holds exactly its own exchanges once each, after a reload too, the address's plan matches the chat's, and her plan set is unchanged except that a hidden plan offered by Open Plan joins the shown list. pass^10 is the chance that ten runs all stay consistent, Equation 2.2's estimate from the scenario's runs.

## The scenarios as built

| Scenario | Runs | Races provoked | Inconsistent runs | pass^10 | What failed |
| --- | --- | --- | --- | --- | --- |
| S1: Ask, then switch plan before the reply | 10 | 9 | 0 | 1.00 | nothing |
| S2: Switch plan, then ask | 10 | 0 | 0 | 1.00 | nothing |
| S3: Compare two plans, then ask | 10 | 0 | 0 | 1.00 | nothing |
| S4: Reload mid-reply | 10 | 10 | 6 | 0.00 | a chat not holding exactly its own exchanges, once each |
| S5: Two tabs ask on different plans at once | 10 | 10 | 0 | 1.00 | nothing |
| S6: Press Open Plan on a hidden plan a reply offers | 10 | 0 | 0 | 1.00 | nothing |

Regenerate after a record change: not applicable, as version 1 allows no change to her record after setup.

## The planted fault

planted-fault.patch makes the assistant write each returned exchange into whichever chat is open when it lands. With it applied, S1 and S5 ran ten times each again, with the same delays and switch times.

| Scenario | Runs | Races provoked | Inconsistent runs | pass^10 | What failed |
| --- | --- | --- | --- | --- | --- |
| S1: Ask, then switch plan before the reply | 10 | 10 | 10 | 0.00 | the address's plan not matching the chat's; a chat not holding exactly its own exchanges, once each; a reply outside the chat of the plan or pair it names |
| S5: Two tabs ask on different plans at once | 10 | 10 | 0 | 1.00 | nothing |

The test caught it: 10 inconsistent runs, in S1.
