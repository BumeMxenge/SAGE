# Rule trees in plain words, as a reviewer compares them with print and as the engine's reasons and
# the advisor will word them, such as "MEC1009F or MEC1009S, and one of MEC2023F, MEC2023S, MEC2047F
# or MEC2047S". "or" binds tighter than ", and", so an all inside another node is bracketed, and so is
# a list with commas of its own in the middle of an all, where its commas would run into the all's.
from sage.domain.rules import (
    AllOf,
    AllOfGroup,
    AnyOf,
    ChooseFromGroup,
    CourseNeed,
    CreditsFromGroups,
    EntryRule,
    MinYearOfStudy,
    Refer,
    StudentIn,
    TotalCredits,
    YearRule,
    YearRules,
)


def in_words(rule: EntryRule | YearRules | None) -> str:
    if rule is None:
        return "no requirement"
    if isinstance(rule, YearRules):
        return _all([_part(part) for part in rule.all], listed=True)
    return _words(rule)


def _words(node: EntryRule, nested: bool = False) -> str:
    if isinstance(node, AllOf):
        listed = any(_lists(child) for child in node.all)
        words = [
            f"({_words(child)})"
            if _commas(child) and at < len(node.all) - 1
            else _words(child, True)
            for at, child in enumerate(node.all)
        ]
        return f"({_all(words, listed)})" if nested else _all(words, listed)
    if isinstance(node, AnyOf):
        return _one_of([_words(child, True) for child in node.any])
    if isinstance(node, CourseNeed):
        if node.need == "concurrent":
            return f"{node.course} taken alongside"
        if node.need == "mark":
            return f"at least {node.min_mark}% in {node.course}"
        return node.course
    if isinstance(node, StudentIn):
        return f"a student on {_one_of(list(node.student_in))}"
    if isinstance(node, MinYearOfStudy):
        return f"year of study {node.min_year_of_study} or later"
    if isinstance(node, Refer):
        return f'a person\'s judgement of "{node.refer}"'
    raise TypeError(f"no words for {node!r}")


def _part(part: YearRule) -> str:
    if isinstance(part, AllOfGroup):
        return f"every course in {part.all_of_group}"
    if isinstance(part, ChooseFromGroup):
        courses = "course" if part.choose == 1 else "courses"
        return f"{part.choose} {courses} from {part.from_group}"
    if isinstance(part, CreditsFromGroups):
        return f"at least {part.credits} credits from {_one_of(list(part.from_groups))}"
    if isinstance(part, TotalCredits):
        return f"{part.total_credits} credits in total"
    raise TypeError(f"no words for {part!r}")


def _lists(node: EntryRule) -> bool:
    # Whether a node's words hold a list of their own
    if isinstance(node, StudentIn):
        return len(node.student_in) > 1
    return isinstance(node, AllOf | AnyOf)


def _commas(node: EntryRule) -> bool:
    # Whether a node's words separate items with commas: one of three or more. A student_in, which
    # sorts last among its siblings, never sits in the middle of an all.
    return isinstance(node, AnyOf) and len(node.any) > 2


def _all(words: list[str], listed: bool) -> str:
    # Parts that must all hold: "A and B", or "X, and Y" where a part holds a list of its own
    if len(words) == 1:
        return words[0]
    return f"{', '.join(words[:-1])}{',' if listed else ''} and {words[-1]}"


def _one_of(words: list[str]) -> str:
    # Parts of which one must hold: "A or B", or "one of A, B or C"
    if len(words) == 1:
        return words[0]
    if len(words) == 2:
        return f"{words[0]} or {words[1]}"
    return f"one of {', '.join(words[:-1])} or {words[-1]}"
