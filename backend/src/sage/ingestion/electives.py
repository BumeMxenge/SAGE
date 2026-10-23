# Each complementary course's tab and summary, which SAGE's language model writes from the course's
# passage alone, and the rules they must meet, whoever writes them: the model drafting, or a person
# correcting the draft in the review. The year's electives.json caches each draft with its model and
# the SHA-256 of the passage it read. A draft of an unchanged passage is kept, one an earlier year
# made of the same passage is reused, and only a run that drafts asks the model for the rest. A draft
# that breaks a rule is reported and not kept, and the run goes on.
import hashlib
import json
import re
from collections.abc import Collection, Mapping, Sequence
from pathlib import Path
from typing import get_args

from pydantic import JsonValue

from sage.shared.base import Row
from sage.shared.language_model import LanguageModel, Said, Schema, strict_object
from sage.shared.rules import ElectiveTab

# The prompt after its opening note for people, split as the drafting prompt is
PROMPT = (
    Path(__file__)
    .with_name("electives_prompt.md")
    .read_text(encoding="utf-8")
    .split("\n---\n", 1)[1]
    .strip()
)
TABS: tuple[str, ...] = get_args(ElectiveTab)
# The language options' tab, fixed when the workbook is read, and theirs alone
LANGUAGES = "languages"
MAX_WORDS = 40
# A full stop, question mark or exclamation mark that ends a sentence
SENTENCE_END = re.compile(r"[.!?](?=\s|$)")
# Markdown, HTML or a line break, none of which a card shows as written
MARKUP = re.compile(r"[*_#`<>\[\]|\n]|^\s*- ")
# A course's reply, its tab one of the others, and a language option's, its summary alone
COURSE = Schema(
    name="elective",
    shape=strict_object(
        tab={"enum": [tab for tab in TABS if tab != LANGUAGES]},
        summary={"type": "string"},
    ),
)
LANGUAGE_OPTION = Schema(
    name="language_option", shape=strict_object(summary={"type": "string"})
)


class Elective(Row):
    tab: ElectiveTab | None  # None for a language option, whose tab is fixed
    summary: str


class Written(Row):
    electives: dict[str, Elective]  # by code, for each course with a usable draft
    calls: int  # drafts asked of the model in this run
    reused: int  # drafts copied from an earlier year in this run, instead of asking the model
    refused: tuple[str, ...]  # each draft not kept, and why


def write(
    passages: Mapping[str, str],
    languages: Collection[str],
    cache: Path,
    model: LanguageModel | None,
    earlier: Sequence[Path] = (),
) -> Written:
    # passages are what the model reads for each course, by code, and languages the codes of the
    # language options
    drafts = _read(cache)
    before = {
        entry["sha256"]: entry for path in earlier for entry in _read(path).values()
    }
    electives, refused, calls, reused = {}, [], 0, 0
    for code, passage in sorted(passages.items()):
        digest = hashlib.sha256(passage.encode()).hexdigest()
        entry = drafts.get(code)
        if model is not None and (entry is None or entry["sha256"] != digest):
            if digest in before:
                reused += 1
                entry = before[digest]
            else:
                calls += 1
                entry = _draft(model, passage, code in languages)
                if isinstance(entry, str):
                    refused.append(f"{code}: {entry}")
                    continue
                entry["sha256"] = digest
            drafts[code] = entry
            # Saved after each draft, so a run that stops keeps what it paid for
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(
                json.dumps(drafts, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        if entry is not None and entry["sha256"] == digest:
            electives[code] = Elective(tab=entry["tab"], summary=entry["summary"])
    return Written(
        electives=electives, calls=calls, reused=reused, refused=tuple(refused)
    )


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


def _draft(
    model: LanguageModel, passage: str, language: bool
) -> dict[str, JsonValue] | str:
    # The model's tab and summary for one passage as a cache entry, or why it can't stand
    reply = model.respond(
        PROMPT,
        [Said(role="user", text=passage)],
        schema=LANGUAGE_OPTION if language else COURSE,
    )
    try:
        answer = json.loads(reply.text or "")
    except json.JSONDecodeError:
        answer = None
    if not isinstance(answer, dict):
        return "the reply isn't a JSON object"
    value = {
        "tab": LANGUAGES if language else answer.get("tab"),
        "summary": answer.get("summary"),
    }
    if problem := fault(value, language):
        return problem
    return {
        "model": model.model,
        "tab": None if language else value["tab"],
        "summary": value["summary"],
    }


def _read(cache: Path) -> dict[str, dict]:
    # A year's drafts by course code
    return json.loads(cache.read_text(encoding="utf-8")) if cache.exists() else {}
