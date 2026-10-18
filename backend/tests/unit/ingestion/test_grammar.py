# Checks the requirement grammar on requirements printed in the 2023 and 2026 handbooks: what it
# reads, against trees written by hand from the page, and what it refuses, with the cause
import pytest

from sage.domain.rules import AllOf, AnyOf, CourseNeed
from sage.ingestion.grammar import Refused, read


def passes(*codes):
    return tuple(CourseNeed(course=code, need="pass") for code in codes)


@pytest.mark.parametrize(
    ("printed", "tree"),
    [
        # MEC1003F (2026, page 144)
        ("None", None),
        # EEE4117F (2026, page 139)
        ("EEE3091F", CourseNeed(course="EEE3091F", need="pass")),
        # MAM1021S (2026, page 179): the closing full stop changes nothing
        ("MAM1020F.", CourseNeed(course="MAM1020F", need="pass")),
        # EEE3090F (2026, page 134)
        ("EEE2045F and EEE2047S", AllOf(all=passes("EEE2045F", "EEE2047S"))),
        # EEE4022S (2026, page 138), printed over two lines
        (
            (
                "EEE4114F or EEE4126F or EEE4117F or EEE4118F or EEE4121F or\n"
                "EEE4120F or EEE4119F"
            ),
            AnyOf(
                any=passes(
                    "EEE4114F",
                    "EEE4126F",
                    "EEE4117F",
                    "EEE4118F",
                    "EEE4121F",
                    "EEE4120F",
                    "EEE4119F",
                )
            ),
        ),
        # EEE2047S (2026, page 132): F/S and S/F are either term, in the same any
        (
            "MAM1021F/S or MAM1024S/F",
            AnyOf(any=passes("MAM1021F", "MAM1021S", "MAM1024S", "MAM1024F")),
        ),
        # MEC2047F (2026, page 148): commas join like "and"
        (
            "MAM1021F/S, PHY1012F/S and MEC1009F/S",
            AllOf(
                all=(
                    AnyOf(any=passes("MAM1021F", "MAM1021S")),
                    AnyOf(any=passes("PHY1012F", "PHY1012S")),
                    AnyOf(any=passes("MEC1009F", "MEC1009S")),
                )
            ),
        ),
        # CSC2004Z (2026, page 170): brackets group
        (
            "(CSC1015F/S and CSC1016S) or (CSC1010H and CSC1011H)",
            AnyOf(
                any=(
                    AllOf(
                        all=(
                            AnyOf(any=passes("CSC1015F", "CSC1015S")),
                            CourseNeed(course="CSC1016S", need="pass"),
                        )
                    ),
                    AllOf(all=passes("CSC1010H", "CSC1011H")),
                )
            ),
        ),
        # EEE2044S (2026, page 130): the comma after "and" changes nothing
        (
            "(MAM1020F/S or MAM1023F/S) and, (PHY1013F/S or PHY1015F/S) and EEE1007S",
            AllOf(
                all=(
                    AnyOf(any=passes("MAM1020F", "MAM1020S", "MAM1023F", "MAM1023S")),
                    AnyOf(any=passes("PHY1013F", "PHY1013S", "PHY1015F", "PHY1015S")),
                    CourseNeed(course="EEE1007S", need="pass"),
                )
            ),
        ),
    ],
)
def test_wording_with_one_reading_is_read(printed, tree):
    assert read(printed) == tree


@pytest.mark.parametrize(
    ("printed", "cause"),
    [
        # MAM1020F (2026, page 178): a school result, though it also gives a mark
        (
            (
                "A pass in NSC Mathematics with at least 70%, or at least a D symbol "
                "at A-level."
            ),
            "refused_school_result",
        ),
        # CML4607F (2026, page 164)
        (
            (
                "This course is only available to BSc(Eng) Electrical Engineering; "
                "BSc(Eng) Electrical and Computer Engineering and BSc(Eng) Mechatronics "
                "students."
            ),
            "refused_programme",
        ),
        # HUB4049F (2026, page 162)
        ("Students must be in their fourth year of study.", "refused_year_of_study"),
        # CSC2002S (2026, page 170)
        ("CSC2001F (At least 45% for CSC2001F)", "refused_mark_threshold"),
        # MAM2083F (2026, page 182): "or equivalent", though its codes lack a term too
        (
            "MAM1020 or equivalent and MAM1021 or equivalent.",
            "refused_or_equivalent",
        ),
        # MAM2085F (2026, page 183)
        ("MAM1023 and MAM1024", "refused_code_without_term"),
        # CSC3023F (2023, page 179): a condition in prose, though a full stop joins it too
        (
            "CSC2001F, CSC2002S. CSC2004Z is required if CSC2002S was passed after 2017.",
            "refused_free_text",
        ),
        # PHY2010S (2026, page 191), printed over two lines
        (
            "PHY1012F/S and PHY1013F/S; or PHY1014F/S and PHY1015F/S.\nMAM2083F/S.",
            "refused_punctuation",
        ),
        # MEC2045S (2026, page 148)
        ("MEC1009F/S and MEC2023F/S or MEC2047F/S", "refused_mixed_and_or"),
        # Made up, as nothing printed has them: a bracket that never closes, codes with
        # no join between them, and a join with nothing after it
        ("(EEE2045F or EEE2046F", "refused_other"),
        ("(EEE2045F) EEE2046F", "refused_other"),
        ("EEE2045F and", "refused_other"),
    ],
)
def test_wording_without_one_reading_is_refused_with_its_cause(printed, cause):
    with pytest.raises(Refused) as refused:
        read(printed)
    assert refused.value.cause == cause
