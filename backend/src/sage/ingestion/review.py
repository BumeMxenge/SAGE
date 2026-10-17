# Reviews a handbook year by exception, against the latest year approved before it. A row of the
# year's rules that's unchanged since then carries over, and a change read with certainty is accepted
# automatically. Everything else becomes a review row, one per printed thing, with every reason a
# person must look at it: a refusal, a removal, an equivalence no handbook prints, a course with no
# entry, a curriculum note or a failed check. An approved year is kept as a snapshot.
import re
from collections import defaultdict
from collections.abc import Collection, Iterable, Sequence
from typing import Literal, get_args

from pydantic import JsonValue

from sage.domain.base import Row
from sage.domain.rules import (
    NODE_KEYS,
    PRIMARY_KEYS,
    DeltaFlag,
    DeltaTable,
    HandbookDelta,
    RefusalCause,
    RuleSet,
    year_column,
)
from sage.ingestion.checks import Check
from sage.ingestion.sources import Reading

# Every flag in DeltaFlag's order, the order rows are sorted in
FLAGS = tuple(flag for flags in get_args(DeltaFlag) for flag in get_args(flags))
REFUSALS = frozenset(get_args(RefusalCause))
# A printed DP (a duly performed certificate), which both models in E2 tended to read as a pass
DP = re.compile(r"\bDP\b")
# What each table's review rows are called, and the part of a row a person decides
KINDS = {
    "courses": ("requirement", lambda row: row["entry_rule"]),
    "curriculum_rules": ("rule", lambda row: row["rule"]),
    "equivalences": ("equivalence", lambda row: row),
}


class Snapshot(Row):
    # An approved year as data/rules/<year>/rulebook.json holds it: every row sage load writes, and
    # where each was printed, which the next year reads to carry over what it prints unchanged
    rules: RuleSet
    readings: tuple[Reading, ...]

    @property
    def year(self) -> int:
        return self.rules.handbook_versions[0].year


class ReviewRow(Row):
    # One printed thing for a person to decide, and every table row the decision covers
    id: str  # its kind, then what it is, such as requirement/MEC2045S or removal/EEE1006F
    causes: tuple[DeltaFlag, ...]
    # Each table row it covers, as "table/key", and where it's printed
    covers: dict[str, str]
    printed: str
    failures: tuple[str, ...]  # each failed check on it, and where to look
    # What the previous approved year held, for each row it held
    old: dict[str, JsonValue]
    new: JsonValue  # what this year reads, the same for every row covered; None for a removal
    mark: Literal["dp"] | None  # a draft of wording that prints a DP, to read closely


class Review(Row):
    year: int
    compared_with: int | None  # the previous approved year; None when there's none
    rows: tuple[ReviewRow, ...]
    carried: int  # table rows unchanged since the previous approved year
    # Every table row added, changed or removed since then, flagged with its review row's first
    # cause, and accepted already where it has none
    deltas: tuple[HandbookDelta, ...]


