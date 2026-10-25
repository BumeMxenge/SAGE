# Rule trees in plain words, as a reviewer compares them with print and as the engine's reasons and
# the advisor word them, such as "MEC1009F or MEC1009S, and one of MEC2023F, MEC2023S, MEC2047F or
# MEC2047S". "or" binds tighter than ", and", so an all inside another node is bracketed, and so is
# a list with commas of its own in the middle of an all, where its commas would run into the all's.
from sage.shared.rules import (
    AllOf,
    AllOfGroup,
    AnyOf,
    ChooseFromGroup,
    CourseNeed,
    CreditsFromGroups,
    EntryRule,
    MinYearOfStudy,
    StudentIn,
    YearRule,
    YearRules,
    continues,
)


def in_words(rule: EntryRule | YearRules | None, quoted: bool = False) -> str:
    # Quoted, as a student's reasons have it, a refer leaf is its printed text alone, in quotes,
    # and words that continue a list, such as "or equivalent", follow it with no "or" of their own
    if rule is None:
        return "no requirement"
    if isinstance(rule, YearRules):
        return all_of([_part(part) for part in rule.all], listed=True)
    return _words(rule, quoted=quoted)


def _words(node: EntryRule, nested: bool = False, quoted: bool = False) -> str:
    if isinstance(node, AllOf):
        listed = any(_lists(child) for child in node.all)
        # A tree joins an all inside an all, so a child here is never an all
        words = [
            f"({_words(child, quoted=quoted)})"
            if _commas(child, quoted) and at < len(node.all) - 1
            else _words(child, quoted=quoted)
            for at, child in enumerate(node.all)
        ]
        return f"({all_of(words, listed)})" if nested else all_of(words, listed)
    if isinstance(node, AnyOf):
        listed, after = _branches(node, quoted)
        words = _one_of([_words(child, True, quoted) for child in listed])
        return " ".join([words, *(_words(child, quoted=quoted) for child in after)])
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
    return f'"{node.refer}"' if quoted else f'a person\'s judgement of "{node.refer}"'


def _part(part: YearRule) -> str:
    if isinstance(part, AllOfGroup):
        return f"every course in {part.all_of_group}"
    if isinstance(part, ChooseFromGroup):
        courses = "course" if part.choose == 1 else "courses"
        return f"{part.choose} {courses} from {part.from_group}"
    if isinstance(part, CreditsFromGroups):
        return f"at least {part.credits} credits from {_one_of(list(part.from_groups))}"
    return f"{part.total_credits} credits in total"


def _lists(node: EntryRule) -> bool:
    # Whether a node's words hold a list of their own. An all never sits inside an all, as a tree
    # joins them.
    if isinstance(node, StudentIn):
        return len(node.student_in) > 1
    return isinstance(node, AnyOf)


def _commas(node: EntryRule, quoted: bool) -> bool:
    # Whether a node's words separate items with commas: one of three or more listed. A student_in,
    # which sorts last among its siblings, never sits in the middle of an all.
    return isinstance(node, AnyOf) and len(_branches(node, quoted)[0]) > 2


def _branches(node: AnyOf, quoted: bool) -> tuple[list[EntryRule], list[EntryRule]]:
    # The branches an any lists, and, quoted, the words that continue the list, which follow it.
    # Unquoted, they're a person's judgement like any other branch.
    if not quoted:
        return list(node.any), []
    return (
        [child for child in node.any if not continues(child)],
        [child for child in node.any if continues(child)],
    )


def all_of(words: list[str], listed: bool = False) -> str:
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
