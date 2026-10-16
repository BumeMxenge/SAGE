<!-- My judgement calls in E2's labels, by labels.csv's spreadsheet row, for Chapter 3 to cite -->
# Judgement calls in the labels

I wrote every tree in [labels.csv](labels.csv) from print, by the rules in [prompt.md](../prompt.md). The rows below needed a judgement the rules don't settle on their own. Row numbers are labels.csv's spreadsheet rows, with the header as row 1.

The `printed` column is empty on every row: I checked each string against the PDF, and the extraction matched print everywhere.

- **8, APG2015F.** A programme outside the six curricula is a refer leaf, with the courses beside it (rules 6 and 8).
- **12, APG2026F/S.** Each programme's sentence is its own branch, joined by any, since no student is on both programmes.
- **24, APG3016C.** The Geomatics extra applies to some students only, so the conditional sentence is one refer, as in the CSC2004Z example.
- **33, APG3034Z.** "/" between two full codes is read as or. APG2038W has no 2026 entry, and APG2043F, Environment & Services I, replaced it.
- **42, APG4003Z.** Being able to graduate that year isn't a year of study, so refer.
- **46, APG4012S.** Kept as refer rather than null under rule 9. The ASPECT sentence makes the final-year intention a restriction with an exception, consistent with rows 42 and 59.
- **56, CIV3048F and CIV3049S.** "n/a" holds no requirement, so null.
- **58, CIV4035C.** The prose part is a refer, and the listed courses are leaves.
- **59, CIV4041F.** A potential qualifier isn't a year of study, so refer.
- **60, CIV4044F.** Two prose conditions, so two refers.
- **62, MEC2048S.** The print has a stray bracket. Read as two old and new pairs, MEC2025F or MEC2049F and MEC2042F or MEC2046F, as MEC3076F prints them.
- **75, MEC3083W.** "AYOS 3" is read as min_year_of_study 3.
- **76, MEC4047F, and 79, MEC4124W.** Mixed and/or is read by meaning (rule 3). In both, or joins a code with no 2026 entry to the course that replaced it, so the groupings differ.

The code column names APG2021F (rows 10 and 11) and APG2039F (rows 14 and 15), where the entries are APG2021W and APG2039W. The extractor took each code from a line such as "APG2021F/S versions are available for Semester Abroad students only", not from the heading above it. The strings and pages are right, and E2 scores strings, not codes, so the column stays as it is.
