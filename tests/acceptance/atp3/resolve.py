# Resolves every ATP-3 expectation from the engine and the plan data, and writes results/resolved.csv
# before any model call, so each is fixed first. It never runs the advisor's own tools, so a fault in
# them can't mark itself right. It also checks each quote against the student's slice: an answer
# that rests on a passage her slice doesn't hold can't come from her evidence, so the prompt expects
# a referral. Anything it can't resolve stops it, every problem listed, before it writes a row.
# make atp3-resolve runs it from backend/, and it calls no model.
import csv
import json
import re
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import time
from typing import Any, get_args

from show_plans import ACCOUNT
from students import FILES, HERE, YEAR, prepared, short_ids, store, stores

from sage.advisor.evidence import Evidence
from sage.engine.eligibility import EntryRuleEligibility
from sage.features.chats import service as chats
from sage.shared.planning import Eligibility
from sage.shared.rulebook import Rulebook
from sage.shared.rules import (
    Passage,
    RuleSet,
    TermCode,
    TimetableSlot,
    meetings,
    meetings_on,
)
from sage.shared.students import StudentState

PROMPTS = HERE / "prompts.csv"
RESULTS = HERE / "results"
HEADER = (
    "id",
    "student",
    "term",
    "group",
    "prompt",
    "expected_behaviour",
    "expected_fact",
    "page",
    "quote",
    "resolve",
    "tempting_wrong",
    "paraphrase_of",
    "control_arm",
    "note",
)
COLUMNS = (
    "prompt",
    "student",
    "group",
    "term",
    "plans",
    "expected",
    "moved",
    "kind",
    "predicted",
    "engine",
    "slice",
    "data",
    "words",
)
# The behaviours that answer, which NF-2's 95% counts, and the rest, which its 90% counts
ANSWERABLE = ("answer", "offer_plan", "no_plan", "firm_no")
REFERRING = ("refer", "decline")
BEHAVIOURS = (*ANSWERABLE, *REFERRING, "per_engine")
VERDICTS = ("eligible", "check", "not_eligible")
# per_engine's behaviour for each verdict, as my answers at Stop 1 set it
PER_ENGINE = {"eligible": "answer", "check": "refer", "not_eligible": "firm_no"}
# The verdict a group's prompts need, where its name states one
GROUP_VERDICT = {"not_eligible": "not_eligible", "check_refer": "check"}
DAYS = {"mon": 1, "tue": 2, "wed": 3, "thu": 4, "fri": 5, "sat": 6, "sun": 7}
DAY_NAMES = {number: name.title() for name, number in DAYS.items()}
WEEKDAYS = range(1, 6)
# The parts of the year a meeting's term covers: the semesters' quarters, and winter and summer.
# Two meetings can clash only if they share a part, so Q1 and Q2 never do, and a week tab shows each
# meeting whose term shares a part with the tab's.
PARTS: dict[str, frozenset[str]] = {
    "q1": frozenset({"Q1"}),
    "q2": frozenset({"Q2"}),
    "sem1": frozenset({"Q1", "Q2"}),
    "q3": frozenset({"Q3"}),
    "q4": frozenset({"Q4"}),
    "sem2": frozenset({"Q3", "Q4"}),
    "full_year": frozenset({"Q1", "Q2", "Q3", "Q4"}),
    "winter": frozenset({"winter"}),
    "summer": frozenset({"summer"}),
    "other": frozenset(),
}
CODE = re.compile(r"^[A-Z]{3}\d{4}[A-Z]$")
PLAN = re.compile(r"\bV\d{2}\b")
# Where a quote leaves words out, and a table row's dotted leader, which print runs between words
GAP = re.compile(r"\.{3,}|…")
# Print's curly quotes and dashes, which a quote typed by hand writes plainly
PLAIN = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-"})

Row = dict[str, str]


class Unresolved(Exception):
    # A prompt whose expectation can't be fixed from the engine and the plan data
    pass


