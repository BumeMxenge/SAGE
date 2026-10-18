# Reviews a handbook year by exception, against the latest year approved before it. A row of the
# year's rules that's unchanged since then carries over, and a change read with certainty is accepted
# automatically. Everything else becomes a review row, one per printed thing, with every reason a
# person must look at it: a refusal, a removal, an equivalence no handbook prints, a course with no
# entry, a curriculum note or a failed check. A person's decision on a row holds only while the row
# shows what it showed then, and the code check runs again on the year as decided. An approved year
# is kept as a snapshot.
import hashlib
import json
import re
from collections import defaultdict
from collections.abc import Collection, Iterable, Mapping, Sequence
from typing import Literal, get_args

from pydantic import JsonValue, TypeAdapter, ValidationError, computed_field

from sage.domain.base import Row
from sage.domain.rules import (
    NODE_KEYS,
    PRIMARY_KEYS,
    Course,
    DeltaFlag,
    DeltaTable,
    EntryRule,
    Equivalence,
    HandbookDelta,
    RefusalCause,
    RuleSet,
    YearRules,
)
from sage.ingestion.checks import Check, tree_codes
from sage.ingestion.sources import Reading

# Every flag in DeltaFlag's order, the order rows are sorted in
FLAGS = tuple(flag for flags in get_args(DeltaFlag) for flag in get_args(flags))
REFUSALS = frozenset(get_args(RefusalCause))
# A printed DP (a duly performed certificate), which both models in E2 tended to read as a pass
DP = re.compile(r"\bDP\b")
# What each table's review rows are called, and the column a person decides, or None where a person
# decides the whole row
KINDS = {
    "courses": ("requirement", "entry_rule"),
    "curriculum_rules": ("rule", "rule"),
    "equivalences": ("equivalence", None),
}
# The decisions each kind of row takes, and the type a correction must be
DECISIONS = {
    "requirement": ("accept", "correct", "reject"),
    "rule": ("accept", "correct", "reject"),
    "equivalence": ("accept", "reject"),
    "removal": ("accept", "reject"),
    "no_entry": ("accept",),
    "check": ("accept",),
}
TREES = {"requirement": TypeAdapter(EntryRule), "rule": TypeAdapter(YearRules)}
# What a row shows a person, which its fingerprint is made from
SHOWN = {"id", "causes", "covers", "printed", "failures", "old", "new", "mark"}


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
    # A person's decision as review.json holds it: accept, correct or reject, the tree a correction
    # makes it, and why. Each is kept as written, so a slip is shown rather than lost.
    decision: JsonValue = None
    corrected: JsonValue = None
    note: JsonValue = None

    @property
    def kind(self) -> str:
        return self.id.split("/", 1)[0]

    @computed_field
    @property
    def fingerprint(self) -> str:
        # What the row shows, in twelve hex digits. A decision holds only while this is unchanged.
        shown = json.dumps(self.model_dump(mode="json", include=SHOWN), sort_keys=True)
        return hashlib.sha256(shown.encode()).hexdigest()[:12]


class Problem(Row):
    # Why a row's decision can't be used yet, or a check that fails on the year as decided on no
    # row's account, where row is None. A note settles one that only asks for a note.
    row: str | None
    text: str
    note: bool = False


class Review(Row):
    year: int
    compared_with: int | None  # the previous approved year; None when there's none
    rows: tuple[ReviewRow, ...]  # with each decision that still holds
    carried: int  # table rows unchanged since the previous approved year
    rules: RuleSet  # the year's rows with each decision that can be used
    # Every table row added, changed or removed since then, or changed by a decision, flagged with
    # its review row's first cause, and accepted already where it has none
    deltas: tuple[HandbookDelta, ...]
    # Decided rows that no longer show what they did when decided, or no longer exist
    returned: tuple[str, ...]
    problems: tuple[Problem, ...]

    @property
    def pending(self) -> tuple[str, ...]:
        return _pending(self.rows, self.problems)

    @property
    def settled(self) -> bool:
        # Whether the year can be approved: every row decided, and no check failing unexplained
        return not (self.pending or self.problems)


