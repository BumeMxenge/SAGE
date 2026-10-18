<!-- How to fill ATP-1's label sheets from print, and check each one before it's committed -->
# ATP-1 label sheets

ATP-1 measures how well ingestion reads the printed sources, so its answers come from print alone: the handbooks, and the workbooks as Excel shows them, never anything SAGE produced. Each sheet was made naming only what to label, with every value blank, and filled from print by hand. Once a sheet was filled and passed the check, it was committed on its own, before anything ran against it.

The filled sheets were checked against print by an AI assistant (Claude). It changed four complementary page numbers, to the heading-page rule below, and one line break in a requirement's text. No tree, time, day or code changed. It also labelled the 60 timetable cells on its own, and its reading agreed with the committed labels on every field.

| Sheet | Rows | Label from |
| --- | --- | --- |
| `courses_2026.xlsx` | 60 courses: every one the six Electrical Engineering curricula print | `data/sources/2026/EBE_2026.pdf` |
| `courses_2023.xlsx` | 65 courses, the same for 2023 | `data/sources/2023/EBE_2023.pdf` |
| `timetable.xlsx` | 60 of the 785 timetable cells that name a course | `data/sources/2026/2026_timetable.xlsx`, in Excel |
| `complementary.xlsx` | 40 of the 173 rows of the complementary workbook's Meetings sheet | the faculty handbooks |
| `held_out.xlsx` | all 56 Chemical Engineering and Construction Economics entries, less three already seen | `data/sources/2026/EBE_2026.pdf` |

Each sheet's About tab says how its rows were found, in which file (with its SHA-256), and the seed of its draw if it has one.

## Filling a sheet

- Leave the first columns alone: they name the row. Fill the rest from print.
- Columns with a fixed list have a dropdown. Note is never checked, so use it for anything print leaves unclear.
- Pages are the numbers printed at the top of each page. The PDFs count from the cover, so printed page 131 is the viewer's page 132.
- Paste a printed requirement into the formula bar, or double-click the cell first. Pasted onto a selected cell, a requirement over several lines spreads down the rows below.
- Times are HH:MM, such as 08:00.

### courses_2026.xlsx and courses_2023.xlsx

- **Title, Credits, NQF level:** from the entry's heading and its "NQF credits at NQF level" line. Copy the title as printed, capitals included, and join a title that wraps with a space.
- **Term:** the term the code's last letter gives by the book's key (2026 p. 11, 2023 p. 12): F sem1, S sem2, H and W full_year, A to D q1 to q4, L winter, U, J and P summer, and M, X and Z other.
- **Requirement:** what follows "Course entry requirements:", as printed, or None when the entry prints none. **Co-requisite:** what follows "Co-requisites:", or blank.
- **Requirement tree, Co-requisite tree:** each one's tree (see Trees), or null where the print holds no requirement. Leave it blank when its text is None or blank.
- A row with no page is a course a curriculum lists but the book never describes. It holds "no entry printed" in Note, and the rest stays blank.

### timetable.xlsx

- Open `data/sources/2026/2026_timetable.xlsx` in Excel, go to the sheet and cell, and label what Excel shows.
- **Course:** every course the cell names, as full codes separated by commas: EEE3097/8S is EEE3097S, EEE3098S.
- **Section:** the section numbers the cell shows, if any.
- **Day, Start, End, Term:** when the meeting runs, with Term the one the sheet places the cell in. A cell merged over several periods runs from the first one's start to the last one's end. The 2026 handbook gives the periods on p. 10: period 1 is 08:00 to 08:45, each later one starts on the hour and lasts 45 minutes, and the meridian, 13:00 to 14:00, sits between periods 5 and 6.
- **Kind:** from the dropdown, and blank when the cell's own text shows none, on the Labs sheet too.
- A cell that names a course but isn't a meeting, such as a note, gets Course only.

### complementary.xlsx