@dataclass(frozen=True)
class Meeting:
    code: str
    day: int | None
    start: time | None
    end: time | None
    parts: frozenset[str]
    certain: bool  # not one of several alternatives, of which she attends one

    @property
    def timed(self) -> bool:
        return None not in (self.day, self.start, self.end)

    def words(self) -> str:
        day = DAY_NAMES[self.day] if self.day else "no printed day"
        hours = (
            f"{self.start:%H:%M} to {self.end:%H:%M}"
            if self.start and self.end
            else "no printed time"
        )
        return f"{self.code} {day} {hours}"


def read_prompts() -> list[Row]:
    with PROMPTS.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if tuple(reader.fieldnames or ()) != HEADER:
            raise SystemExit(
                f"prompts.csv's header isn't the one agreed: {reader.fieldnames}"
            )
        return list(reader)


def read_resolved() -> dict[str, Row]:
    with (RESULTS / "resolved.csv").open(encoding="utf-8", newline="") as file:
        return {row["prompt"]: row for row in csv.DictReader(file)}


def as_meetings(code: str, slots: Iterable[TimetableSlot]) -> list[Meeting]:
    # A choice group with more than one alternative left is hers to pick from, so its meetings aren't
    # certain. One alternative can meet more than once.
    slots = list(slots)
    choices: dict[str, set[str | None]] = defaultdict(set)
    for slot in slots:
        if slot.choice_group is not None:
            choices[slot.choice_group].add(slot.choice)
    return [
        Meeting(
            code=code,
            day=slot.day,
            start=slot.start_time,
            end=slot.end_time,
            parts=PARTS[slot.term],
            certain=slot.choice_group is None or len(choices[slot.choice_group]) == 1,
        )
        for slot in slots
    ]


def plan_week(state: StudentState, key: str, rules: RuleSet, tab: str) -> list[Meeting]:
    # One plan's meetings that show in a week tab, as its courses' timetables place them
    plan = short_ids(state)[key]
    curriculum = state.student.curriculum_code
    found = [
        meeting
        for row in state.plan_courses
        if row.plan_id == plan.id
        for meeting in as_meetings(row.course_code, meetings(row, rules, curriculum))
    ]
    return [meeting for meeting in found if meeting.parts & PARTS[tab]]


def overlaps(one: Meeting, other: Meeting) -> bool:
    # On the same day, in a shared part of the year, and overlapping in time: touching isn't a clash
    return (
        one.timed
        and other.timed
        and one.day == other.day
        and bool(one.parts & other.parts)
        and one.start < other.end
        and other.start < one.end
    )


def day_names(days: Iterable[int]) -> list[str]:
    return [DAY_NAMES[day] for day in sorted(set(days))]


def unplaced(week: Sequence[Meeting]) -> list[str]:
    return [meeting.words() for meeting in week if not meeting.timed]


def finish_after(week: Sequence[Meeting], at: time) -> dict[str, Any]:
    late = {m.day for m in week if m.certain and m.timed and m.end > at}
    maybe = {m.day for m in week if not m.certain and m.timed and m.end > at} - late
    return {
        "days": day_names(late),
        "only_as_alternatives": day_names(maybe),
        "unplaced": unplaced(week),
    }


def count_starts(week: Sequence[Meeting], at: time) -> dict[str, Any]:
    def starting(certain: bool) -> list[str]:
        return [
            meeting.words()
            for meeting in sorted(week, key=lambda m: (m.day or 8, m.code))
            if meeting.certain == certain and meeting.timed and meeting.start == at
        ]

    certain = starting(True)
    return {
        "count": len(certain),
        "meetings": certain,
        "alternatives": starting(False),
        "unplaced": unplaced(week),
    }