def compare(
    year: int,
    rules: RuleSet,
    readings: Iterable[Reading],
    checks: Iterable[Check],
    *,
    left_out: Collection[str] = (),
    entries: Collection[str] = (),
    previous: Snapshot | None = None,
    decided: Iterable[Mapping[str, JsonValue]] = (),
) -> Review:
    # entries are the codes the handbook prints an entry for, and decided the rows as review.json
    # held them when the run began
    readings = tuple(readings)
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
        if table == "course_group_members":
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
    rows, returned = _decisions(rows, decided)

    # Each decision that can be used sets its rows. The code check then runs again on the year as
    # decided, so a correction naming a mistyped code, or a rejected equivalence a rule relies on, is
    # caught, and a decision a check fails on needs a note saying why it stands.
    problems = [
        Problem(row=row.id, text=fault)
        for row in rows
        if row.decision is not None
        for fault in _faults(row)
    ]
    stuck = {problem.row for problem in problems}
    stored = dict(after)
    for row in rows:
        if row.decision is not None and row.id not in stuck:
            _apply(row, stored, before)
    # Where each course was printed, for the check's failures: this year's page, or the previous
    # approved year's for a removed course a person kept
    places = {r.key: r.place for r in readings if r.entity == "courses"}
    if previous:
        kept = {
            r.key: f"{previous.year}, {r.place}"
            for r in previous.readings
            if r.entity == "courses"
        }
        places = kept | places
    failing = _rechecked(year, stored, places, entries)
    covered = {key: row for row in rows for key in row.covers}
    for row in rows:
        if row.decision is None or row.id in stuck:
            continue
        found = [
            text
            for key in row.covers
            for text in failing.get(key, ())
            if text not in row.failures
        ]
        noted = isinstance(row.note, str) and row.note.strip()
        if (row.failures or found) and not noted:
            text = "needs a note saying why it stands, as a check fails on it"
            problems.append(
                Problem(row=row.id, text="; ".join((text, *found)), note=True)
            )
    problems += [
        Problem(row=None, text=text)
        for key, texts in failing.items()
        if key not in covered
        for text in texts
    ]
    return Review(
        year=year,
        compared_with=previous.year if previous else None,
        rows=tuple(rows),
        carried=len(unchanged),
        rules=_decided(year, rules, stored),
        deltas=_deltas(
            year, before, after, stored, covered, set(_pending(rows, problems))
        ),
        returned=returned,
        problems=tuple(problems),
    )


def _decisions(
    rows: Sequence[ReviewRow], decided: Iterable[Mapping[str, JsonValue]]
) -> tuple[list[ReviewRow], tuple[str, ...]]:
    # Each row with the decision review.json holds for it, where the row shows what it showed when
    # decided. A decision made on anything else no longer holds, and its row is returned to pending.
    held = {row["id"]: row for row in decided}
    kept, returned = [], []
    for row in rows:
        mine = held.pop(row.id, None)
        if mine and mine.get("fingerprint") == row.fingerprint:
            fields = ("decision", "corrected", "note")
            row = row.model_copy(update={field: mine.get(field) for field in fields})
        elif mine and mine.get("decision") is not None:
            returned.append(row.id)
        kept.append(row)
    returned += [key for key, mine in held.items() if mine.get("decision") is not None]
    return kept, tuple(sorted(returned))


def tree_fault(kind: str, tree: JsonValue) -> str | None:
    # Why a correction can't stand as a tree of its row's kind, or None where it can. It's never
    # empty, so a correction left unfilled can't become "no requirement".
    if tree is None:
        return (
            "correct needs the tree in corrected, with a refer leaf where no tree fits"
        )
    try:
        TREES[kind].validate_python(tree)
    except ValidationError as error:
        return f"corrected isn't a {kind} tree: {_first(error)}"
    return None


def _faults(row: ReviewRow) -> list[str]:
    # What stops a decision being used, other than a missing note
    allowed = DECISIONS[row.kind]
    if row.decision not in allowed:
        return [
            f"{row.kind} rows take {_listed(allowed, 'or')}, not {json.dumps(row.decision)}"
        ]
    faults = []
    if row.note is not None and not isinstance(row.note, str):
        faults.append("note must be text in quotes")
    if row.decision == "correct":
        if fault := tree_fault(row.kind, row.corrected):
            faults.append(fault)
    elif row.corrected is not None:
        faults.append("corrected is filled, so the decision should be correct")
    # A rejected draft must never leave a course needing nothing
    if row.decision == "reject" and row.kind in TREES:
        missing = [
            key.split("/", 1)[1] for key in row.covers if row.old.get(key) is None
        ]
        if missing:
            faults.append(
                f"reject keeps the previous approved year's rule, but {_listed(missing, 'and')} "
                + "had none: correct it instead, with a refer leaf where no tree fits"
            )
    return faults


def _rechecked(
    year: int,
    stored: dict[str, dict[str, JsonValue]],
    places: Mapping[str, str],
    entries: Collection[str],
) -> dict[str, list[str]]:
    # Each failure of the code check on the year as decided, by the row it flags
    rechecked = tree_codes(
        [
            Course.model_validate({"handbook_year": year, **value})
            for key, value in stored.items()
            if key.startswith("courses/")
        ],
        places,
        set(entries),
        [
            Equivalence.model_validate({"handbook_year": year, **value})
            for key, value in stored.items()
            if key.startswith("equivalences/")
        ],
    )
    failing: dict[str, list[str]] = defaultdict(list)
    for failure in rechecked.failures:
        failing["/".join(failure.flags)].append(f"{failure.place}: {failure.what}")
    return failing


