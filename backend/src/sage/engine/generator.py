# The plan generator: every valid plan for her year, best first, with the reasons behind them. It
# reads her year of study from her record and sets out what a plan must hold: the core she still
# owes, the year's rules and any an earlier year left unmet, with what she has passed taken off, a
# credit minimum, and the complementary credits and 576-credit places a plan leaves to her. The
# solver lists every plan once, and the smallest conflict explains an empty set. The set comes back
# unwritten and not yet complete.
import logging
from collections.abc import Mapping, Sequence
from uuid import UUID, uuid5

from sage.engine import printed
from sage.engine.evaluator import Record, Verdict, evaluate
from sage.engine.facts import (
    FLOOR,
    Facts,
    Need,
    Problem,
    facts,
    need,
    take,
    untimed,
    verdicts,
)
from sage.engine.reasons import Reason, Reasons
from sage.engine.solver import Found, Solver
from sage.shared.base import Row
from sage.shared.rules import (
    COMPLEMENTARY,
    AllOfGroup,
    ChooseFromGroup,
    CreditsFromGroups,
    ResultSymbol,
    RuleSet,
    TotalCredits,
    YearRule,
    meetings_on,
)
from sage.shared.students import (
    CourseHistoryLine,
    Plan,
    PlanCourse,
    PlanReason,
    PlanSet,
    PlanSetRows,
    Student,
)

CAP = 50  # the plans a set keeps, best first
logger = logging.getLogger(__name__)

# Reasons by the plan they belong to, with the set's own under None
Said = dict[tuple[str, ...] | None, list[Reason]]


class Owed(Row):
    # A year rule she still has to meet, the earlier year it's owed from, if any, and its table
    need: Need
    year: int | None
    table: str | None


class Slot(Row):
    # Credits a plan leaves her to fill with approved complementary studies courses: a year's
    # complementary credits, or a 576-credit place
    credits: int
    table: str | None = None
    place: printed.Place | None = None


class ClingoPlanGenerator:
    def __init__(self) -> None:
        self._solver = Solver()

    def generate(
        self,
        student: Student,
        history: Sequence[CourseHistoryLine],
        rules: RuleSet,
        symbols: Mapping[str, ResultSymbol],
    ) -> PlanSetRows:
        (version,) = rules.handbook_versions
        plan_set = PlanSet(
            id=uuid5(student.id, f"plan_sets/{version.year}"),
            student_id=student.id,
            period=version.year,
            version=1,
        )
        year = Year(student, Record(student, history, rules, symbols), rules)
        if year.finished:
            return rows(plan_set, {None: [year.said.finished()]}, [], {}, ())
        found, written, problem = self._plans(year)
        ranked = sorted(
            (plan for plan in found if plan.courses),
            key=lambda plan: (len(plan.conditional), year.credits(plan), plan.courses),
        )
        if not ranked and not any(note.kind == "conflict" for note in year.notes):
            year.notes.append(year.said.nothing())
        if len(ranked) > CAP:
            logger.warning("Kept the best %s of %s plans", CAP, len(ranked))
            ranked = ranked[:CAP]
        candidates = (*problem.required, *problem.electives)
        chosen = {
            plan.courses: self._solver.choices(written, plan, candidates)
            if year.grouped & set(plan.courses)
            else {}
            for plan in ranked
        }
        said = year.reasons(ranked, problem, self._fits(year, problem, ranked))
        return rows(plan_set, said, ranked, chosen, problem.required)

    def _plans(self, year: "Year") -> tuple[list[Found], Facts, Problem]:
        # Every plan, once each current-year course that clashes with one she's repeating or owes
        # from an earlier year is left out (FB3.4). Any other conflict leaves none.
        while True:
            problem = year.problem()
            written = facts(problem, year.rules, year.record)
            found = self._solver.plans(written)
            if found:
                return found, written, problem
            core = self._solver.conflict(written, year.order(problem))
            if not year.drop(core, problem):
                year.notes.append(year.conflict(core, problem))
                return [], written, problem

    def _fits(
        self, year: "Year", problem: Problem, ranked: Sequence[Found]
    ) -> dict[tuple[str, ...], tuple[str, ...]]:
        # The approved complementary courses that fit each plan's timetable, when it has a slot
        if not year.slots:
            return {}
        written = facts(problem, year.rules, year.record, year.extras(problem))
        candidates = (*problem.required, *problem.electives)
        return {
            plan.courses: self._solver.fits(written, plan, candidates)
            for plan in ranked
        }


