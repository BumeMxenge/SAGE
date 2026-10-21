# Runs plans.lp over one student's facts with clingo, the engine's only use of it: every plan once,
# the courses that fit beside a plan, with their sections and any of the plan's they force, the
# alternatives of each of a plan's choice groups that fit it, and the smallest set of requirements
# that leaves no plan.
from collections.abc import Collection, Sequence
from pathlib import Path

import clingo

from sage.engine.facts import Facts
from sage.shared.base import Row

ENCODING = Path(__file__).with_name("plans.lp")

# A switch and whether it's on
Assumption = tuple[clingo.Symbol, bool]


class Found(Row):
    # One plan, by its courses, the courses it holds only conditionally, and those of them whose
    # entry rule only possibly holds
    courses: tuple[str, ...]
    conditional: tuple[str, ...]
    unsure: tuple[str, ...]


class Fit(Row):
    # A course some way of attending a plan leaves room for, the sections of it that fit, by choice
    # group, and the section of a plan's course it forces, where its own meetings rule out the others
    code: str
    sections: dict[str, list[str]]
    forced: dict[str, dict[str, str]]


class Solver:
    def __init__(self) -> None:
        # Read once, when the app builds the engine, so a missing file stops it starting
        self._encoding = ENCODING.read_text(encoding="utf-8")

    def plans(self, facts: Facts, off: Collection[str] = ()) -> list[Found]:
        # Every plan, each once however many ways there are to attend it, as projection onto take/1
        # compares answer sets by their courses alone. Switches in off stay off.
        control = self._ground(facts, "--models=0", "--project", parts=("plans",))
        found: list[Found] = []

        def keep(model: clingo.Model) -> None:
            atoms = model.symbols(shown=True)
            found.append(
                Found(
                    courses=named(atoms, "take"),
                    conditional=named(atoms, "conditional"),
                    unsure=named(atoms, "unsure"),
                )
            )

        control.solve(assumptions=switched(facts, off), on_model=keep)
        return found

    def fits(
        self,
        facts: Facts,
        plan: Found,
        candidates: Collection[str],
        off: Collection[str] = (),
    ) -> list[Fit]:
        # The extra courses some way of attending the plan leaves room for, with their sections
        # that fit: clingo's brave mode keeps whatever at least one answer set holds. A course whose
        # meetings could rule out a section of the plan's is then tried alone in cautious mode, and
        # the plan's section it leaves in every answer set is the one it forces.
        assumptions = fixed(facts, plan, candidates, off)
        brave = self._last(
            self._ground(facts, "--enum-mode=brave", "--models=0"), assumptions
        )
        blocking = {
            atom.arguments[0].string for atom in brave if atom.name == "blocked"
        }
        cautious = self._ground(facts, "--enum-mode=cautious", "--models=0")
        found = []
        for code in named(brave, "add"):
            sections: dict[str, list[str]] = {}
            for course, group, choice in sorted(picks(brave)):
                if course == code:
                    sections.setdefault(group, []).append(choice)
            forced = (
                self._forced(cautious, assumptions, code) if code in blocking else {}
            )
            found.append(Fit(code=code, sections=sections, forced=forced))
        return found

    def _forced(
        self, control: clingo.Control, assumptions: list[Assumption], code: str
    ) -> dict[str, dict[str, str]]:
        # The plan's sections that every answer set with the course added picks, where the
        # course's own meetings rule out another of the same group
        added = (clingo.Function("add", [clingo.String(code)]), True)
        every = self._last(control, [*assumptions, added])
        ruled = {
            (atom.arguments[1].string, atom.arguments[2].string)
            for atom in every
            if atom.name == "blocked"
        }
        forced: dict[str, dict[str, str]] = {}
        for course, group, choice in picks(every):
            if (course, group) in ruled:
                forced.setdefault(course, {})[group] = choice
        return forced

    def choices(
        self,
        facts: Facts,
        plan: Found,
        candidates: Collection[str],
        off: Collection[str] = (),
    ) -> dict[str, dict[str, list[str]]]:
        # Each choice group's alternatives that some clash-free way of attending the whole plan
        # uses, sorted: clingo's brave mode keeps whatever at least one answer set holds. One left
        # is the only one that fits.
        control = self._ground(facts, "--enum-mode=brave", "--models=0")
        chosen: dict[str, dict[str, list[str]]] = {}
        for code, group, choice in sorted(
            picks(self._last(control, fixed(facts, plan, candidates, off)))
        ):
            chosen.setdefault(code, {}).setdefault(group, []).append(choice)
        return chosen

    def conflict(
        self, facts: Facts, order: Sequence[str], off: Collection[str] = ()
    ) -> list[str]:
        # With no plan, the smallest set of switches that leaves none. clingo returns a set that
        # does, its core; each of its switches is then dropped, in the order given, if the rest
        # still leave no plan, so the switches given first leave first.
        control = self._ground(facts)
        literal = {
            control.symbolic_atoms[on(switch)].literal: switch
            for switch in facts.switches
        }
        core: list[int] = []
        control.solve(assumptions=switched(facts, off), on_core=core.extend)
        found = {literal[number] for number in core}
        kept = [switch for switch in order if switch in found]
        held_off = [(on(switch), False) for switch in off]
        for switch in list(kept):
            trial = [other for other in kept if other != switch]
            result = control.solve(
                assumptions=[(on(other), True) for other in trial] + held_off
            )
            if result.unsatisfiable:
                kept = trial
        return kept

    def _ground(
        self, facts: Facts, *arguments: str, parts: Sequence[str] = ()
    ) -> clingo.Control:
        control = clingo.Control(list(arguments))
        control.add(self._encoding)
        control.add(facts.text)
        control.ground([("base", ()), *((part, ()) for part in parts)])
        return control

    def _last(
        self, control: clingo.Control, assumptions: list[Assumption]
    ) -> Sequence[clingo.Symbol]:
        # The last answer set's shown atoms, which in brave and cautious mode hold the consequences
        last: list[clingo.Symbol] = []

        def keep(model: clingo.Model) -> None:
            last[:] = model.symbols(shown=True)

        control.solve(assumptions=assumptions, on_model=keep)
        return last


def on(switch: str) -> clingo.Symbol:
    return clingo.parse_term(f"on({switch})")


def switched(facts: Facts, off: Collection[str] = ()) -> list[Assumption]:
    # Every switch on, except those in off
    return [(on(switch), switch not in off) for switch in facts.switches]


def fixed(
    facts: Facts, plan: Found, candidates: Collection[str], off: Collection[str]
) -> list[Assumption]:
    # Exactly the plan's courses taken, with the switches as they were when it was found
    taken = [
        (clingo.Function("take", [clingo.String(code)]), code in plan.courses)
        for code in candidates
    ]
    return switched(facts, off) + taken


def picks(atoms: Sequence[clingo.Symbol]) -> list[tuple[str, str, str]]:
    # Each course, choice group and alternative the atoms pick
    return [
        (code.string, group.string, choice.string)
        for code, group, choice in (
            atom.arguments for atom in atoms if atom.name == "pick"
        )
    ]


def named(atoms: Sequence[clingo.Symbol], name: str) -> tuple[str, ...]:
    # The course codes in the atoms with this name
    return tuple(
        sorted(atom.arguments[0].string for atom in atoms if atom.name == name)
    )