def day_load(week: Sequence[Meeting], day: int) -> dict[str, Any]:
    on_day = sorted(
        (m for m in week if m.day == day),
        key=lambda m: (m.start or time.max, m.end or time.max, m.code),
    )
    return {
        "day": DAY_NAMES[day],
        "meetings": [m.words() for m in on_day if m.certain and m.timed],
        "alternatives": [m.words() for m in on_day if not m.certain],
        "no_printed_time": [m.words() for m in on_day if m.certain and not m.timed],
        "no_printed_day": [m.words() for m in week if m.day is None],
    }


def free_days(week: Sequence[Meeting]) -> dict[str, Any]:
    # A meeting with a day but no printed time still takes up its day
    busy = {m.day for m in week if m.certain and m.day is not None}
    maybe = {m.day for m in week if not m.certain and m.day is not None} - busy
    return {
        "free": day_names(day for day in WEEKDAYS if day not in busy | maybe),
        "free_unless_she_picks_an_alternative": day_names(
            day for day in WEEKDAYS if day in maybe
        ),
        "no_printed_day": [m.words() for m in week if m.day is None],
    }


def clash(state: StudentState, rules: RuleSet, one: str, other: str) -> dict[str, Any]:
    # Whether two courses' meetings clash in each plan holding both, or, where none does, whether
    # their timetabled meetings overlap at all
    curriculum = state.student.curriculum_code
    plans = []
    for key, plan in sorted(short_ids(state).items()):
        rows = {
            row.course_code: row
            for row in state.plan_courses
            if row.plan_id == plan.id and row.course_code in (one, other)
        }
        if len(rows) < 2:
            continue
        first, second = (
            as_meetings(code, meetings(rows[code], rules, curriculum))
            for code in (one, other)
        )
        pairs = [(a, b) for a in first for b in second if overlaps(a, b)]
        plans.append(
            {
                "plan": key,
                "name": plan.name,
                "clash": any(a.certain and b.certain for a, b in pairs),
                "only_with_alternatives": bool(pairs)
                and not any(a.certain and b.certain for a, b in pairs),
            }
        )
    if plans:
        return {"plans": plans}
    first, second = (
        as_meetings(code, meetings_on(rules, curriculum, code)) for code in (one, other)
    )
    return {
        "plans": [],
        "timetables_overlap": any(overlaps(a, b) for a in first for b in second),
    }


def find_plan(state: StudentState, have: set[str], avoid: set[str]) -> dict[str, Any]:
    # Her plans, shown or hidden, with every course in have and none in avoid
    found = []
    for key, plan in sorted(short_ids(state).items()):
        codes = {
            row.course_code for row in state.plan_courses if row.plan_id == plan.id
        }
        if have <= codes and not avoid & codes:
            found.append({"plan": key, "name": plan.name, "hidden": plan.hidden})
    if found:
        return {"plans": found}
    reasons = [
        reason.message for reason in state.plan_reasons if reason.plan_id is None
    ]
    return {"plans": [], "reasons": reasons}


def verdict(state: StudentState, rulebook: Rulebook, code: str) -> Eligibility | None:
    # The engine's verdict on one course for her, or None for a code the 2026 handbook doesn't hold
    rules = rulebook.year(YEAR)
    course = next((course for course in rules.courses if course.code == code), None)
    if course is None:
        return None
    checked = EntryRuleEligibility().check(
        [course], state.course_history, rules, rulebook.symbols(), state.student
    )
    return checked[code]


