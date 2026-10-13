<!-- The prompt E2 sends both models, which is also the labelling guide for E2 and ATP-1 -->
# Reading a printed requirement

These rules are also the labelling guide. Every label in E2's sheet and in ATP-1's requirement sheets follows them, so a label and a model's draft are written to one set of rules. The drafter sends the models everything after the line below, unchanged. Its examples come only from the development fields, the strings the grammar was written from.

---

You turn one printed course requirement from the University of Cape Town's Engineering & the Built Environment undergraduate handbook into a rule tree that a planning tool can check.

You get the field's name and its text, as printed:
- "Course entry requirements": what a student needs before taking the course.
- "Co-requisites": courses the student must take alongside it, or have passed before.

Answer with {"rule": <tree>}, or {"rule": null} where the field prints "None" or holds no requirement.

## The tree

A tree is one node, and each node is one of these:
- {"all": [<node>, ...]}: every child must hold.
- {"any": [<node>, ...]}: at least one child must hold.
- {"course": "EEE3091F", "need": "pass"}: a pass in the course.
- {"course": "MAM2084F", "need": "concurrent"}: the course taken alongside, or passed before.
- {"course": "CSC2001F", "need": "mark", "min_mark": 45}: a final mark of at least min_mark in the course, pass or not.
- {"student_in": ["EB009EEE01", ...]}: the student is on one of these curricula.
- {"min_year_of_study": 3}: the student is in this year of study or a later one.
- {"refer": "<printed words>"}: a condition only a person can judge, holding the printed words for that part.

## How to read the print

1. In "Course entry requirements", course leaves need "pass". In "Co-requisites", they need "concurrent". Wherever else the print asks for a course taken alongside, its leaf needs "concurrent" too.
2. A course code is three letters, four digits and a term letter, such as EEE3091F. A code followed by other term letters, such as MAM1021F/S or MAM1024S/F, means the course in any of those terms: an any of each term's code.
3. "and", commas and semicolons join parts into an all, and "or" joins them into an any. Brackets group. Where "and" and "or" are mixed with no brackets, choose the reading the handbook means.
4. A final-mark threshold, such as "at least 45% for CSC2001F", is a mark leaf, and so is a pass with at least a given mark.
5. A year of study, such as "fourth year of study", is min_year_of_study.
6. A condition on the student's programme is student_in only when it names programmes among the six curricula below, listing every curriculum it names. Any other programme condition is a refer leaf.
7. "or equivalent" is an any of the named course and a refer leaf holding "or equivalent".
8. Anything else the nodes can't express, such as a school result (NSC, A-level), a DP (duly performed certificate), permission, a condition in prose, or a code printed without its term letter, is a refer leaf for that part, beside the parts that can be checked.
9. Words that only describe the course, give advice or state a preference aren't a requirement, so leave them out. If nothing is left, the rule is null.
10. Don't put an all directly inside an all, or an any directly inside an any: join them. Don't give an all or an any only one child.

The six curricula:

| Code | Curriculum |
| --- | --- |
| EB009EEE01 | BSc(Eng) Electrical Engineering, 4-year |
| EB809EEE01 | BSc(Eng) Electrical Engineering, 5-year |
| EB022EEE02 | BSc(Eng) Electrical and Computer Engineering, 4-year |
| EB822EEE02 | BSc(Eng) Electrical and Computer Engineering, 5-year |
| EB011EEE05 | BSc(Eng) Mechatronics, 4-year |
| EB811EEE05 | BSc(Eng) Mechatronics, 5-year |

## Examples

Course entry requirements: EEE3092F or EEE3094S
{"rule": {"any": [{"course": "EEE3092F", "need": "pass"}, {"course": "EEE3094S", "need": "pass"}]}}

Course entry requirements: MAM1021F/S, PHY1012F/S and MEC1009F/S
{"rule": {"all": [{"any": [{"course": "MAM1021F", "need": "pass"}, {"course": "MAM1021S", "need": "pass"}]}, {"any": [{"course": "PHY1012F", "need": "pass"}, {"course": "PHY1012S", "need": "pass"}]}, {"any": [{"course": "MEC1009F", "need": "pass"}, {"course": "MEC1009S", "need": "pass"}]}]}}

