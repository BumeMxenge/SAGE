# Checks the handbook reader on typed pages in the printed layout: each page's running header is
# cropped off and its number kept, a heading in larger type is a break, course entries read as
# printed, and listed prose becomes passages in printed order, one per rule clause
import pytest

from sage.ingestion.handbook import Handbook, Page, pages, passages
from sage.ingestion.sources import Section, SourceError

# The fixture's pages, as their running headers print them
NUMBERS = (48, 49, 132, 138, 164, 188, 189)


def test_a_printed_page_reads_back_below_its_running_header(
    tmp_path, handbook_pages, handbook_pdf
):
    assert pages(handbook_pdf(tmp_path / "handbook.pdf", handbook_pages)) == [
        Page(number=number, lines=tuple(body))
        for number, (_, *body) in zip(NUMBERS, handbook_pages, strict=True)
    ]


def test_a_heading_in_larger_type_is_a_break_even_at_the_top_of_a_page(
    tmp_path, handbook_pdf
):
    # The end of PHY2010S and the next department's heading, 2023 pages 193 and 194, after a cover,
    # which has no running header and so no page number
    typed = [
        ["", "UNIVERSITY OF CAPE TOWN"],
        ["193", "examination."],
        [
            "194",
            ("STATISTICAL SCIENCES", 14),
            "Associate Professor and Head of Department:",
        ],
    ]
    assert pages(handbook_pdf(tmp_path / "handbook.pdf", typed)) == [
        Page(number=193, lines=("examination.",)),
        Page(
            number=194,
            lines=(
                "",
                "STATISTICAL SCIENCES",
                "Associate Professor and Head of Department:",
            ),
        ),
    ]


@pytest.mark.parametrize(
    ("code", "read", "last_line"),
    [
        # A title over two lines, and no requirement line
        (
            "EEE2048S",
            {
                "codes": ("EEE2048S",),
                "name": "Professional Communication for Electrical Engineering",
                "credits": 8,
                "nqf_level": 6,
                "term": None,
                "convener": "Ms T Moodley",
                "requirement": None,
                "corequisite": None,
                "page": 132,
            },
            "for this course.",
        ),
        # One entry for both terms, a note under the title, and a requirement whose second line
        # opens with a code
        (
            "EEE4022S",
            {
                "codes": ("EEE4022F", "EEE4022S"),
                "name": "Research Project",
                "credits": 40,
                "nqf_level": 8,
                "term": None,
                "convener": "Associate Professor S Chowdhury",
                "requirement": (
                    "EEE4114F or EEE4126F or EEE4117F or EEE4118F or EEE4121F or EEE4120F or "
                    "EEE4119F"
                ),
                "corequisite": None,
                "page": 138,
            },
            "for this course.",
        ),
        # The entry ends at the break after its assessment, before the next section's heading
        (
            "CML4607F",
            {
                "codes": ("CML4607F",),
                "name": "Law for Engineers",
                "credits": 10,
                "nqf_level": 8,
                "term": None,
                "convener": "B Zungu",
                "requirement": (
                    "This course is only available to BSc(Eng) Electrical Engineering; BSc(Eng) "
                    "Electrical and Computer Engineering and BSc(Eng) Mechatronics students."
                ),
                "corequisite": None,
                "page": 164,
            },
            "Assessment: Assignment (20%), Class test (20%), Exam (60%)",
        ),
        # A printed term and a co-requisite, and an assessment that carries on over the page
        (
            "PHY1013S",
            {
                "codes": ("PHY1013S",),
                "name": "Physics B for Engineers",
                "credits": 18,
                "nqf_level": 5,
                "term": "sem2",
                "convener": "D R Geduld",
                "requirement": "PHY1012F/S or PHY1014F/S",
                "corequisite": "MAM1020F (or equivalent)",
                "page": 188,
            },
            "a mandatory pre-supp tutoring and revision programme.",
        ),
    ],
)
def test_an_entry_reads_as_printed(handbook, code, read, last_line):
    entry = handbook.entry(code)
    assert entry.model_dump(exclude={"content"}) == read
    # It runs from its heading to its last printed line
    lines = entry.content.splitlines()
    assert lines[0].startswith(code[:7])
    assert lines[-1] == last_line


def test_a_line_of_prose_opening_with_a_code_is_not_a_heading():
    # APG2021W's entry (2026, page 78), shortened, with a line under its heading that opens with the
    # codes of its semester versions
    lines = (
        "APG2021W TECHNOLOGY II",
        "APG2021F/S versions are available for Semester Abroad students only.",
        "20 NQF credits at NQF level 6; Site visits, tutorials. Second year undergraduate.",
        "Convener: TBA",
        "Course entry requirements: APG1003W",
        "Co-requisites: APG2038W, APG2039W",
        "Course outline:",
        "Understanding materials, components, assembly systems, and generic details.",
        "Assessment: Please refer to the official course handout document.",
    )
    book = Handbook([Page(number=78, lines=lines)])
    entry = book.entry("APG2021W")
    assert (entry.codes, entry.name, entry.credits, entry.requirement) == (
        ("APG2021W",),
        "Technology II",
        20,
        "APG1003W",
    )
    assert book.entry("APG2021F") is book.entry("APG2021S") is None