def parse(spec: str) -> tuple[str, dict[str, Any]]:
    # The resolve column's form and its values, or Unresolved for one it can't read
    spec = spec.strip()
    if not spec:
        return "", {}
    kind, _, rest = spec.partition(":")
    if kind == "check_eligibility":
        code, _, predicted = rest.partition("=")
        if CODE.match(code) and predicted in VERDICTS:
            return kind, {"code": code, "predicted": predicted}
    elif kind == "find_plan":
        parts = dict(part.partition("=")[::2] for part in rest.split(";"))
        if set(parts) <= {"has", "avoid"} and parts:
            have, avoid = (
                {c for c in parts.get(n, "").split(",") if c} for n in ("has", "avoid")
            )
            if (have or avoid) and all(CODE.match(c) for c in have | avoid):
                return kind, {"have": sorted(have), "avoid": sorted(avoid)}
    elif kind == "clash":
        codes = rest.split(",")
        if len(codes) == 2 and all(CODE.match(code) for code in codes):
            return kind, {"codes": codes}
    elif kind == "week":
        tab, _, form = rest.partition(":")
        name, _, value = form.partition("=")
        if tab in ("sem1", "sem2", "winter", "summer"):
            if name in ("finish_after", "count_starts") and re.fullmatch(
                r"\d{2}:\d{2}", value
            ):
                return kind, {"tab": tab, "form": name, "at": value}
            if name == "day_load" and value[:3].lower() in DAYS:
                return kind, {"tab": tab, "form": name, "day": value[:3].lower()}
            if name == "free_days" and not value:
                return kind, {"tab": tab, "form": name}
    raise Unresolved(f"can't read the resolve spec {spec!r}")


def open_plans(note: str, state: StudentState) -> list[str]:
    # The plan she has open: V01, unless the note names one, or two for a pair
    named = list(dict.fromkeys(PLAN.findall(note)))
    if len(named) > 2 or any(key not in short_ids(state) for key in named):
        raise Unresolved(f"can't tell which plans the note opens: {note!r}")
    return named or ["V01"]


def open_slot(state: StudentState, key: str) -> bool:
    # Whether a plan leaves a complementary course to choose: only a slot's reason has details
    plan = short_ids(state)[key]
    return any(
        reason.details and reason.plan_id in (None, plan.id)
        for reason in state.plan_reasons
    )


def week_form(
    state: StudentState, key: str, rules: RuleSet, spec: dict[str, Any]
) -> dict[str, Any]:
    week = plan_week(state, key, rules, spec["tab"])
    form = spec["form"]
    if form == "finish_after":
        return finish_after(week, time.fromisoformat(spec["at"]))
    if form == "count_starts":
        return count_starts(week, time.fromisoformat(spec["at"]))
    if form == "day_load":
        return day_load(week, DAYS[spec["day"]])
    return free_days(week)


def evened(text: str) -> str:
    # Text as a quote is matched: print's curly quotes and dashes made plain, leaders gone, and runs
    # of spaces and line breaks made one space
    return " ".join(GAP.sub(" ", text.translate(PLAIN)).split())


def holding(quote: str, passages: Iterable[Passage]) -> list[Passage]:
    # The passages that hold every part of a quote, a part being what's left between its gaps
    parts = [part for part in map(evened, GAP.split(quote)) if part]
    return [
        p
        for p in passages
        if parts and all(part in evened(p.content) for part in parts)
    ]


def placed(
    row: Row, passages: Sequence[Passage], sliced: set[Any], about: Sequence[str]
) -> tuple[bool | None, str]:
    # Whether her slice holds the passage of the prompt's quote, None when it has no quote, and where
    # it was found. The quote counts only from its own context: a passage on its printed page, or
    # one that starts a page earlier and runs onto it, and, where the prompt is about a course, that
    # course's entry. So a sentence many entries print, such as the course handout's, never stands
    # in for the right one. A course SAGE holds no entry for is absent, which the declared referral
    # override covers. Any other quote no passage in context holds stops the run.
    if not row["quote"].strip():
        return None, ""
    page = int(row["page"])
    near = [p for p in holding(row["quote"], passages) if p.page in (page, page - 1)]
    theirs = [p for p in near if p.course_code in about]
    context = theirs or near
    if not context:
        held = {p.course_code for p in passages}
        missing = [code for code in about if code not in held]
        if missing:
            return (
                False,
                f"absent: SAGE's {YEAR} rulebook holds no entry for {', '.join(missing)}",
            )
        raise Unresolved(
            f"{row['id']}: no {YEAR} passage in its context holds its quote"
        )
    in_slice = any(passage.id in sliced for passage in context)
    sections = "; ".join(sorted({passage.section for passage in context}))
    return in_slice, f"{'in' if in_slice else 'out'}, page {row['page']}, {sections}"


