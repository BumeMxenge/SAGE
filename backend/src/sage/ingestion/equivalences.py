# Reads a year's equivalences: codes whose pass counts as another's. No handbook prints "counts as",
# so each row was drafted from the pages it cites, and every one is flagged for a person to check.
import csv
from pathlib import Path

from sage.ingestion.sources import Reading, SourceError
from sage.shared.base import Row
from sage.shared.rules import Equivalence

COLUMNS = ["code", "counts_as", "reason", "page"]


class Equivalences(Row):
    equivalences: tuple[Equivalence, ...]
    readings: tuple[Reading, ...]


def read(path: Path, year: int) -> Equivalences:
    with path.open(encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames != COLUMNS:
            raise SourceError(f"{path.name}'s columns aren't {', '.join(COLUMNS)}")
        rows = list(reader)
    return Equivalences(
        equivalences=tuple(
            Equivalence(
                handbook_year=year, course_code=row["code"], counts_as=row["counts_as"]
            )
            for row in rows
        ),
        readings=tuple(
            Reading(
                entity="equivalences",
                key=f"{row['code']}/{row['counts_as']}",
                place=row["page"],
                printed=row["reason"],
                flag="not_printed",
            )
            for row in rows
        ),
    )