class Year:
    # Her year of study as a plan must meet it
    def __init__(self, student: Student, record: Record, rules: RuleSet) -> None:
        self.student, self.record, self.rules = student, record, rules
        self.curriculum = student.curriculum_code
        self.said = Reasons(rules, self.curriculum)
        # The set's reasons found while setting the year out
        self.notes: list[Reason] = []
        self._credits = {course.code: course.credits for course in rules.courses}
        self._labels = {group.group_key: group.label for group in rules.course_groups}
        self._by_year = {
            rule.year_of_study: rule.rule.all
            for rule in rules.curriculum_rules
            if rule.curriculum_code == self.curriculum
        }
        self.number = record.year
        self.finished = self.number not in self._by_year
        self.required: list[str] = []
        # Required, and repeated or owed from an earlier year
        self.first: set[str] = set()
        self.current: list[str] = []  # required from her own year
        self.arrears: dict[int, list[str]] = {}
        self.owed: list[Owed] = []
        # Courses whose rule her record doesn't meet
        self.left_out: dict[str, Verdict] = {}
        self.dropped: set[str] = set()  # current-year courses an FB3.4 clash leaves out
        self.total = 0
        self.slots: list[Slot] = []
        self.grouped: set[str] = set()
        if self.finished:
            return
        complementary = []
        for number in sorted(self._by_year):
            if number > self.number:
                break
            self._core(number)
            for part in self._by_year[number]:
                if isinstance(part, CreditsFromGroups) and part.from_groups == (
                    COMPLEMENTARY,
                ):
                    complementary.append((number, part.credits))
                elif isinstance(part, ChooseFromGroup | CreditsFromGroups):
                    self._owe(number, part)
                elif isinstance(part, TotalCredits) and number == self.number:
                    self.total = part.total_credits
        self.slots = self._slots(complementary)
        self.grouped = {
            code
            for code in self._candidates()
            if any(
                slot.choice_group for slot in meetings_on(rules, self.curriculum, code)
            )
        }

    def credits(self, plan: Found) -> int:
        return sum(self._credits[code] for code in plan.courses)

    def _core(self, number: int) -> None:
        # A year's core she still owes. Practical training is never in a plan, and a result still to
        # come is taken as passed, each with its reason.
        for part in self._by_year[number]:
            if not isinstance(part, AllOfGroup):
                continue
            for code in self.record.members[part.all_of_group]:
                if code.endswith("X"):
                    if self.record.passed(code) is None:
                        self.notes.append(self.said.practical(code))
                    continue
                pending = self.record.pending(code)
                if pending:
                    self.notes.append(self.said.pending(code, pending))
                if self.record.done(code):
                    continue
                self.required.append(code)
                if number < self.number:
                    self.arrears.setdefault(number, []).append(code)
                else:
                    self.current.append(code)
                if number < self.number or self.record.repeated(code):
                    self.first.add(code)

    def _owe(self, number: int, part: ChooseFromGroup | CreditsFromGroups) -> None:
        # A choose or credits rule, less what she has done towards it
        members = list(
            dict.fromkeys(
                code for group in groups(part) for code in self.record.members[group]
            )
        )
        done = [code for code in members if self.record.done(code)]
        if isinstance(part, ChooseFromGroup):
            kind, left = "courses", part.choose - len(done)
        else:
            kind, left = "credits", part.credits - sum(self._credits[c] for c in done)
        if left > 0:
            courses = tuple(code for code in members if code not in done)
            self.owed.append(
                Owed(
                    need=Need(kind=kind, amount=left, courses=courses),
                    year=number if number < self.number else None,
                    table=self._heading(groups(part)),
                )
            )

    def _slots(self, complementary: list[tuple[int, int]]) -> list[Slot]:
        # Complementary credits and 576-credit places still to fill. Her passed complementary
        # courses meet the years' complementary credits first, largest first so the fewest are
        # used, and each one left over fills a place, earliest first.
        passed = sorted(
            (
                self._credits[code]
                for code in self.record.members[COMPLEMENTARY]
                if self.record.done(code)
            ),
            reverse=True,
        )
        slots = []
        for number, credits in complementary:
            while credits > 0 and passed:
                credits -= passed.pop(0)
            if credits > 0:
                slots.append(Slot(credits=credits, table=self._core_table(number)))
        (version,) = self.rules.handbook_versions
        if version.year != printed.PLACES_YEAR or not self._before_change():
            return slots
        for place in printed.PLACES.get(self.curriculum or "", ()):
            if place.year > self.number or self.record.done(place.code):
                continue
            filling = [at for at, worth in enumerate(passed) if worth >= place.credits]
            if filling:
                passed.pop(filling[0])
            else:
                slots.append(Slot(credits=place.credits, place=place))
        return slots

    def _before_change(self) -> bool:
        # Registered before the 560-credit curriculum started
        return (self.student.intake_year or printed.CHANGE) < printed.CHANGE

    def _candidates(self) -> list[str]:
        electives = [code for owed in self.owed for code in owed.need.courses]
        return list(dict.fromkeys([*self.required, *electives]))

    def minimum(self) -> int:
        # The year's total, less the credits of her year's courses she has done or can't take, and
        # in her final year at least what's left of the degree. It needs no check against the core,
        # which every plan holds.
        named = {
            code
            for part in self._by_year[self.number]
            for group in groups(part)
            if group != COMPLEMENTARY
            for code in self.record.members[group]
        }
        done = sum(self._credits[code] for code in named if self.record.done(code))
        gone = sum(
            self._credits[code]
            for code in self.current
            if code in self.left_out or code in self.dropped
        )
        least = self.total - done - gone
        (version,) = self.rules.handbook_versions
        degree = printed.DEGREE_CREDITS.get(version.year, {}).get(self.curriculum or "")
        if degree and self.number == max(self._by_year):
            total = degree[0] if self._before_change() else degree[1]
            least = max(least, total - self.record.passed_credits)
        return least

    def problem(self) -> Problem:
        # What the solver gets, once each course whose rule her record can't meet is left out, and
        # then each course that needed one of them, until none is left
        while True:
            gone = set(self.left_out) | self.dropped
            required = tuple(code for code in self.required if code not in gone)
            needs = tuple(
                Need(
                    kind=owed.need.kind,
                    amount=owed.need.amount,
                    courses=tuple(c for c in owed.need.courses if c not in gone),
                )
                for owed in self.owed
            )
            electives = tuple(
                code
                for code in self._candidates()
                if code not in required and code not in gone
            )
            floor = self.minimum() - sum(slot.credits for slot in self.slots)
            problem = Problem(
                required=required, electives=electives, needs=needs, floor=max(floor, 0)
            )
            failing = {
                code: verdict
                for code, verdict in verdicts(problem, self.rules, self.record).items()
                if verdict.value == "not_met"
            }
            if not failing:
                return problem
            self.left_out.update(failing)

    def order(self, problem: Problem) -> list[str]:
        # The switches a conflict is traced through. Her own year's courses leave the core first,
        # and those she's repeating or owes from an earlier year last, so a clash between the two
        # ends with one of each.
        current = [take(code) for code in problem.required if code not in self.first]
        rules = [need(number) for number in range(len(problem.needs))]
        floor = [FLOOR] if problem.floor else []
        first = [take(code) for code in problem.required if code in self.first]
        return [*current, *rules, *floor, *first]

    def drop(self, core: list[str], problem: Problem) -> bool:
        # A current-year course that clashes with one she's repeating or owes from an earlier year
        # is left out (FB3.4), so the plans can go on without it
        switched = {take(code): code for code in problem.required}
        pair = [switched[switch] for switch in core if switch in switched]
        kept = [code for code in pair if code in self.first]
        if len(core) != 2 or len(pair) != 2 or len(kept) != 1:
            return False
        (dropped,) = set(pair) - set(kept)
        owed = any(kept[0] in codes for codes in self.arrears.values())
        self.dropped.add(dropped)
        self.notes.append(self.said.precedence(dropped, kept[0], repeated=not owed))
        return True

    def conflict(self, core: list[str], problem: Problem) -> Reason:
        courses = [code for code in problem.required if take(code) in core]
        broken = [n for n in range(len(problem.needs)) if need(n) in core]
        table = self.owed[broken[0]].table if broken else self._last_table()
        return self.said.conflict(
            courses,
            [problem.needs[n] for n in broken],
            problem.floor if FLOOR in core else None,
            table,
        )

    def extras(self, problem: Problem) -> tuple[str, ...]:
        # The approved complementary courses a slot could list: not done, not a plan course, and
        # with an entry rule her record doesn't fail
        rules = {course.code: course.entry_rule for course in self.rules.courses}
        candidates = {*problem.required, *problem.electives}
        return tuple(
            code
            for code in sorted(set(self.record.members[COMPLEMENTARY]) - candidates)
            if not self.record.done(code)
            and evaluate(rules[code], self.record).value != "not_met"
        )

    def reasons(
        self,
        ranked: Sequence[Found],
        problem: Problem,
        fits: Mapping[tuple[str, ...], tuple[str, ...]],
    ) -> Said:
        said = self.said
        found: Said = {None: self._rules(problem, bool(ranked))}
        found.update({plan.courses: [] for plan in ranked})
        opened = verdicts(problem, self.rules, self.record).items()
        for code, verdict in sorted(opened):
            if verdict.value != "open":
                continue
            unsure = [plan for plan in ranked if code in plan.unsure]
            met = [p for p in ranked if code in p.courses and code not in p.unsure]
            attach(found, ranked, unsure, said.unsure(code, verdict.rest))
            every = len(met) == len(ranked)
            attach(found, ranked, met, said.met_by_plan(code, verdict.rest, every))
        held = sorted({code for plan in ranked for code in plan.courses})
        for code in held:
            if untimed(code, self.rules, self.curriculum):
                holding = [plan for plan in ranked if code in plan.courses]
                attach(found, ranked, holding, said.untimed(code))
        for plan in ranked:
            for slot in self.slots:
                fit = [
                    code
                    for code in fits[plan.courses]
                    if not slot.place or self._credits[code] >= slot.place.credits
                ]
                late = [c for c in fit if untimed(c, self.rules, self.curriculum)]
                found[plan.courses].append(
                    said.slot(slot.credits, slot.table, fit, late, slot.place)
                )
        return found

    def _rules(self, problem: Problem, any_plan: bool) -> list[Reason]:
        # The set's reasons that hold whatever plan she picks
        said = self.said
        whole = []
        current = [code for code in self.current if code in problem.required]
        if current:
            whole.append(said.core(current, self._core_table(self.number)))
        for number, codes in sorted(self.arrears.items()):
            owed = [code for code in codes if code in problem.required]
            if owed:
                whole.append(said.arrears(owed, number, self._core_table(number)))
        whole += [
            said.need(rule, owed.year, owed.table)
            for owed, rule in zip(self.owed, problem.needs, strict=True)
        ]
        if any_plan:
            whole.append(
                said.minimum(self.minimum(), self._last_table(), bool(self.slots))
            )
        electives = [owed for owed in self.owed if owed.year is None]
        if electives:
            note = printed.ALL_THREE.get((self.curriculum or "", self.number))
            whole.append(said.more_electives(electives[0].table, note))
        same = printed.SAME_SLOTS.get((self.curriculum or "", self.number))
        if same:
            whole.append(said.same_slots(same))
        if not self.rules.timetable_slots:
            whole.append(said.unchecked())
        whole += self.notes
        whole += [
            said.excluded(code, verdict.rest, code in self.required)
            for code, verdict in sorted(self.left_out.items())
        ]
        return whole

    def _heading(self, keys: Sequence[str]) -> str | None:
        # The first of these groups whose table has a passage
        return next(
            (
                self._labels[key]
                for key in keys
                if self.said.table(self._labels[key]) is not None
            ),
            None,
        )

    def _core_table(self, number: int) -> str | None:
        return self._heading(
            [p.all_of_group for p in self._by_year[number] if isinstance(p, AllOfGroup)]
        )

    def _last_table(self) -> str | None:
        # The year's last table, which prints its total
        position = {
            passage.section: passage.position
            for passage in self.rules.passages
            if passage.curriculum_code == self.curriculum
        }
        headings = [
            self._labels[group]
            for part in self._by_year[self.number]
            for group in groups(part)
            if self._labels.get(group) in position
        ]
        return max(headings, key=position.__getitem__, default=None)