def about(row: Row, spec: dict[str, Any], rules: RuleSet) -> list[str]:
    # The courses a prompt is about: its spec's, or else those its question names by code or name
    if "code" in spec:
        return [spec["code"]]
    if "codes" in spec:
        return list(spec["codes"])
    asked = row["prompt"].lower()
    return [
        course.code
        for course in rules.courses
        if course.code.lower() in asked or course.name.lower() in asked
    ]


def expected(
    row: Row, kind: str, engine: Eligibility | None, in_slice: bool | None
) -> tuple[str, str]:
    # Her prompt's expected behaviour once resolved, and why it moved, if it did. The engine decides
    # a verdict, and stops the run only where it contradicts the prompt's group, unless the prompt
    # is per_engine, which follows it. An answer that rests on the handbook alone, with nothing the engine or her plans serve,
    # becomes a referral when her slice doesn't hold its quote.
    behaviour, moved = row["expected_behaviour"], []
    if behaviour not in BEHAVIOURS:
        raise Unresolved(f"{row['id']}: unknown expected_behaviour {behaviour!r}")
    needed = GROUP_VERDICT.get(row["group"])
    if engine is not None and needed and engine.status != needed:
        # A per_engine row is a declared exception, as P22's was at input review: it follows the
        # engine whatever its group says, and the exception is logged
        if behaviour != "per_engine":
            raise Unresolved(
                f"{row['id']}: the engine says {engine.status}, against its group, "
                f"{row['group']}"
            )
        moved.append(
            f"declared group exception: {row['group']}, but the engine says {engine.status}"
        )
    if behaviour == "per_engine":
        if engine is None:
            raise Unresolved(
                f"{row['id']}: per_engine with no check_eligibility to follow"
            )
        behaviour = PER_ENGINE[engine.status]
        moved.append(f"per_engine: the engine says {engine.status}")
    # The engine or her plans serve an answer, except a verdict on a course SAGE doesn't hold
    served = kind and not (kind == "check_eligibility" and engine is None)
    if behaviour in ANSWERABLE and not served and in_slice is False:
        behaviour = "refer"
        moved.append("slice: her slice doesn't hold the quote's passage")
    return behaviour, "; ".join(moved)


