# Checks the grammar reads first and a model drafts only what it refuses: a draft is kept only if it
# fits a rule tree, a cached draft never calls the model, wording an earlier year drafted keeps that
# draft, and with no model a refused string stands as a refer leaf. A fake stands in for the model, so
# no test calls one.
import json

from sage.ingestion.translate import Translation, translate
from sage.shared.rules import AnyOf, CourseNeed, Refer

# CSC2002S's requirement (2026, page 170), which the grammar refuses for its mark, and the tree a
# person would write from the page: a final mark of at least 45 in CSC2001F, pass or not
REFUSED = "CSC2001F (At least 45% for CSC2001F)"
MARK = {"course": "CSC2001F", "need": "mark", "min_mark": 45}


class Fake:
    model = "a made-up model"

    def __init__(self, draft):
        self.draft_given, self.calls = draft, []

    def draft(self, printed, need):
        self.calls.append((printed, need))
        return self.draft_given


def earlier_draft(tmp_path):
    # An earlier year's cache, as `sage ingest --draft` writes it, holding the mark leaf for REFUSED
    path = tmp_path / "2023.json"
    drafts = {"pass": {REFUSED: {"model": "a made-up model", "tree": MARK}}}
    path.write_text(json.dumps(drafts), encoding="utf-8")
    return path


def test_a_refused_string_is_drafted_once_and_cached(tmp_path):
    # In a year's folder that doesn't exist yet, as on the first run that drafts
    cache = tmp_path / "rules" / "2026" / "drafts.json"
    fake = Fake(MARK)
    # EEE4117F's requirement (2026, page 139) and a co-requisite, which the grammar reads, never
    # reach the model. The co-requisite's courses are needed alongside, as E2's prompt reads it.
    strings = [("EEE3091F", "pass"), ("MAM2084F/S.", "concurrent"), (REFUSED, "pass")]
    first = translate(strings, cache, fake)
    assert first.translations == (
        Translation(
            printed=REFUSED,
            need="pass",
            tree=CourseNeed(course="CSC2001F", need="mark", min_mark=45),
            cause="refused_mark_threshold",
            drafted=True,
        ),
        Translation(
            printed="EEE3091F",
            need="pass",
            tree=CourseNeed(course="EEE3091F", need="pass"),
            cause=None,
            drafted=False,
        ),
        Translation(
            printed="MAM2084F/S.",
            need="concurrent",
            tree=AnyOf(
                any=(
                    CourseNeed(course="MAM2084F", need="concurrent"),
                    CourseNeed(course="MAM2084S", need="concurrent"),
                )
            ),
            cause=None,
            drafted=False,
        ),
    )
    assert (fake.calls, first.calls) == ([(REFUSED, "pass")], 1)
    assert json.loads(cache.read_text(encoding="utf-8")) == {
        "pass": {REFUSED: {"model": "a made-up model", "tree": MARK}}
    }
    # A second run takes the draft from the cache and asks the model nothing
    again = Fake(MARK)
    assert translate(strings, cache, again) == first.model_copy(update={"calls": 0})
    assert again.calls == []


def test_a_draft_that_does_not_fit_a_rule_tree_is_refused(tmp_path):
    cache = tmp_path / "drafts.json"
    # A mark leaf without its mark
    read = translate(
        [(REFUSED, "pass")], cache, Fake({"course": "CSC2001F", "need": "mark"})
    )
    assert read.refused == (REFUSED,)
    assert read.translations[0].tree == Refer(refer=REFUSED)
    assert not read.translations[0].drafted
    assert json.loads(cache.read_text(encoding="utf-8")) == {}


def test_wording_an_earlier_year_drafted_keeps_that_draft_without_asking(tmp_path):
    cache = tmp_path / "drafts.json"
    # A model that would draft it differently
    fake = Fake({"refer": REFUSED})
    read = translate([(REFUSED, "pass")], cache, fake, [earlier_draft(tmp_path)])
    assert fake.calls == []
    assert (read.calls, read.reused) == (0, 1)
    assert read.translations[0].tree == CourseNeed(
        course="CSC2001F", need="mark", min_mark=45
    )
    assert read.translations[0].drafted
    # The year's own cache holds it too, so its drafts stand on their own
    assert json.loads(cache.read_text(encoding="utf-8")) == {
        "pass": {REFUSED: {"model": "a made-up model", "tree": MARK}}
    }


def test_a_draft_of_no_requirement_is_kept_as_no_rule(tmp_path):
    # Wording that only describes a course, which E2's prompt answers with a null rule
    cache = tmp_path / "drafts.json"
    printed = "None. This is a course designed for beginners."
    read = translate([(printed, "pass")], cache, Fake(None))
    assert read.translations == (
        Translation(
            printed=printed,
            need="pass",
            tree=None,
            cause="refused_free_text",
            drafted=True,
        ),
    )
    # Cached, so a second run asks the model nothing
    again = Fake(MARK)
    assert translate([(printed, "pass")], cache, again) == read.model_copy(
        update={"calls": 0}
    )
    assert again.calls == []


def test_without_a_model_a_refused_string_stands_as_a_refer_leaf(tmp_path):
    cache = tmp_path / "drafts.json"
    # Even where an earlier year drafted it, as only a run that drafts copies a draft
    read = translate([(REFUSED, "pass")], cache, None, [earlier_draft(tmp_path)])
    assert read.translations == (
        Translation(
            printed=REFUSED,
            need="pass",
            tree=Refer(refer=REFUSED),
            cause="refused_mark_threshold",
            drafted=False,
        ),
    )
    assert (read.calls, read.reused, cache.exists()) == (0, 0, False)