Course entry requirements: (CSC1015F/S and CSC1016S) or (CSC1010H and CSC1011H)
{"rule": {"any": [{"all": [{"any": [{"course": "CSC1015F", "need": "pass"}, {"course": "CSC1015S", "need": "pass"}]}, {"course": "CSC1016S", "need": "pass"}]}, {"all": [{"course": "CSC1010H", "need": "pass"}, {"course": "CSC1011H", "need": "pass"}]}]}}

Course entry requirements: PHY1012F/S and PHY1013F/S; or PHY1014F/S and PHY1015F/S. MAM2083F/S.
{"rule": {"all": [{"any": [{"all": [{"any": [{"course": "PHY1012F", "need": "pass"}, {"course": "PHY1012S", "need": "pass"}]}, {"any": [{"course": "PHY1013F", "need": "pass"}, {"course": "PHY1013S", "need": "pass"}]}]}, {"all": [{"any": [{"course": "PHY1014F", "need": "pass"}, {"course": "PHY1014S", "need": "pass"}]}, {"any": [{"course": "PHY1015F", "need": "pass"}, {"course": "PHY1015S", "need": "pass"}]}]}]}, {"any": [{"course": "MAM2083F", "need": "pass"}, {"course": "MAM2083S", "need": "pass"}]}]}}

Course entry requirements: MEC1009F/S and MEC2023F/S or MEC2047F/S
{"rule": {"all": [{"any": [{"course": "MEC1009F", "need": "pass"}, {"course": "MEC1009S", "need": "pass"}]}, {"any": [{"course": "MEC2023F", "need": "pass"}, {"course": "MEC2023S", "need": "pass"}, {"course": "MEC2047F", "need": "pass"}, {"course": "MEC2047S", "need": "pass"}]}]}}

Co-requisites: MAM2084F/S.
{"rule": {"any": [{"course": "MAM2084F", "need": "concurrent"}, {"course": "MAM2084S", "need": "concurrent"}]}}

Co-requisites: MAM1020F (or equivalent)
{"rule": {"any": [{"course": "MAM1020F", "need": "concurrent"}, {"refer": "or equivalent"}]}}

Course entry requirements: CSC2001F (At least 45% for CSC2001F)
{"rule": {"course": "CSC2001F", "need": "mark", "min_mark": 45}}

Course entry requirements: CSC1015F (or at least 60% for CSC1017S)
{"rule": {"any": [{"course": "CSC1015F", "need": "pass"}, {"course": "CSC1017S", "need": "mark", "min_mark": 60}]}}

Course entry requirements: Students must be in their fourth year of study.
{"rule": {"min_year_of_study": 4}}

Course entry requirements: This course is only available to BSc(Eng) Electrical Engineering; BSc(Eng) Electrical and Computer Engineering and BSc(Eng) Mechatronics students.
{"rule": {"student_in": ["EB009EEE01", "EB809EEE01", "EB022EEE02", "EB822EEE02", "EB011EEE05", "EB811EEE05"]}}

Course entry requirements: This course is for non-Humanities students only and does not count towards Humanities degrees.
{"rule": {"refer": "This course is for non-Humanities students only"}}

Course entry requirements: A pass in NSC Mathematics with at least 70%, or at least a D symbol at A-level.
{"rule": {"refer": "A pass in NSC Mathematics with at least 70%, or at least a D symbol at A-level."}}

Course entry requirements: At least 70% for NSC Mathematics. Students registered for this course will be assessed in week 5; if it is judged that they are not coping with the level and pace of the course, and would benefit from an opportunity to strengthen foundational concepts and learn new material at a slower pace, they will be required to transfer to CSC1010H from week 7.
{"rule": {"refer": "At least 70% for NSC Mathematics."}}

Course entry requirements: CSC2001F, CSC2002S. CSC2004Z is required if CSC2002S was passed after 2017.
{"rule": {"all": [{"course": "CSC2001F", "need": "pass"}, {"course": "CSC2002S", "need": "pass"}, {"refer": "CSC2004Z is required if CSC2002S was passed after 2017."}]}}

Course entry requirements: MAM1023 and MAM1024
{"rule": {"refer": "MAM1023 and MAM1024"}}

Co-requisites: None
{"rule": null}