def resolve(
    row: Row,
    state: StudentState,
    rulebook: Rulebook,
    sliced: set[Any],
) -> Row:
    rules = rulebook.year(YEAR)
    plans = open_plans(row["note"], state)
    names = short_ids(state)
    kind, spec = parse(row["resolve"])
    engine, data, words = None, {}, ""
    if kind == "check_eligibility":
        engine = verdict(state, rulebook, spec["code"])
        if engine is None:
            data = {"code": spec["code"], "status": "absent"}
            words = (
                f"The engine has no verdict on {spec['code']}: SAGE's {YEAR} handbook doesn't "
                "hold that course."
            )
        else:
            data = {"code": spec["code"], **engine.model_dump(mode="json")}
            words = f"The engine's verdict on {spec['code']} for her: {engine.status}."
            if engine.reason:
                words += f" Its reason: {engine.reason}"
    elif kind == "find_plan":
        data = find_plan(state, set(spec["have"]), set(spec["avoid"]))
        wanted = " and ".join(
            part
            for part in (
                f"with {', '.join(spec['have'])}" if spec["have"] else "",
                f"without {', '.join(spec['avoid'])}" if spec["avoid"] else "",
            )
            if part
        )
        if data["plans"]:
            listed = "; ".join(
                f"{p['plan']} {p['name']}"
                + (" (hidden from her plan list)" if p["hidden"] else "")
                for p in data["plans"]
            )
            words = f"Her plans {wanted}: {listed}."
        else:
            words = (
                f"None of her plans is {wanted}. The plan set's reasons: "
                + " ".join(data["reasons"])
            )
    elif kind == "clash":
        one, other = spec["codes"]
        data = clash(state, rules, one, other)
        if data["plans"]:
            words = " ".join(
                f"In {p['plan']} {p['name']}, {one} and {other} "
                + (
                    "clash."
                    if p["clash"]
                    else "clash only if she picks clashing alternatives."
                    if p["only_with_alternatives"]
                    else "don't clash."
                )
                for p in data["plans"]
            )
        else:
            words = (
                f"No plan of hers holds both {one} and {other}. Their timetabled meetings "
                + ("overlap." if data["timetables_overlap"] else "don't overlap.")
            )
    elif kind == "week":
        data = {key: week_form(state, key, rules, spec) for key in plans}
        words = " ".join(
            f"{key} {names[key].name}, {spec['tab']}: {json.dumps(found, ensure_ascii=False)}."
            + (
                " This plan still has a complementary slot to fill, so this is its week as "
                "scheduled now."
                if open_slot(state, key)
                else ""
            )
            for key, found in data.items()
        )
    in_slice, where = placed(row, rules.passages, sliced, about(row, spec, rules))
    behaviour, moved = expected(row, kind, engine, in_slice)
    return {
        "prompt": row["id"],
        "student": row["student"],
        "group": row["group"],
        "term": row["term"],
        "plans": " ".join(plans),
        "expected": behaviour,
        "moved": moved,
        "kind": kind,
        "predicted": spec.get("predicted", ""),
        "engine": engine.status if engine else data.get("status", ""),
        "slice": where,
        "data": json.dumps(data, ensure_ascii=False, sort_keys=True) if data else "",
        "words": " ".join(
            part
            for part in (
                "Open: " + "; ".join(f"{key} {names[key].name}" for key in plans) + ".",
                words,
            )
            if part
        ),
    }


def slice_ids(state: StudentState, rulebook: Rulebook) -> set[Any]:
    # The passages her slice holds, as the advisor chooses them: her curriculum's, the entries of
    # every course in her plan set and her favourites, and those naming neither, whichever plan is open
    students = store(state)
    chat = chats.start(students, ACCOUNT, state.plans[0].id, None)
    evidence = Evidence(chat, None, students, rulebook, EntryRuleEligibility())
    return {passage.id for passage in evidence.passages.values()}


def main() -> None:
    prompts = read_prompts()
    unknown = {row["student"] for row in prompts} - set(FILES)
    if unknown:
        raise SystemExit(f"prompts.csv names students with no file: {sorted(unknown)}")
    rules, rulebook = stores()
    states = {
        code: prepared(code, rules, rulebook)
        for code in dict.fromkeys(row["student"] for row in prompts)
    }
    sliced = {code: slice_ids(state, rulebook) for code, state in states.items()}
    resolved, problems = [], []
    for row in prompts:
        if row["term"] not in get_args(TermCode):
            problems.append(f"{row['id']}: unknown term {row['term']!r}")
            continue
        try:
            resolved.append(
                resolve(row, states[row["student"]], rulebook, sliced[row["student"]])
            )
        except Unresolved as problem:
            problems.append(str(problem))
    if problems:
        raise SystemExit("Nothing written. Unresolved:\n" + "\n".join(problems))
    RESULTS.mkdir(exist_ok=True)
    with (RESULTS / "resolved.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(resolved)
    moved = [row for row in resolved if row["moved"]]
    print(f"results/resolved.csv: {len(resolved)} prompts, {len(moved)} moved")
    for row in resolved:
        if row["predicted"] and row["predicted"] != row["engine"]:
            print(
                f"{row['prompt']}: predicted {row['predicted']}, the engine says {row['engine']}"
            )
        if ", not page" in row["slice"]:
            print(
                f"{row['prompt']}: its quote is found on another page: {row['slice']}"
            )


if __name__ == "__main__":
    main()