@pytest.mark.parametrize(
    ("lines", "refusal"),
    [
        (
            (
                "EEE3100S ENERGY SYSTEMS AND GRIDS I",
                "16 NQF credits at NQF level 7",
                "Assessment: Please refer to the official course handout document.",
                "",
                "EEE3100S ENERGY SYSTEMS AND GRIDS I",
                "16 NQF credits at NQF level 7",
                "Assessment: Please refer to the official course handout document.",
            ),
            "EEE3100S has an entry on each of pages 138, 138",
        ),
        (
            ("EEE3100S ENERGY SYSTEMS AND GRIDS I", "16 NQF credits at NQF level 7"),
            "EEE3100S's entry on page 138 prints no Assessment line",
        ),
    ],
)
def test_an_entry_the_reader_cannot_place_is_refused(lines, refusal):
    with pytest.raises(SourceError, match=refusal):
        Handbook([Page(number=138, lines=lines)]).entry("EEE3100S")


def test_listed_prose_becomes_passages_one_per_rule_clause_in_printed_order():
    # The foot of 2026's page 10, where two listed sections share the page; 2023's FB3.2, whose
    # text ends by naming FB3.1 again; and 2026's FB8.10, whose heading opens a page above its
    # number, with no break after the page before
    book = Handbook(
        [
            Page(
                number=10,
                lines=(
                    "Lecture timetable",
                    "The lecture timetables are published separately by the department concerned from where they are",
                    "obtainable at Registration.",
                    "",
                    "Key to Course Abbreviations, Codes and Terminology Guide to the Credit System",
                    "",
                    "Course Codes",
                    "",
                    "ACC Accounting",
                ),
            ),
            Page(
                number=14,
                lines=(
                    "RULES FOR UNDERGRADUATE DEGREES",
                    "The rules must be read together with the general rules for degrees and diplomas in Handbook 3 of this",
                    "series.",
                    "",
                    "FB3.2 Candidates must complete approved courses of not less than 576 credits in the case",
                    "of the degrees which have a minimum duration of 4 years and not less than 432",
                    "credits in the case of degrees which have a minimum duration of 3 years. Rule",
                    "FB3.1 above also applies.",
                ),
            ),
            Page(
                number=18,
                lines=(
                    "BSc(Eng) Electrical Engineering, Electrical and Computer Engineering, Mechatronics Engineering",
                    "candidates (4-year curriculum) (EB009, EB022, EB011)",
                    "FB8.10 Except by permission of the Senate candidates may not renew their registration if:",
                ),
            ),
        ]
    )
    units = book.prose(
        [
            Section(section="Lecture timetable", pages=(10, 10)),
            Section(section="Course Codes", pages=(10, 10)),
            Section(section="Rules for Undergraduate Degrees", pages=(14, 18)),
        ]
    )
    # Passages are numbered by where they're printed, whatever order they arrive in
    read = passages(units[::-1], 2026, "A made-up handbook")
    assert [
        (
            p.position,
            p.section,
            p.page,
            p.content.split("\n")[0],
            p.content.split("\n")[-1],
        )
        for p in read
    ] == [
        (
            1,
            "Lecture timetable",
            10,
            "Lecture timetable",
            "Key to Course Abbreviations, Codes and Terminology Guide to the Credit System",
        ),
        (2, "Course Codes", 10, "Course Codes", "ACC Accounting"),
        (
            3,
            "Rules for Undergraduate Degrees",
            14,
            "RULES FOR UNDERGRADUATE DEGREES",
            "series.",
        ),
        (
            4,
            "FB3.2",
            14,
            "FB3.2 Candidates must complete approved courses of not less than 576 credits in the case",
            "FB3.1 above also applies.",
        ),
        (
            5,
            "FB8.10",
            18,
            "BSc(Eng) Electrical Engineering, Electrical and Computer Engineering, Mechatronics Engineering",
            "FB8.10 Except by permission of the Senate candidates may not renew their registration if:",
        ),
    ]
    # A passage's id comes from what it holds, so a second read gives the same ids, and each is its
    # own
    assert passages(units, 2026, "A made-up handbook") == read
    assert len({p.id for p in read}) == len(read)


def test_a_section_ends_at_the_heading_its_manifest_names():
    # 2026's page 61, shortened, where the department's programmes end partway down the page, at
    # the access route for transferees
    book = Handbook(
        [
            Page(
                number=61,
                lines=(
                    "graduates of the Mechanical Engineering programme.",
                    "",
                    "Electrical Engineering",
                    "The last line of the department's programmes.",
                    "",
                    "Access for University of Technology Transferees",
                    "Transferees may be admitted to the second year.",
                ),
            )
        ]
    )
    until = "Access for University of Technology Transferees"
    section = Section(section="Electrical Engineering", pages=(61, 61), until=until)
    assert book.text(book.section(section)) == (
        "Electrical Engineering\nThe last line of the department's programmes."
    )
    # A heading the page doesn't print stops the run
    with pytest.raises(SourceError, match="No heading 'Civil Engineering' between"):
        book.section(Section(section="Civil Engineering", pages=(61, 61)))
