# Checks the rules every elective's tab and summary must meet, whoever wrote them: a tab from the
# closed list, the languages tab for the language options alone, and a summary of one or two plain
# sentences and at most 40 words, tested on both sides of each limit. Then that the job asks the
# model from each passage alone, keeps a draft only while its passage is unchanged, reuses an
# earlier year's but not its copy of another offering's, refuses a draft that breaks a rule or isn't
# an object, saves each as it's made and writes nothing without a model, and that a course offered
# twice with one passage has one draft, which leaves the courses after it alone. A scripted model
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
    paired,
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


# Why each summary is refused, as the walk and the run report say it, so a summary that breaks one
# rule is refused for that rule, not another
SENTENCES = "the summary must be one or two sentences"
MARKUP = "the summary must be plain text, with no markup or line breaks"
MISSING = "the summary is missing"


@pytest.mark.parametrize(
    ("summary", "reason"),
    [
        # 40 words in one sentence: 39 "Studies" and "history."
        (" ".join(["Studies"] * 39) + " history.", None),
        # 41 words
        (
            " ".join(["Studies"] * 40) + " history.",
            "the summary has 41 words, more than 40",
        ),
        ("One sentence about it.", None),
        ("Three short sentences. About one course. Too many.", SENTENCES),
        ("A sentence with no end", SENTENCES),
        ("A **bold** claim about the course.", MARKUP),
        ("A line about it.\nAnother line about it.", MARKUP),
        ("   ", MISSING),
        (None, MISSING),
    ],
)
def test_a_summary_is_one_or_two_plain_sentences_of_at_most_40_words(summary, reason):
    assert fault({"tab": "history", "summary": summary}, False) == reason


def test_a_value_without_both_parts_is_refused():
    assert (
        fault({"summary": SUMMARY}, True) == 'it must be {"tab": ..., "summary": ...}'
    )


# What the model reads for a made-up course and a made-up language option, by code
HISTORY = (
    "HST1013F Made Up History\nCourse outline: How made-up societies kept records."
)
SWAHILI = "SLL1017F Made Up Swahili\nCourse outline: Speaking and writing Swahili."
PASSAGES = {"HST1013F": HISTORY, "SLL1017F": SWAHILI}
# The same history course in the second semester, printing the same words
SECOND = HISTORY.replace("HST1013F", "HST1013S")
CREDITS = {"HST1013F": 18, "HST1013S": 18, "SLL1017F": 18}


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
    written = write(PASSAGES, {"SLL1017F"}, CREDITS, tmp_path / "electives.json", model)
    assert (written.electives, written.calls) == (
        {
            "HST1013F": Elective(tab="history", summary=SUMMARY),
            "SLL1017F": Elective(tab=None, summary=SUMMARY),
        },
        2,
    )
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
    written = write(PASSAGES, {"SLL1017F"}, CREDITS, cache, model)
    assert written.refused == (
        (
            "HST1013F: the tab must be one of arts, business, econ, ethics, history, "
            "literature, logic, media, religion, science, society"
        ),
    )
    assert list(written.electives) == ["SLL1017F"]
    assert list(json.loads(cache.read_text(encoding="utf-8"))) == ["SLL1017F"]


def test_a_reply_that_isnt_a_json_object_is_refused_and_the_run_goes_on(tmp_path):
    model = ScriptedModel(
        {
            "elective": [Response(text="Made Up History is on the history tab.")],
            "language_option": [Response(text=json.dumps({"summary": SUMMARY}))],
        }
    )
    written = write(PASSAGES, {"SLL1017F"}, CREDITS, tmp_path / "electives.json", model)
    assert (written.refused, list(written.electives)) == (
        ("HST1013F: the reply isn't a JSON object",),
        ["SLL1017F"],
    )


def test_a_cached_summary_is_not_drawn_again(tmp_path):
    cache = tmp_path / "electives.json"
    cached(cache, "HST1013F", HISTORY, SUMMARY)
    # A model with nothing scripted fails if asked
    model = replies()
    written = write({"HST1013F": HISTORY}, (), CREDITS, cache, model)
    assert (model.calls, written.calls, written.reused) == ([], 0, 0)
    assert written.electives == {"HST1013F": Elective(tab="history", summary=SUMMARY)}


