# Reads one printed entry requirement or co-requisite into an EntryRule. It accepts only wording with
# exactly one reading: course codes, where EEE2046F/S means either term's course, joined by "or", or
# by "and" and commas, with brackets to group, or "None". Anything else is refused with its cause,
# and a model drafts that tree for a person to check.
#
# Developed only from the requirements of the courses the six EEE curricula list, in the 2023 and
# 2026 handbooks. It is frozen once branch B's E2 has run: a later change is logged in
# docs/shortfalls.md with its date and reason, and E2 is rerun.
import re
from typing import Literal

from sage.domain.rules import AllOf, AnyOf, CourseNeed, EntryRule, RefusalCause

# Wording only a person can judge, in the order a reviewer most needs to see it: a string carrying
# several is refused for the first
JUDGED: tuple[tuple[RefusalCause, re.Pattern[str]], ...] = (
    ("refused_school_result", re.compile(r"\bNSC\b|\bA-level\b")),
    ("refused_programme", re.compile(r"\bonly available to\b|\bstudents only\b")),
    ("refused_year_of_study", re.compile(r"\byear of study\b")),
    ("refused_mark_threshold", re.compile(r"\d\s*%")),
    ("refused_or_equivalent", re.compile(r"\bor equivalent\b")),
)
# A code with its term letter, and any other term it runs in (EEE2046F/S)
CODE = re.compile(r"[A-Z]{3}\d{4}[A-Z](?:/[A-Z])*")
# A code printed without a term letter (MAM1020), which doesn't say which course it means
BARE_CODE = re.compile(r"[A-Z]{3}\d{4}")
# A comma beside "and" or "or" belongs to it, as in EEE2044S's "and, (", so each join is one token
TOKEN = re.compile(rf"{CODE.pattern}\b|,?\s*\b(?P<join>and|or)\b\s*,?|\w+|\S")
JOINS = ("and", "or", ",")


class Refused(Exception):
    # Wording the grammar won't read, and why, which flags the model's draft for review
    def __init__(self, cause: RefusalCause) -> None:
        super().__init__(cause)
        self.cause = cause


def read(text: str, need: Literal["pass", "concurrent"] = "pass") -> EntryRule | None:
    # The tree a printed requirement means, or None where it prints "None". A co-requisite's leaves
    # need the course taken alongside, the rest a pass.
    wording = " ".join(text.split()).removesuffix(".")
    if wording == "None":
        return None
    tokens = [match["join"] or match[0] for match in TOKEN.finditer(wording)]
    try:
        tree, at = _expression(tokens, 0, need)
        if at < len(tokens):
            raise Refused("refused_other")
    except Refused as refused:
        raise Refused(_cause(wording, tokens, refused.cause)) from None
    return tree


def _expression(
    tokens: list[str], at: int, need: Literal["pass", "concurrent"]
) -> tuple[EntryRule, int]:
    # Terms joined one way only: by "or", or by "and" and commas
    terms, joins = [], set()
    term, at = _term(tokens, at, need)
    terms.append(term)
    while at < len(tokens) and tokens[at] in JOINS:
        joins.add("or" if tokens[at] == "or" else "and")
        term, at = _term(tokens, at + 1, need)
        terms.append(term)
    if len(joins) > 1:
        raise Refused("refused_mixed_and_or")
    if len(terms) == 1:
        return term, at
    # A child joined the same way as its parent is spliced into it, so A or (B or C) is one any
    node, field = (AnyOf, "any") if joins == {"or"} else (AllOf, "all")
    children: list[EntryRule] = []
    for term in terms:
        children.extend(getattr(term, field) if isinstance(term, node) else (term,))
    return node(**{field: tuple(children)}), at


def _term(
    tokens: list[str], at: int, need: Literal["pass", "concurrent"]
) -> tuple[EntryRule, int]:
    # One code, or an expression in brackets
    token = tokens[at] if at < len(tokens) else ""
    if CODE.fullmatch(token):
        code, *terms = token.split("/")
        leaves = [CourseNeed(course=code, need=need)]
        leaves += [CourseNeed(course=code[:-1] + term, need=need) for term in terms]
        return (leaves[0] if len(leaves) == 1 else AnyOf(any=tuple(leaves))), at + 1
    if token == "(":
        tree, at = _expression(tokens, at + 1, need)
        if at < len(tokens) and tokens[at] == ")":
            return tree, at + 1
    raise Refused("refused_other")


def _cause(wording: str, tokens: list[str], structure: RefusalCause) -> RefusalCause:
    # The first cause the wording shows, whatever stopped the parser, so the same wording is always
    # refused for the same reason
    for cause, pattern in JUDGED:
        if pattern.search(wording):
            return cause
    unread = {
        t for t in tokens if not CODE.fullmatch(t) and t not in (*JOINS, "(", ")")
    }
    if any(BARE_CODE.fullmatch(token) for token in unread):
        return "refused_code_without_term"
    if unread - {";", "."}:
        return "refused_free_text"
    if unread:
        return "refused_punctuation"
    return structure
