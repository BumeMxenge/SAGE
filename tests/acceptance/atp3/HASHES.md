<!-- The SHA-256 of every ATP-3 input, recorded after the inputs' commit and before any model call -->
# ATP-3 input hashes

Recorded on 26 October 2026, after the inputs' commit (c119f78) and before any model call. `shasum -a 256` on each file, from this folder, gives the same value.

| File | SHA-256 |
| --- | --- |
| `prompts.csv` | `af80ec46d16c50307642e61bb1c1e2642e5d8e29899e7b1dfdc7ce6fa8ff5488` |
| `students/signals1-failed.json` (R1) | `8952e577812f3f94dc652e0c19fbd3bb740b9bd11b38805e2cee098f8777824b` |
| `students/embedded1-failed.json` (R4) | `5fa6dc0abb358189256ab108c93f23cf45da385b99907f88a8a7f0e3f1bd5b2e` |
| `students/aspect-final-supp.json` (R5) | `cc3b0c973e153ba23267c5e1bb18152e321e89bf521bb670ffe6af5574bad24b` |
| `control_prompt.md` | `37407ba514eef68cf6928426f899703035ea60b48d58aee4ee335dcde9045165` |
| `judge_prompt.md` | `b60b5736c9d068207448b7cdcba1edbf4cddaae31e52920a8ef1db181fc40af8` |

`results/resolved.csv`, committed with this file, fixes every prompt's expectation from the engine and the plan data before the run.
