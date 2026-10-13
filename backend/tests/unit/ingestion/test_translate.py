# Checks the grammar reads first and a model drafts only what it refuses: a draft is kept only if it
# fits a rule tree, a cached draft never calls the model, and with no model a refused string stands as
# a refer leaf. A fake stands in for the model, so no test calls one.
import json

from sage.domain.rules import CourseNeed, Refer
from sage.ingestion.translate import Translation, translate

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


def test_a_refused_string_is_drafted_once_and_cached(tmp_path):
    cache = tmp_path / "drafts.json"
    fake = Fake(MARK)
    # EEE4117F's requirement (2026, page 139), which the grammar reads, never reaches the model
    strings = [("EEE3091F", "pass"), (REFUSED, "pass")]
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
    )
    assert fake.calls == [(REFUSED, "pass")]
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


def test_without_a_model_a_refused_string_stands_as_a_refer_leaf(tmp_path):
    cache = tmp_path / "drafts.json"
    read = translate([(REFUSED, "pass")], cache, None)
    assert read.translations == (
        Translation(
            printed=REFUSED,
            need="pass",
            tree=Refer(refer=REFUSED),
            cause="refused_mark_threshold",
            drafted=False,
        ),
    )
    assert (read.calls, cache.exists()) == (0, False)
