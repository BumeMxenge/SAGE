# A year's sources, as data/sources/<year>/manifest.toml names them. Every file is checked against its
# SHA-256 before anything reads it, so a changed file stops the run instead of changing a rule
# unnoticed.
import hashlib
import json
import tomllib
from collections.abc import Mapping
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

from sage.domain.base import Row

# Rows that need an id get one made from what they hold, so a row read again gets the same id
ROW_IDS = uuid5(NAMESPACE_URL, "https://github.com/BumeMxenge/SAGE/ingestion")


class SourceError(Exception):
    # A source doesn't fit its reading. The run stops, and the message names the file and the place,
    # so a person can look at the print.
    pass


class SourceFile(Row):
    file: str
    format: str
    title: str
    sha256: str


class Section(Row):
    # Printed prose cut into passages, by its heading and its first and last pages. A section that
    # ends partway down its last page names the heading that follows it.
    section: str
    pages: tuple[int, int]
    until: str | None = None


class HandbookFile(SourceFile):
    url: str
    passages: tuple[Section, ...]


class Alternatives(Row):
    # Meetings a sheet prints side by side, of which a student attends one, by their cells in the
    # order of their choice letters
    course: str
    group: str
    cells: tuple[str, ...]  # such as "Labs!O11:O14"


class TimetableFile(SourceFile):
    sheets: dict[str, tuple[str, ...]]  # each sheet read, with the curricula it shows
    alternatives: tuple[Alternatives, ...] = ()


class ComplementaryFile(SourceFile):
    # Each sheet read, by what it holds
    courses: str
    languages: str
    meetings: str


class Manifest(Row):
    folder: Path
    year: int
    # The department whose curricula are in scope, by its printed heading
    department: str
    handbook: HandbookFile
    timetable: TimetableFile | None = None
    complementary: ComplementaryFile | None = None
    equivalences: SourceFile

    def path(self, source: SourceFile) -> Path:
        return self.folder / source.file


def row_id(row: Mapping[str, object]) -> UUID:
    return uuid5(ROW_IDS, json.dumps(row, sort_keys=True, default=str))


def load(folder: Path) -> Manifest:
    data = tomllib.loads((folder / "manifest.toml").read_text(encoding="utf-8"))
    manifest = Manifest.model_validate({"folder": folder, **data})
    for source in (
        manifest.handbook,
        manifest.timetable,
        manifest.complementary,
        manifest.equivalences,
    ):
        if source is None:
            continue
        found = hashlib.sha256(manifest.path(source).read_bytes()).hexdigest()
        if found != source.sha256:
            raise SourceError(
                f"{source.file} has changed: its SHA-256 is {found}, but manifest.toml "
                f"expects {source.sha256}"
            )
    return manifest