def groups(part: YearRule) -> tuple[str, ...]:
    # The groups a year rule names
    if isinstance(part, AllOfGroup):
        return (part.all_of_group,)
    if isinstance(part, ChooseFromGroup):
        return (part.from_group,)
    if isinstance(part, CreditsFromGroups):
        return part.from_groups
    return ()


def attach(
    found: Said, ranked: Sequence[Found], plans: Sequence[Found], reason: Reason
) -> None:
    # A reason true of every plan is the set's, and one true of only some is each of theirs
    if not plans:
        return
    if len(plans) == len(ranked):
        found[None].append(reason)
        return
    for plan in plans:
        found[plan.courses].append(reason)


def name(courses: Sequence[str], required: Sequence[str]) -> str:
    # A plan is named by its electives, in code order
    electives = [code for code in courses if code not in required]
    if not electives:
        return "Core courses only"
    if len(electives) == 1:
        return electives[0]
    return f"{', '.join(electives[:-1])} & {electives[-1]}"


def rows(
    plan_set: PlanSet,
    said: Said,
    ranked: Sequence[Found],
    chosen: Mapping[tuple[str, ...], dict[str, dict[str, str]]],
    required: Sequence[str],
) -> PlanSetRows:
    # The set as stored, with ids made from her id, the year and each plan's courses, so a retried
    # onboarding writes the same rows
    student, period = plan_set.student_id, plan_set.period
    ids: dict[tuple[str, ...] | None, UUID | None] = {None: None}
    plans, courses = [], []
    for position, found in enumerate(ranked, start=1):
        plan_id = uuid5(student, f"plans/{period}/{'+'.join(found.courses)}")
        ids[found.courses] = plan_id
        plans.append(
            Plan(
                id=plan_id,
                plan_set_id=plan_set.id,
                student_id=student,
                position=position,
                name=name(found.courses, required),
            )
        )
        courses += [
            PlanCourse(
                plan_id=plan_id,
                course_code=code,
                student_id=student,
                handbook_year=period,
                choices=chosen[found.courses].get(code),
            )
            for code in found.courses
        ]
    reasons = [
        PlanReason(
            id=uuid5(student, f"plan_reasons/{period}/{number}"),
            plan_set_id=plan_set.id,
            student_id=student,
            plan_id=ids[key],
            **reason.model_dump(),
        )
        for number, (key, reason) in enumerate(
            (key, reason) for key, listed in said.items() for reason in listed
        )
    ]
    return PlanSetRows(
        plan_set=plan_set,
        plans=tuple(plans),
        plan_courses=tuple(courses),
        plan_reasons=tuple(reasons),
    )
