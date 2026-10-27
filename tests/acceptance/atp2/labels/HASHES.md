<!-- The SHA-256 of every label file and of the approved 2026 rules, recorded before ATP-2's first run -->
# Hashes before the first run

Recorded on 26 October 2026, before any record ran, from the labels as committed in 0cefd5e and the approved 2026 rules the engine and the checker read. A file changed since then gives a different hash. This command reproduces them:

```
shasum -a 256 tests/acceptance/atp2/labels/*.csv tests/acceptance/atp2/labels/*.md tests/acceptance/atp2/labels/records/*.json data/rules/2026/rulebook.json
```

It also lists this file, which isn't in the table.

| File | SHA-256 |
| --- | --- |
| `tests/acceptance/atp2/labels/README.md` | `dfd51f0d88e25b15ceb7cd34c631c4d4ad942277267192b0e2efec5830d7eb76` |
| `tests/acceptance/atp2/labels/NOTES.md` | `b152a070967c56201052328c55a33a478c9c617164e776e715a3cbe9937cc7a3` |
| `tests/acceptance/atp2/labels/REVIEW.md` | `b5ea221854a2c2408f013aa0aca3f9baf61ff32823131a77e693a93c1e33c4ea` |
| `tests/acceptance/atp2/labels/records.csv` | `9b80ae6c560014a2bee603325743ad29133650ccd8d245de50258a714abcf776` |
| `tests/acceptance/atp2/labels/decisions.csv` | `c6260a13e9dfcd4c079549dd6a46d8555f3322580e69c4800eb74ad9a0bd3263` |
| `tests/acceptance/atp2/labels/records/aspect-final-supp.json` | `cc3b0c973e153ba23267c5e1bb18152e321e89bf521bb670ffe6af5574bad24b` |
| `tests/acceptance/atp2/labels/records/aspect-maths-physics.json` | `58843f79e2423fddcf498c6710452a663bce68a8b82a9a3f3d2f8059852ff730` |
| `tests/acceptance/atp2/labels/records/embedded1-failed.json` | `5fa6dc0abb358189256ab108c93f23cf45da385b99907f88a8a7f0e3f1bd5b2e` |
| `tests/acceptance/atp2/labels/records/owes-asl-dp-refused.json` | `93dc4f57c9377a973d6664668bc8bb34dc60fa7e0b0d913ad43a8907afc99448` |
| `tests/acceptance/atp2/labels/records/power-repeat-clash.json` | `ecfdc9ef75259f0e95e3449e611593792c1de9c04f63cdf72d88342d5dd8bbe3` |
| `tests/acceptance/atp2/labels/records/signals1-failed.json` | `8952e577812f3f94dc652e0c19fbd3bb740b9bd11b38805e2cee098f8777824b` |
| `data/rules/2026/rulebook.json` | `0b0c2a40e1c1599a644be58097714cc0f875098026b0ffec87900e40d033191d` |
