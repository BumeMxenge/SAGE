# Checks the handbook reader on typed pages in the printed layout: each page's running header is
# cropped off and its number kept, a heading in larger type is a break, and course entries read as
# printed
import pytest
from fpdf import FPDF

from sage.ingestion.handbook import Handbook, Page, pages
from sage.ingestion.sources import SourceError

# The fixture's pages, as their running headers print them
NUMBERS = (132, 138, 164, 188, 189)


def printed(tmp_path, typed):
    # Sets each typed page as the handbook does: its first line as the running header at the top, the
    # rest from 60 points down in 8-point type, with a blank line as a gap. A (text, size) pair is set
    # in that size. A4, so the longest typed line fits.
    pdf = FPDF(unit="pt", format="A4")
    pdf.set_auto_page_break(False)
    for header, *body in typed:
        pdf.add_page()
        pdf.set_font("Helvetica", size=8)
        if header:
            pdf.set_xy(36, 28)
            pdf.cell(text=header)
        pdf.set_y(60)
        for line in body:
            text, size = line if isinstance(line, tuple) else (line, 8)
            pdf.set_font("Helvetica", size=size)
            if text:
                pdf.cell(h=size + 1, text=text, new_x="LMARGIN", new_y="NEXT")
            else:
                pdf.ln(9)
    path = tmp_path / "handbook.pdf"
    pdf.output(str(path))
    return path


@pytest.fixture
def handbook(handbook_pages):
    return Handbook(
        [
            Page(number=number, lines=tuple(body))
            for number, (_, *body) in zip(NUMBERS, handbook_pages, strict=True)
        ]
    )


def test_a_printed_page_reads_back_below_its_running_header(tmp_path, handbook_pages):
    assert pages(printed(tmp_path, handbook_pages)) == [
        Page(number=number, lines=tuple(body))
        for number, (_, *body) in zip(NUMBERS, handbook_pages, strict=True)
    ]


def test_a_heading_in_larger_type_is_a_break_even_at_the_top_of_a_page(tmp_path):
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
    assert pages(printed(tmp_path, typed)) == [
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


def test_a_requirement_line_opening_with_a_code_is_not_an_entry(handbook):
    # EEE4022S's requirement carries on with "EEE4120F or EEE4119F", and EEE4120F's own entry isn't
    # among these pages
    assert handbook.entry("EEE4120F") is None


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
