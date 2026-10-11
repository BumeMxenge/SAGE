# Checks the transcript reader on the made-up fixture in the real layout: Mbali's record reads back as
# her seeded history, each kind of wrong file gets its own refusal, and a guess is always flagged
import re
from datetime import date
from uuid import UUID

import pytest
from fpdf import FPDF

from sage.domain.errors import (
    NoCourseHistory,
    NotATranscript,
    TranscriptIncomplete,
    TranscriptNotYours,
    TranscriptUnreadable,
)
from sage.domain.students import CourseHistoryLine
from sage.ingestion.transcript import BEGINNING, ROW, pdf_pages, read_lines
from sage.services.seed import load_seed

MBALI = "DLMMBA999"


def replace(pages: list[list[str]], old: str, new: str) -> None:
    # Swaps one printed line, in place
    for page in pages:
        if old in page:
            page[page.index(old)] = new
            return
    raise AssertionError(f"no line {old!r}")


def year_of(transcript, year: int):
    return [line for line in transcript.lines if line.academic_year == year]


def test_the_fixture_reads_as_her_seeded_history(transcript_pages, seed_file):
    transcript = read_lines(transcript_pages, MBALI)
    account = UUID(int=1)
    read = [
        CourseHistoryLine(
            student_id=account,
            **line.model_dump(exclude={"result_printed", "unverified"}),
        )
        for line in transcript.lines
    ]
    seeded = load_seed(seed_file, account).student.course_history
    assert len(read) == len(seeded) == 34
    assert set(read) == set(seeded)
    assert not any(line.unverified for line in transcript.lines)
    assert transcript.programme == "Bachelor of Science in Engineering in Mechatronics"
    assert transcript.issued_on == date(2026, 2, 5)
    assert transcript.warnings == ()


def test_a_generated_pdf_reads_back_line_for_line(transcript_pages, pdf_of):
    assert pdf_pages(pdf_of(transcript_pages)) == transcript_pages


def test_a_latest_year_with_results_to_come_is_in_progress(transcript_pages):
    # 2026 in progress: rows print only a description and 0 credits until results are out
    end = transcript_pages[1].index("– – – – – End of Academic Record – – – – –")
    transcript_pages[1][end:end] = [
        "2026",
        "Programme: Bachelor of Science in Engineering in Mechatronics",
        "Specialisation: Mechatronics",
        "EEE 4022S Research Project 0",
        "EEE 4124C Impact of Engineering 0",
    ]
    new = year_of(read_lines(transcript_pages, MBALI), 2026)
    assert [line.course_code for line in new] == ["EEE4022S", "EEE4124C"]
    for line in new:
        assert (line.result, line.credits, line.nqf_level, line.mark) == (
            "GIP",
            0,
            None,
            None,
        )
        assert not line.unverified  # expected in the latest year


def test_a_missing_result_in_an_earlier_year_is_unverified(transcript_pages):
    replace(
        transcript_pages,
        "EEE 1000X Practical Training 05 0 GIP GIP",
        "EEE 1000X Practical Training 0",
    )
    lines = year_of(read_lines(transcript_pages, MBALI), 2023)
    assert [line.course_code for line in lines if line.unverified] == ["EEE1000X"]


def test_a_term_gpa_that_doesnt_add_up_flags_its_whole_year(transcript_pages):
    replace(transcript_pages, "Term GPA: 71.50", "Term GPA: 70.00")
    transcript = read_lines(transcript_pages, MBALI)
    assert all(line.unverified for line in year_of(transcript, 2024))
    assert not any(line.unverified for line in year_of(transcript, 2023))
    (warning,) = transcript.warnings
    assert warning.code == "term_gpa_mismatch"
    assert "2024" in warning.message


def test_a_suffix_outside_the_handbook_key_is_unverified(transcript_pages):
    replace(
        transcript_pages,
        "MEC 1003F Engineering Drawing 05 8 95 1",
        "MEC 1003Q Engineering Drawing 05 8 95 1",
    )
    (line,) = [
        row
        for row in read_lines(transcript_pages, MBALI).lines
        if row.course_code == "MEC1003Q"
    ]
    assert (line.term, line.unverified) == ("other", True)


def test_an_issue_date_that_cant_exist_is_left_out(transcript_pages):
    pages = [
        [line.replace("05/02/2026", "31/02/2026") for line in page]
        for page in transcript_pages
    ]
    assert read_lines(pages, MBALI).issued_on is None


