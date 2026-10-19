# Turns printed requirements into rule trees, grammar first. The grammar reads wording with exactly one
# reading. A string it refuses takes its draft from the year's drafts.json, or, when a drafter is
# given, a model drafts it and the draft is cached there. Then wording an earlier year drafted takes
# that draft instead, so the same words never get two drafts. A draft is kept only if it's a rule
# tree, or null where the model reads no requirement, as E2's prompt asks, and it stays flagged with
# the grammar's cause for a person to check. A refused string with no draft yet stands as a refer
# leaf holding its printed words, flagged the same way.
import json
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Literal

from pydantic import TypeAdapter, ValidationError

from sage.ingestion import grammar
from sage.ingestion.drafting import Drafter
from sage.shared.base import Row
from sage.shared.rules import EntryRule, Refer, RefusalCause

Need = Literal["pass", "concurrent"]
DRAFT = TypeAdapter(EntryRule | None)


class Translation(Row):
    printed: str  # with its spacing evened out, as the grammar reads it
    need: Need
    tree: EntryRule | None  # None where the print, or a draft of it, asks for nothing
    cause: RefusalCause | None  # why the grammar refused it; None when it read it
    drafted: bool  # whether the tree is a model's draft, rather than the grammar's or a stand-in


class Translations(Row):
    translations: tuple[Translation, ...]
    calls: int  # drafts asked of the model in this run
    reused: int  # drafts copied from an earlier year in this run, instead of asking the model
    refused: tuple[str, ...]  # drafts that weren't a rule tree or null, so weren't kept


def translate(
    strings: Iterable[tuple[str, Need]],
    cache: Path,
    drafter: Drafter | None,
    earlier: Sequence[Path] = (),
) -> Translations:
    drafts = _read(cache)
    # Earlier years' caches come in year order, so wording printed before takes the latest year's
    # draft. The review compares a year with the one before it, and would read a different draft of
    # the same words as a change.
    before = {
        (need, printed): draft
        for path in earlier
        for need, by_printed in _read(path).items()
        for printed, draft in by_printed.items()
    }
    translations, refused, calls, reused = [], [], 0, 0
    for printed, need in sorted(
        {(" ".join(text.split()), need) for text, need in strings}
    ):
        try:
            tree = grammar.read(printed, need)
            translations.append(
                Translation(
                    printed=printed, need=need, tree=tree, cause=None, drafted=False
                )
            )
            continue
        except grammar.Refused as refusal:
            cause = refusal.cause
        cached = drafts.get(need, {}).get(printed)
        if cached is None and drafter is not None:
            if (need, printed) in before:
                reused += 1
                cached = before[need, printed]
            else:
                calls += 1
                draft = drafter.draft(printed, need)
                try:
                    DRAFT.validate_python(draft)
                except ValidationError:
                    refused.append(printed)
                else:
                    cached = {"model": drafter.model, "tree": draft}
            if cached is not None:
                drafts.setdefault(need, {})[printed] = cached
        tree = DRAFT.validate_python(cached["tree"]) if cached else Refer(refer=printed)
        translations.append(
            Translation(
                printed=printed, need=need, tree=tree, cause=cause, drafted=bool(cached)
            )
        )
    if calls or reused:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(
            json.dumps(drafts, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    return Translations(
        translations=tuple(translations),
        calls=calls,
        reused=reused,
        refused=tuple(refused),
    )


def _read(cache: Path) -> dict[str, dict[str, dict]]:
    # A year's drafts by need, then by printed wording
    return json.loads(cache.read_text(encoding="utf-8")) if cache.exists() else {}
