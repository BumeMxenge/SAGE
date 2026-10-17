# Checks the manifest stops a run when a source no longer matches its fingerprint
import pytest

from sage.ingestion.sources import SourceError, load

# The SHA-256 of a file with no bytes, a published constant
EMPTY = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

# A year with no timetable or complementary workbook, as 2023 has, so the check must pass over the
# missing files and still reach the equivalences
MANIFEST = f"""
year = 2023
department = "Electrical Engineering"

[handbook]
file = "handbook.pdf"
format = "pdf"
title = "A made-up handbook"
url = "https://example.org/handbook.pdf"
sha256 = "{EMPTY}"
passages = []

[equivalences]
file = "equivalences.csv"
format = "csv"
title = "Made-up equivalences"
sha256 = "{EMPTY}"
"""


def test_a_source_must_match_its_fingerprint(tmp_path):
    (tmp_path / "manifest.toml").write_text(MANIFEST, encoding="utf-8")
    (tmp_path / "handbook.pdf").write_bytes(b"")
    (tmp_path / "equivalences.csv").write_bytes(b"")
    assert load(tmp_path).year == 2023

    (tmp_path / "equivalences.csv").write_bytes(b"\n")
    with pytest.raises(SourceError, match="equivalences.csv has changed"):
        load(tmp_path)
