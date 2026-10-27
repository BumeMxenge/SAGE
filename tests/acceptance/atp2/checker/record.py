# Her record as SEMANTICS.md reads it: what each line's result means, from the result_symbols
# table, and which codes each line covers: its own, then at most one equivalence step and one
# offering step, in either order (Covers)
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

from sage.shared.rules import Outcome, ResultSymbol, RuleSet
from sage.shared.students import CourseHistoryLine

PASSED = frozenset({"pass", "credited"})
# A result still to come counts as passed for her year, her outstanding core and her plans, which
# assume she passes, but not for the final year's floor (Courses she can't take yet)
DONE = PASSED | {"in_progress", "supp_pending"}
FAILED = frozenset({"fail"})


class Covers:
    # Which codes a pass covers, from the year's equivalences and the offerings it holds
    def __init__(self, rules: RuleSet) -> None:
        self.counts_as: dict[str, set[str]] = defaultdict(set)
        for row in rules.equivalences:
            self.counts_as[row.course_code].add(row.counts_as)
        self.stems: dict[str, dict[str, int]] = defaultdict(dict)
        for course in rules.courses:
            self.stems[course.code[:7]][course.code] = course.credits

    def offerings(self, code: str, credits: int) -> set[str]:
        # The other offerings the rules hold with the same first seven characters, at her line's
        # credits. An offering the rules don't hold gives no cover.
        return {
            other
            for other, worth in self.stems.get(code[:7], {}).items()
            if other != code and worth == credits
        }

    def __call__(self, code: str, credits: int) -> frozenset[str]:
        equivalent = self.counts_as.get(code, set())
        offered = self.offerings(code, credits)
        return frozenset(
            {code, *equivalent, *offered}
            | {then for other in offered for then in self.counts_as.get(other, ())}
            | {then for other in equivalent for then in self.offerings(other, credits)}
        )


@dataclass(frozen=True)
class Line:
    code: str
    credits: int
    outcome: Outcome
    mark: int | None  # the final mark, where a supplementary pass (SP) counts as 50
    covers: frozenset[str]


class Record:
    def __init__(
        self,
        history: Sequence[CourseHistoryLine],
        covers: Covers,
        symbols: Mapping[str, ResultSymbol],
    ) -> None:
        self.lines = tuple(
            Line(
                code=line.course_code,
                credits=line.credits,
                outcome=symbols[line.result].outcome,
                mark=50 if line.result == "SP" else line.mark,
                covers=covers(line.course_code, line.credits),
            )
            for line in history
        )

    def has(self, code: str, outcomes: frozenset[str]) -> bool:
        # Whether a line with one of these outcomes covers the code
        return any(
            code in line.covers and line.outcome in outcomes for line in self.lines
        )

    def matched(self, codes: Iterable[str]) -> set[str]:
        # The codes her passed or pending lines meet, each line counting once however many codes
        # it covers (Group rules): a matching of lines to codes, grown by augmenting paths
        wanted = set(codes)
        lines = [
            line for line in self.lines if line.outcome in DONE and line.covers & wanted
        ]
        owner: dict[str, int] = {}

        def assign(i: int, seen: set[str]) -> bool:
            for code in sorted(lines[i].covers & wanted):
                if code not in seen:
                    seen.add(code)
                    if code not in owner or assign(owner[code], seen):
                        owner[code] = i
                        return True
            return False

        for i in range(len(lines)):
            assign(i, set())
        return set(owner)
