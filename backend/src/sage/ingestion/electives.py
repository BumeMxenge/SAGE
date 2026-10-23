# What a complementary course's tab and summary must be, whoever writes them: SAGE's language model
# drafting from the course's passage, or a person correcting the draft in the review.
import re
from typing import get_args

from pydantic import JsonValue

from sage.shared.rules import ElectiveTab

TABS: tuple[str, ...] = get_args(ElectiveTab)
# The language options' tab, fixed when the workbook is read, and theirs alone
LANGUAGES = "languages"
MAX_WORDS = 40
# A full stop, question mark or exclamation mark that ends a sentence
SENTENCE_END = re.compile(r"[.!?](?=\s|$)")
# Markdown, HTML or a line break, none of which a card shows as written
MARKUP = re.compile(r"[*_#`<>\[\]|\n]|^\s*- ")


def fault(value: JsonValue, language: bool) -> str | None:
    # Why a tab and summary can't stand, or None where they can. A language option's tab is
    # languages, and any other course's is one of the other tabs. A summary is plain text of one or
    # two sentences and at most 40 words, as the card has room for.
    if not isinstance(value, dict) or set(value) != {"tab", "summary"}:
        return 'it must be {"tab": ..., "summary": ...}'
    tab, summary = value["tab"], value["summary"]
    if language and tab != LANGUAGES:
        return f"a language option's tab is {LANGUAGES}"
    if not language and (tab not in TABS or tab == LANGUAGES):
        others = ", ".join(t for t in TABS if t != LANGUAGES)
        return f"the tab must be one of {others}"
    if not isinstance(summary, str) or not summary.strip():
        return "the summary is missing"
    if MARKUP.search(summary):
        return "the summary must be plain text, with no markup or line breaks"
    if (words := len(summary.split())) > MAX_WORDS:
        return f"the summary has {words} words, more than {MAX_WORDS}"
    ends = len(SENTENCE_END.findall(summary.strip()))
    if ends not in (1, 2) or summary.strip()[-1] not in ".!?":
        return "the summary must be one or two sentences"
    return None