def _decided(
    year: int, rules: RuleSet, stored: dict[str, dict[str, JsonValue]]
) -> RuleSet:
    # The year's rules with the rows its decisions leave
    tables: dict[str, list[dict[str, JsonValue]]] = {
        t: [] for t in get_args(DeltaTable)
    }
    for key, value in stored.items():
        table = key.split("/", 1)[0]
        tables[table].append({"handbook_year": year, **value})
    return RuleSet.model_validate({**dict(rules), **tables})


def _deltas(
    year: int,
    before: dict[str, dict[str, JsonValue]],
    after: dict[str, dict[str, JsonValue]],
    stored: dict[str, dict[str, JsonValue]],
    covered: Mapping[str, ReviewRow],
    pending: set[str],
) -> tuple[HandbookDelta, ...]:
    # Each change with its decision: accepted as read, rejected for the previous approved year's
    # row, or corrected to what the decision made it. One awaiting its decision is pending.
    deltas = []
    for key in sorted(before.keys() | after.keys()):
        old, new, kept = before.get(key), after.get(key), stored.get(key)
        if old == new == kept:
            continue
        row = covered.get(key)
        if row is None:
            approved, corrected = True, None
        elif row.id in pending:
            approved, corrected = None, None
        elif kept == new:
            approved, corrected = True, None
        elif kept == old:
            approved, corrected = False, None
        else:
            approved, corrected = True, kept
        table, name = key.split("/", 1)
        deltas.append(
            HandbookDelta(
                handbook_year=year,
                entity=table,
                entity_key=name,
                old_value=old,
                new_value=new,
                corrected_value=corrected,
                approved=approved,
                flag=row.causes[0] if row else None,
            )
        )
    return tuple(deltas)


def _pending(rows: Iterable[ReviewRow], problems: Iterable[Problem]) -> tuple[str, ...]:
    # Rows with no decision that can be used yet
    stuck = {problem.row for problem in problems}
    return tuple(row.id for row in rows if row.decision is None or row.id in stuck)


def _apply(
    row: ReviewRow,
    stored: dict[str, dict[str, JsonValue]],
    before: dict[str, dict[str, JsonValue]],
) -> None:
    # Each table row the decision covers, as the decision leaves it
    for key in row.covers:
        if row.kind in TREES:
            if row.decision == "correct":
                trees = TREES[row.kind]
                value = trees.dump_python(
                    trees.validate_python(row.corrected), mode="json"
                )
            else:
                value = row.old[key] if row.decision == "reject" else row.new
            column = KINDS[key.split("/", 1)[0]][1]
            stored[key] = {**stored[key], column: value}
        elif row.decision == "reject" and row.kind == "removal":
            stored[key] = before[key]
        elif row.decision == "reject" and row.kind == "equivalence":
            del stored[key]


def _row(
    keys: Sequence[str],
    read: dict[str, Reading],
    before: dict[str, dict[str, JsonValue]],
    after: dict[str, dict[str, JsonValue]],
    failures: dict[str, list[str]],
) -> ReviewRow:
    # A row for table rows read this year, which share their printed words and what they read
    table, name = keys[0].split("/", 1)
    kind, column = KINDS[table]

    def decided(value: dict[str, JsonValue]) -> JsonValue:
        return value[column] if column else value

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
        for row in getattr(rules, table):
            value = row.model_dump(mode="json", exclude={"handbook_year"})
            key = "/".join(
                str(value[c]) for c in PRIMARY_KEYS[table] if c != "handbook_year"
            )
            keyed[f"{table}/{key}"] = value
    return keyed


def _ordered(causes: set[str]) -> tuple[str, ...]:
    return tuple(sorted(causes, key=FLAGS.index))


def _shape(value: JsonValue) -> str:
    # A tree's nodes without their contents, such as any(course,refer), so like rows sit together
    if not isinstance(value, dict):
        return ""
    node = next((key for key in NODE_KEYS if key in value), "")
    if node in ("all", "any"):
        return f"{node}({','.join(_shape(child) for child in value[node])})"
    return node


def _listed(words: Sequence[str], last: str) -> str:
    # Words in a list, such as "accept, correct or reject"
    return (
        words[0] if len(words) == 1 else f"{', '.join(words[:-1])} {last} {words[-1]}"
    )


def _first(error: ValidationError) -> str:
    # The first thing wrong with a tree, and where in it
    problem = error.errors()[0]
    where = ".".join(str(part) for part in problem["loc"])
    return f"{where}: {problem['msg']}" if where else problem["msg"]