def test_a_changed_passage_is_drafted_again(tmp_path):
    cache = tmp_path / "electives.json"
    cached(cache, "HST1013F", "HST1013F Made Up History\nAn older outline.", SUMMARY)
    # Without a model, the stale draft isn't used
    assert write({"HST1013F": HISTORY}, (), CREDITS, cache, None).electives == {}
    later = "A later summary of the course. It reads well."
    written = write(
        {"HST1013F": HISTORY},
        (),
        CREDITS,
        cache,
        replies({"tab": "society", "summary": later}),
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
    cached(earlier, "SLL1017F", SWAHILI, SUMMARY, tab=None)
    cache = tmp_path / "2026" / "electives.json"
    model = replies()
    written = write(PASSAGES, {"SLL1017F"}, CREDITS, cache, model, [earlier])
    assert (model.calls, written.calls, written.reused) == ([], 0, 2)
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
        write(PASSAGES, (), CREDITS, cache, model)
    assert list(json.loads(cache.read_text(encoding="utf-8"))) == ["HST1013F"]


@pytest.mark.parametrize(
    ("code", "credits", "passage", "first"),
    [
        ("HST1013S", 18, SECOND, "HST1013F"),
        # The same seven characters at other credits, so another course
        ("HST1013S", 36, SECOND, None),
        # Another course, one digit on
        ("HST1014S", 18, HISTORY.replace("HST1013F", "HST1014S"), None),
        # The same course, printing other class times
        ("HST1013S", 18, f"{SECOND}\nClass times: Mondays, 5th period.", None),
    ],
)
def test_offerings_of_one_course_with_one_passage_are_paired(
    code, credits, passage, first
):
    same = paired({"HST1013F": HISTORY, code: passage}, {"HST1013F": 18, code: credits})
    assert same == ({code: first} if first else {})


def test_the_second_offering_takes_the_first_offerings_draft(tmp_path):
    # HST1013S was drafted on its own, as every offering was before pairing
    cache = tmp_path / "electives.json"
    cached(cache, "HST1013F", HISTORY, SUMMARY)
    cached(cache, "HST1013S", SECOND, "Another summary of it.", tab="logic")
    passages = {"HST1013F": HISTORY, "HST1013S": SECOND}
    # Even with no model, it shows the first offering's draft, and writes nothing
    before = cache.read_text(encoding="utf-8")
    shown = write(passages, (), CREDITS, cache, None).electives
    assert shown["HST1013S"] == Elective(tab="history", summary=SUMMARY)
    assert cache.read_text(encoding="utf-8") == before
    # A run that drafts asks the model nothing, and records the copy
    model = replies()
    write(passages, (), CREDITS, cache, model)
    assert model.calls == []
    assert json.loads(cache.read_text(encoding="utf-8"))["HST1013S"] == {
        "model": "an earlier model",
        "tab": "history",
        "summary": SUMMARY,
        "sha256": hashlib.sha256(SECOND.encode()).hexdigest(),
        "same_as": "HST1013F",
    }


@pytest.mark.parametrize("drafted", [True, False])
def test_a_course_after_a_pair_keeps_its_draft(tmp_path, drafted):
    # HST1013F and HST1013S are one course, whose second offering shows the first's draft if it has
    # one, and SLL1017F comes after them by code
    cache = tmp_path / "electives.json"
    cached(cache, "SLL1017F", SWAHILI, SUMMARY, tab=None)
    if drafted:
        cached(cache, "HST1013F", HISTORY, SUMMARY)
    passages = PASSAGES | {"HST1013S": SECOND}
    written = write(passages, {"SLL1017F"}, CREDITS, cache, None)
    pair = ["HST1013F", "HST1013S"] if drafted else []
    assert sorted(written.electives) == [*pair, "SLL1017F"]


def test_an_earlier_years_copy_is_drafted_afresh(tmp_path):
    # In 2025 HST1013S copied HST1013F's draft. In 2026 HST1013F prints a new outline, so the two
    # are no longer one course, and HST1013S's copy of a draft of other words isn't reused.
    earlier = tmp_path / "2025" / "electives.json"
    cached(earlier, "HST1013F", HISTORY, SUMMARY)
    cached(earlier, "HST1013S", SECOND, SUMMARY)
    copies = json.loads(earlier.read_text(encoding="utf-8"))
    copies["HST1013S"]["same_as"] = "HST1013F"
    earlier.write_text(json.dumps(copies), encoding="utf-8")
    passages = {
        "HST1013F": f"{HISTORY} A new outline.",
        "HST1013S": SECOND,
    }
    reply = {"tab": "history", "summary": SUMMARY}
    model = replies(reply, reply)
    written = write(
        passages, (), CREDITS, tmp_path / "2026" / "electives.json", model, [earlier]
    )
    assert (written.calls, written.reused) == (2, 0)


def test_the_prompt_defines_every_tab_the_model_may_pick():
    assert [tab for tab in TABS if f"\n- {tab}: " not in PROMPT] == ["languages"]