def test_another_students_transcript_is_refused_with_both_numbers(transcript_pages):
    with pytest.raises(TranscriptNotYours) as refusal:
        read_lines(transcript_pages, "ZVSORW999")
    assert refusal.value.extra == {
        "transcript_student_number": MBALI,
        "account_student_number": "ZVSORW999",
    }


def test_a_pdf_that_isnt_an_academic_record(transcript_pages):
    pages = [
        [line for line in page if line != "ACADEMIC RECORD"]
        for page in transcript_pages
    ]
    with pytest.raises(NotATranscript):
        read_lines(pages, MBALI)


@pytest.mark.parametrize("missing", ["the legend page", "the end line"])
def test_a_transcript_missing_a_page_or_its_end(transcript_pages, missing):
    if missing == "the legend page":
        transcript_pages.pop()
    else:
        transcript_pages[1].remove("– – – – – End of Academic Record – – – – –")
    with pytest.raises(TranscriptIncomplete):
        read_lines(transcript_pages, MBALI)


def test_rows_with_no_beginning_line_are_unreadable(transcript_pages):
    # Without it there's no telling where the record starts, so its rows can't be placed
    pages = [
        [line for line in page if BEGINNING not in line] for page in transcript_pages
    ]
    with pytest.raises(TranscriptUnreadable):
        read_lines(pages, MBALI)


def test_a_row_that_cant_be_read_makes_the_transcript_unreadable(transcript_pages):
    replace(
        transcript_pages,
        "EEE 3091F Energy Conversion I 07 16 73 2+",
        "EEE 3091F",
    )
    with pytest.raises(TranscriptUnreadable):
        read_lines(transcript_pages, MBALI)


def test_a_record_with_no_courses(transcript_pages):
    course_row = re.compile(r"[A-Z]{3} [0-9]{4}[A-Z] ")
    pages = [
        [line for line in page if not course_row.match(line)]
        for page in transcript_pages
    ]
    with pytest.raises(NoCourseHistory):
        read_lines(pages, MBALI)


def test_no_rows_and_no_beginning_line_is_no_course_history(transcript_pages):
    # Course history is decided by rows, so with none anywhere the missing line changes nothing
    pages = [
        [line for line in page if not ROW.fullmatch(line) and BEGINNING not in line]
        for page in transcript_pages
    ]
    with pytest.raises(NoCourseHistory):
        read_lines(pages, MBALI)


def test_a_pdf_with_no_text_is_unreadable():
    # A scan or a photo: a page with a picture of text and no text in it
    pdf = FPDF()
    pdf.add_page()
    pdf.rect(10, 10, 100, 50, style="F")
    with pytest.raises(TranscriptUnreadable):
        pdf_pages(bytes(pdf.output()))


def test_a_locked_pdf_is_unreadable():
    pdf = FPDF()
    pdf.set_encryption(owner_password="made-up-owner", user_password="made-up-user")
    pdf.set_font("Helvetica", size=9)
    pdf.add_page()
    pdf.cell(text="ACADEMIC RECORD")
    with pytest.raises(TranscriptUnreadable):
        pdf_pages(bytes(pdf.output()))


def test_a_damaged_pdf_is_unreadable():
    with pytest.raises(TranscriptUnreadable):
        pdf_pages(b"%PDF-1.7\nthis is not really a PDF")


def test_a_pdf_with_a_malformed_page_is_unreadable(pdf_of):
    # The page's width printed as text, which pdfplumber calls malformed. The swap keeps the file's
    # length, so its byte offsets still hold.
    pdf = pdf_of([["ACADEMIC RECORD"]]).replace(b"595.28", b"(595.)")
    with pytest.raises(TranscriptUnreadable):
        pdf_pages(pdf)


def test_a_pdf_the_pdf_library_crashes_on_is_unreadable(pdf_of, caplog):
    # A page rotation that's a name rather than a number, which pdfplumber fails on with a bare
    # TypeError: one of the many ways a malformed file can break it
    pdf = pdf_of([["ACADEMIC RECORD"]]).replace(
        b"/Type /Page\n", b"/Rotate /X\n/Type /Page\n"
    )
    with pytest.raises(TranscriptUnreadable) as refusal:
        pdf_pages(pdf)
    error = refusal.value.__cause__
    assert isinstance(error, TypeError)
    # Only its type is logged, as an error's message can quote the file
    assert "pdfplumber couldn't read a transcript: TypeError" in caplog.messages
    assert str(error) not in caplog.text
