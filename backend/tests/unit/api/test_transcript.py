# Checks the transcript upload: her own record comes back as lines to review with the curricula her
# programme could be, and anything else is refused with its own problem
import pytest

END = "– – – – – End of Academic Record – – – – –"


@pytest.fixture
def upload(signed_in, pdf_of):
    # Sends pages of lines as a PDF, signed in as the named account
    def send(pages, token="mbali"):
        return signed_in(token).post(
            "/v1/onboarding/transcript",
            content=pdf_of(pages),
            headers={"Content-Type": "application/pdf"},
        )

    return send


def test_her_transcript_comes_back_to_review(upload, transcript_pages):
    response = upload(transcript_pages)
    assert response.status_code == 200
    transcript = response.json()
    assert transcript["student_number"] == "DLMMBA999"
    assert (
        transcript["programme"] == "Bachelor of Science in Engineering in Mechatronics"
    )
    assert [row["code"] for row in transcript["curriculum_options"]] == ["EB011EEE05"]
    assert transcript["issued_on"] == "2026-02-05"
    assert len(transcript["lines"]) == 34
    assert transcript["lines"][0].keys() == {
        "academic_year",
        "term",
        "course_code",
        "course_name",
        "credits",
        "nqf_level",
        "result",
        "mark",
        "unverified",
    }
    assert transcript["warnings"] == []


def test_another_students_transcript_is_refused_with_both_numbers(
    upload, transcript_pages
):
    response = upload(transcript_pages, token="zvsorw")
    assert response.status_code == 422
    problem = response.json()
    assert problem["code"] == "transcript_not_yours"
    assert problem["transcript_student_number"] == "DLMMBA999"
    assert problem["account_student_number"] == "ZVSORW999"


@pytest.mark.parametrize(
    ("content_type", "body"),
    [
        ("text/plain", b"%PDF-1.7"),
        ("application/pdf", b"Name,Course\nMbali,EEE4113F\n"),
    ],
    ids=["not sent as a PDF", "not a PDF inside"],
)
def test_a_file_that_isnt_a_pdf_is_refused(signed_in, content_type, body):
    response = signed_in("mbali").post(
        "/v1/onboarding/transcript",
        content=body,
        headers={"Content-Type": content_type},
    )
    assert response.status_code == 415
    assert response.json()["code"] == "not_a_pdf"


def test_a_file_over_10_mb_is_refused(signed_in):
    response = signed_in("mbali").post(
        "/v1/onboarding/transcript",
        content=b"%PDF-" + bytes(10 * 1024 * 1024),
        headers={"Content-Type": "application/pdf"},
    )
    assert response.status_code == 413
    assert response.json()["code"] == "file_too_large"


def test_staff_cant_upload_a_transcript(upload, transcript_pages):
    assert upload(transcript_pages, token="staff").json()["code"] == "students_only"


def test_a_record_with_no_courses_says_why(upload, transcript_pages):
    # Everything after the Beginning line on page 1, and every year on page 2
    page1, page2 = transcript_pages[0], transcript_pages[1]
    del page1[page1.index("2023") :]
    del page2[page2.index("Course Description NQF NQF Result") : page2.index(END)]
    problem = upload(transcript_pages).json()
    assert problem["code"] == "no_course_history"
    assert problem["detail"].startswith(
        "Your academic record has no courses on it yet."
    )


def test_a_missing_last_year_is_a_warning_not_an_error(upload, transcript_pages):
    page1, page2 = transcript_pages[0], transcript_pages[1]
    del page1[page1.index("2025") : page1.index("2025") + 3]
    del page2[page2.index("Course Description NQF NQF Result") : page2.index(END)]
    response = upload(transcript_pages)
    assert response.status_code == 200
    (warning,) = response.json()["warnings"]
    assert warning["code"] == "recent_year_missing"
    assert "2025" in warning["message"]


def test_last_years_results_still_to_come_are_a_warning(upload, transcript_pages):
    page2 = transcript_pages[1]
    gip = page2.index("EEE 3000X Practical Training 07 0 GIP GIP")
    page2[gip] = "EEE 3000X Practical Training 0"
    transcript = upload(transcript_pages).json()
    assert [warning["code"] for warning in transcript["warnings"]] == [
        "results_pending"
    ]
    (line,) = [row for row in transcript["lines"] if row["course_code"] == "EEE3000X"]
    assert (line["result"], line["unverified"]) == ("GIP", False)
