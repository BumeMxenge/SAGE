# Checks the rules every elective's tab and summary must meet, whoever wrote them: a tab from the
# closed list, the languages tab for the language options alone, and a summary of one or two plain
# sentences and at most 40 words, tested on both sides of each limit. Then that the job asks the
# model from each passage alone, keeps a draft only while its passage is unchanged, reuses an
# earlier year's, refuses a draft that breaks a rule and saves each as it's made. A scripted model
# answers, so no test calls a real one.
import hashlib
import json

import pytest

from sage.ingestion.electives import (
    COURSE,
    LANGUAGE_OPTION,
    PROMPT,
    TABS,
    Elective,
    fault,
    write,
)
from sage.shared.language_model import ModelUnavailable, Response, Said
from sage.shared.memory.language_model import ScriptedModel

# Two sentences, 20 words, about a made-up course
SUMMARY = (
    "An introduction to how ancient societies kept records. "
    "Students learn to read sources closely and argue from evidence."
)


@pytest.mark.parametrize(
    ("tab", "language", "refused"),
    [
        ("history", False, False),
        ("engineering", False, True),  # not one of the tabs
        (None, False, True),
        ("languages", False, True),  # the language options' tab
        ("languages", True, False),
        ("literature", True, True),  # a language option stays on languages
    ],
)
def test_a_tab_outside_the_list_is_refused(tab, language, refused):
    assert (fault({"tab": tab, "summary": SUMMARY}, language) is not None) == refused


@pytest.mark.parametrize(
    ("summary", "refused"),
    [
        # 40 words in one sentence: 39 "Studies" and "history."
        (" ".join(["Studies"] * 39) + " history.", False),
        # 41 words
        (" ".join(["Studies"] * 40) + " history.", True),
        ("One sentence about it.", False),
        ("Three short sentences. About one course. Too many.", True),
        ("A sentence with no end", True),
        ("A **bold** claim about the course.", True),
        ("A line about it.\nAnother line about it.", True),
        ("   ", True),
        (None, True),
    ],
)
def test_a_summary_is_one_or_two_plain_sentences_of_at_most_40_words(summary, refused):
    assert (fault({"tab": "history", "summary": summary}, False) is not None) == refused


def test_a_value_without_both_parts_is_refused():
    assert fault({"summary": SUMMARY}, True) is not None


# What the model reads for a made-up course and a made-up language option, by code
HISTORY = (
    "HST1013F Made Up History\nCourse outline: How made-up societies kept records."
)
SWAHILI = "SLL1017F Made Up Swahili\nCourse outline: Speaking and writing Swahili."
PASSAGES = {"HST1013F": HISTORY, "SLL1017F": SWAHILI}


def replies(*courses, languages=()):
    # A scripted model's replies to a course, held to its tab and summary, and a language option
    return ScriptedModel(
        {
            "elective": [Response(text=json.dumps(reply)) for reply in courses],
            "language_option": [
                Response(text=json.dumps({"summary": summary})) for summary in languages
            ],
        }
    )


def cached(cache, code, passage, summary, tab="history"):
    # An entry as a run that drafts writes it, for the passage given
    entry = {
        "model": "an earlier model",
        "tab": tab,
        "summary": summary,
        "sha256": hashlib.sha256(passage.encode()).hexdigest(),
    }
    drafts = json.loads(cache.read_text(encoding="utf-8")) if cache.exists() else {}
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(drafts | {code: entry}), encoding="utf-8")


def test_each_course_is_asked_for_from_its_passage_alone(tmp_path):
    model = replies({"tab": "history", "summary": SUMMARY}, languages=[SUMMARY])
    written = write(PASSAGES, {"SLL1017F"}, tmp_path / "electives.json", model)
    assert written.electives == {
        "HST1013F": Elective(tab="history", summary=SUMMARY),
        "SLL1017F": Elective(tab=None, summary=SUMMARY),
    }
    # The prompt and the passage, and a language option asked for its summary alone
    assert [
        (call.instructions, call.conversation, call.schema) for call in model.calls
    ] == [
        (PROMPT, (Said(role="user", text=HISTORY),), COURSE),
        (PROMPT, (Said(role="user", text=SWAHILI),), LANGUAGE_OPTION),
    ]


def test_a_tab_outside_the_list_is_refused_and_the_run_goes_on(tmp_path):
    cache = tmp_path / "electives.json"
    model = replies({"tab": "engineering", "summary": SUMMARY}, languages=[SUMMARY])
    written = write(PASSAGES, {"SLL1017F"}, cache, model)
    assert written.refused == (
        (
            "HST1013F: the tab must be one of arts, business, econ, ethics, history, "
            "literature, logic, media, religion, science, society"
        ),
    )
    assert list(written.electives) == ["SLL1017F"]
    assert list(json.loads(cache.read_text(encoding="utf-8"))) == ["SLL1017F"]


def test_a_cached_summary_is_not_drawn_again(tmp_path):
    cache = tmp_path / "electives.json"
    cached(cache, "HST1013F", HISTORY, SUMMARY)
    # A model with nothing scripted fails if asked
    model = replies()
    written = write({"HST1013F": HISTORY}, (), cache, model)
    assert (model.calls, written.calls, written.reused) == ([], 0, 0)
    assert written.electives == {"HST1013F": Elective(tab="history", summary=SUMMARY)}


def test_a_changed_passage_is_drafted_again(tmp_path):
    cache = tmp_path / "electives.json"
    cached(cache, "HST1013F", "HST1013F Made Up History\nAn older outline.", SUMMARY)
    # Without a model, the stale draft isn't used
    assert write({"HST1013F": HISTORY}, (), cache, None).electives == {}
    later = "A later summary of the course. It reads well."
    written = write(
        {"HST1013F": HISTORY}, (), cache, replies({"tab": "society", "summary": later})
    )
    assert (written.calls, written.electives) == (
        1,
        {"HST1013F": Elective(tab="society", summary=later)},
    )
    assert json.loads(cache.read_text(encoding="utf-8"))["HST1013F"] == {
        "model": "a scripted model",
        "tab": "society",
        "summary": later,
        "sha256": hashlib.sha256(HISTORY.encode()).hexdigest(),
    }


def test_an_earlier_years_draft_of_the_same_passage_is_reused(tmp_path):
    earlier = tmp_path / "2025" / "electives.json"
    cached(earlier, "HST1013F", HISTORY, SUMMARY)
    cache = tmp_path / "2026" / "electives.json"
    model = replies()
    written = write({"HST1013F": HISTORY}, (), cache, model, [earlier])
    assert (model.calls, written.calls, written.reused) == ([], 0, 1)
    # The year's own cache holds it too, so its drafts stand on their own
    assert json.loads(cache.read_text(encoding="utf-8")) == json.loads(
        earlier.read_text(encoding="utf-8")
    )


def test_each_draft_is_saved_as_it_is_made(tmp_path):
    # The model drafts the first course, then can't be reached
    cache = tmp_path / "electives.json"
    model = ScriptedModel(
        {
            "elective": [
                Response(text=json.dumps({"tab": "history", "summary": SUMMARY})),
                ModelUnavailable("RateLimitError"),
            ]
        }
    )
    with pytest.raises(ModelUnavailable):
        write(PASSAGES, (), cache, model)
    assert list(json.loads(cache.read_text(encoding="utf-8"))) == ["HST1013F"]


def test_the_prompt_defines_every_tab_the_model_may_pick():
    assert [tab for tab in TABS if f"\n- {tab}: " not in PROMPT] == ["languages"]
