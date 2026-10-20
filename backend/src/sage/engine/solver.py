# Runs plans.lp over one student's facts with clingo, the engine's only use of it: every plan once,
# the courses that fit beside a plan, the alternatives every way of attending a plan shares, and the
# smallest set of requirements that leaves no plan.
from collections.abc import Collection, Sequence
from pathlib import Path

import clingo

from sage.engine.facts import Facts
from sage.shared.base import Row

ENCODING = Path(__file__).with_name("plans.lp")

# A switch and whether it's on
Assumption = tuple[clingo.Symbol, bool]


class Found(Row):
    # One plan, by its courses, and the courses it holds only conditionally
    courses: tuple[str, ...]
    conditional: tuple[str, ...]


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
    ) -> tuple[str, ...]:
        # The extra courses some way of attending the plan leaves room for: clingo's brave mode
        # keeps whatever at least one answer set holds
        control = self._ground(facts, "--enum-mode=brave", "--models=0")
        return named(self._last(control, fixed(facts, plan, candidates, off)), "add")

    def choices(
        self,
        facts: Facts,
        plan: Found,
        candidates: Collection[str],
        off: Collection[str] = (),
    ) -> dict[str, dict[str, str]]:
        # The alternatives every clash-free way of attending the plan uses: clingo's cautious mode
        # keeps only what every answer set holds
        control = self._ground(facts, "--enum-mode=cautious", "--models=0")
        chosen: dict[str, dict[str, str]] = {}
        for atom in self._last(control, fixed(facts, plan, candidates, off)):
            if atom.name == "pick":
                code, group, choice = (argument.string for argument in atom.arguments)
                chosen.setdefault(code, {})[group] = choice
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


def named(atoms: Sequence[clingo.Symbol], name: str) -> tuple[str, ...]:
    # The course codes in the atoms with this name
    return tuple(
        sorted(atom.arguments[0].string for atom in atoms if atom.name == name)
    )