- **Row** is the row in the Meetings sheet of `data/sources/2026/2026_Complementary_Studies_Course_Details.xlsx`, and **Place** its place among its course's rows: 2 of 3 is the second of three.
- Find the course's printed entry first, and use Place to tell which printed meeting the row stands for. Look at the row itself only if that's still unclear.
- **Days:** every day print gives, as weekday names separated by commas, or blank if it gives none.
- **Start, End:** as print gives them, both or neither.
- **Kind:** from the dropdown.
- **Book, Page:** the handbook you read it in, by its cover title, and the printed page of the entry's heading, as on the courses sheets. A meeting printed only in a schedule table, such as GEO1009F's practicals, takes the table's page.
- **Ambiguous:** yes where print can be read more than one way, such as the ECO slots. Label the documented reading and say why in Note.

### held_out.xlsx

- **Code** is each entry's heading as printed, and **Page** its page.
- **Requirement, Co-requisite** and their trees as on the courses sheets.

## Trees

Trees follow the labelling conventions in E2's [prompt.md](../../../../experiments/ingestion/requirement-parsing/prompt.md), so E2's labels and ATP-1's follow one set of rules.

A cell holds the tree itself, not the `{"rule": ...}` the models answer with, and null stands for a rule of null. Each tree is JSON in the seed's shape, which `EntryRule` in `backend/src/sage/domain/rules.py` defines. One example of each leaf, with made-up codes:

| Leaf | Tree |
| --- | --- |
| A pass | `{"course": "ABC1001F", "need": "pass"}` |
| A co-requisite | `{"course": "ABC1002F", "need": "concurrent"}` |
| A mark threshold | `{"course": "ABC2001F", "need": "mark", "min_mark": 50}` |
| any | `{"any": [{"course": "ABC1001F", "need": "pass"}, {"course": "ABC1001S", "need": "pass"}]}` |
| all | `{"all": [{"course": "ABC1001F", "need": "pass"}, {"course": "XYZ1003S", "need": "pass"}]}` |
| student_in | `{"student_in": ["EB000ABC01"]}` |
| min_year_of_study | `{"min_year_of_study": 3}` |
| refer | `{"refer": "the printed words, copied exactly"}` |

## Checking a sheet

From the repo root, name the sheets to check:

```
uv run --project backend python tests/acceptance/atp1/labels/check_labels.py tests/acceptance/atp1/labels/courses_2026.xlsx
```

It lists every row whose labels are missing or malformed, and passes only when there are none. It checks each tree with `EntryRule` alone, never the grammar. It also refuses what `EntryRule` lets through but would later count against SAGE: a course leaf that isn't a full code, and the shapes rule 10 of `prompt.md` forbids.

## How the rows were found

`make_sheets.py` made the sheets from the sources alone and printed nothing. It writes only what names each row, never a value to label, and uses none of SAGE's readers, grammar or output. The timetable and complementary rows are seeded draws (seed 4022); the other sheets list their whole population. To check a draw, run it into an empty folder and compare the rows:

```
uv run --project backend python tests/acceptance/atp1/labels/make_sheets.py <empty folder>
```

It refuses to write over a sheet, so a rerun can't wipe labels.

## Scoring

The harness scores SAGE against these labels by these rules, set before its first run.

- **Titles** match ignoring case, as SAGE title-cases names.
- **Trees.** A label's Requirement tree and Co-requisite tree are joined in an all, as SAGE stores one entry rule per course. A tree left blank or null adds nothing, so a course with one tree keeps it alone. Both sides are compared in the normal form of `normal` in E2's [score.py](../../../../experiments/ingestion/requirement-parsing/score.py).
- **Timetable.** Section isn't scored, as SAGE doesn't store it. Kind is scored only where a label gives one.
- **Complementary.** Each Book's cover title maps to the workbook's handbook name, and each day name to the workbook's mon to fri. A Page matches if it falls within the course's printed pages in the workbook.
- **Headline.** `held_out.xlsx` is the headline result for requirement trees. The course sheets are an in-sample check, as the grammar was written from their fields.
- **Judgement calls.** A row is a judgement call when its Note holds anything but "no entry printed", or Ambiguous is yes. Each table is reported with and without those rows.