def compare(
    year: int,
    rules: RuleSet,
    readings: Iterable[Reading],
    checks: Iterable[Check],
    left_out: Collection[str] = (),
    previous: Snapshot | None = None,
) -> Review:
    before = _keyed(previous.rules) if previous else {}
    after = _keyed(rules)
    read = {f"{r.entity}/{r.key}": r for r in readings}
    earlier = {f"{r.entity}/{r.key}": r for r in previous.readings} if previous else {}
    # A row carries over when it holds what was approved and its words are printed as they were
    unchanged = {
        key
        for key, value in after.items()
        if before.get(key) == value and earlier[key].printed == read[key].printed
    }

    # Each failure counts against the table row it flags, every year, as a check is about this
    # year's rules. One that flags no row this year has a row of its own.
    failures: dict[str, list[str]] = defaultdict(list)
    loose: list[tuple[str, str]] = []
    for check in checks:
        for failure in check.failures:
            text = f"{failure.place}: {failure.what}"
            key = "/".join(failure.flags) if failure.flags else None
            if key in after:
                failures[key].append(text)
            else:
                loose.append((check.name, text))

    # Rows read with a cause to look, unless they carry over, and rows a check fails on
    wanted = [
        key
        for key in sorted(after)
        if key in failures or (key not in unchanged and read[key].flag)
    ]
    rows: list[ReviewRow] = []
    by_words: dict[str, list[str]] = defaultdict(list)
    for key in wanted:
        if key.startswith("courses/"):
            # One row per printed requirement, so one decision covers every course printing it
            by_words[read[key].printed].append(key)
        else:
            rows.append(_row([key], read, before, after, failures))
    rows += [_row(keys, read, before, after, failures) for keys in by_words.values()]

    # A course and every list it left are one removal, and each other row is one of its own
    removed: dict[str, list[str]] = defaultdict(list)
    for key in sorted(before.keys() - after.keys()):
        table, name = key.split("/", 1)
        if table in ("courses", "course_group_members"):
            name = name.rsplit("/", 1)[-1]
        removed[name].append(key)
    rows += [
        ReviewRow(
            id=f"removal/{name}",
            causes=_ordered(
                {"removed", "no_entry"} if name in left_out else {"removed"}
            ),
            covers={key: f"{previous.year}, {earlier[key].place}" for key in keys},
            printed=earlier[keys[0]].printed,
            failures=(),
            old={key: before[key] for key in keys},
            new=None,
            mark=None,
        )
        for name, keys in removed.items()
    ]
    # A course only notes name, which the previous approved year didn't hold either
    rows += [
        ReviewRow(
            id=f"no_entry/{code}",
            causes=("no_entry",),
            covers={},
            printed=f"{code}, named only in notes",
            failures=(),
            old={},
            new=None,
            mark=None,
        )
        for code in sorted(set(left_out) - removed.keys())
    ]
    rows += [
        ReviewRow(
            id=f"check/{text}",
            causes=("check_failed",),
            covers={},
            printed=name,
            failures=(text,),
            old={},
            new=None,
            mark=None,
        )
        for name, text in dict.fromkeys(loose)
    ]
    rows.sort(
        key=lambda row: (
            FLAGS.index(row.causes[0]),
            _shape(row.new),
            row.printed,
            row.id,
        )
    )

    flagged = {key: row.causes[0] for row in rows for key in row.covers}
    deltas = tuple(
        HandbookDelta(
            handbook_year=year,
            entity=key.split("/", 1)[0],
            entity_key=key.split("/", 1)[1],
            old_value=before.get(key),
            new_value=after.get(key),
            flag=flagged.get(key),
            approved=None if key in flagged else True,
        )
        for key in sorted(before.keys() | after.keys())
        if before.get(key) != after.get(key)
    )
    return Review(
        year=year,
        compared_with=previous.year if previous else None,
        rows=tuple(rows),
        carried=len(unchanged),
        deltas=deltas,
    )


def _row(
    keys: Sequence[str],
    read: dict[str, Reading],
    before: dict[str, dict[str, JsonValue]],
    after: dict[str, dict[str, JsonValue]],
    failures: dict[str, list[str]],
) -> ReviewRow:
    # A row for table rows read this year, which share their printed words and what they read
    table, name = keys[0].split("/", 1)
    kind, decided = KINDS.get(table, ("check", lambda row: row))
    found = tuple(text for key in keys for text in failures.get(key, ()))
    causes = {read[key].flag for key in keys if read[key].flag}
    causes |= {"check_failed"} if found else set()
    printed = read[keys[0]].printed
    return ReviewRow(
        id=f"{kind}/{name}",
        causes=_ordered(causes),
        covers={key: read[key].place for key in keys},
        printed=printed,
        failures=found,
        old={key: decided(before[key]) for key in keys if key in before},
        new=decided(after[keys[0]]),
        mark="dp" if causes & REFUSALS and DP.search(printed) else None,
    )


def _keyed(rules: RuleSet) -> dict[str, dict[str, JsonValue]]:
    # The rows a change can be in, by "table/key" as a reading names them, each without its year
    keyed = {}
    for table in get_args(DeltaTable):
        year = year_column(table)
        for row in getattr(rules, table):
            value = row.model_dump(mode="json", exclude={year})
            key = "/".join(str(value[c]) for c in PRIMARY_KEYS[table] if c != year)
            keyed[f"{table}/{key}"] = value
    return keyed


def _ordered(causes: set[str]) -> tuple[str, ...]:
    return tuple(sorted(causes, key=FLAGS.index))


def _shape(value: JsonValue) -> str:
    # A tree's nodes without their contents, such as any(course,refer), so like rows sit together
    if not isinstance(value, dict):
        return ""
    node = next((key for key in NODE_KEYS if key in value), "")
    children = value[node] if node in ("all", "any") else None
    if isinstance(children, list):
        return f"{node}({','.join(_shape(child) for child in children)})"
    return node
