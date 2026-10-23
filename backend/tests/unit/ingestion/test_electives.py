# Checks the rules every elective's tab and summary must meet, whoever wrote them: a tab from the
# closed list, the languages tab for the language options alone, and a summary of one or two plain
# sentences and at most 40 words, tested on both sides of each limit.
import pytest

from sage.ingestion.electives import fault

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
