# Checks every equivalence is read with its reason and pages, and flagged for a person, as no
# handbook prints one
from sage.ingestion.equivalences import read
from sage.ingestion.sources import Reading
from sage.shared.rules import Equivalence

# Two rows of 2026's file, with their reasons shortened
CSV = """code,counts_as,reason,page
MAM1020F,MAM1023F,"The 5-year curricula list MAM1023F where the 4-year curricula list MAM1020F.","2026: 48, 50, 183"
EEE1006F,EEE1008F,"2026's first-year slot lists EEE1008F where 2023's lists EEE1006F.",2023: 46; 2026: 48
"""


def test_every_equivalence_is_flagged_as_not_printed(tmp_path):
    path = tmp_path / "equivalences.csv"
    path.write_text(CSV, encoding="utf-8")
    equivalences = read(path, 2026)
    assert equivalences.equivalences == (
        Equivalence(handbook_year=2026, course_code="MAM1020F", counts_as="MAM1023F"),
        Equivalence(handbook_year=2026, course_code="EEE1006F", counts_as="EEE1008F"),
    )
    assert equivalences.readings == (
        Reading(
            entity="equivalences",
            key="MAM1020F/MAM1023F",
            place="2026: 48, 50, 183",
            printed="The 5-year curricula list MAM1023F where the 4-year curricula list MAM1020F.",
            flag="not_printed",
        ),
        Reading(
            entity="equivalences",
            key="EEE1006F/EEE1008F",
            place="2023: 46; 2026: 48",
            printed="2026's first-year slot lists EEE1008F where 2023's lists EEE1006F.",
            flag="not_printed",
        ),
    )
