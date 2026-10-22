# Checks the citation check and the referral it can force, on Mbali's slice of the approved 2026: a
# quote counts only word for word in the passage it cites, and a reply that cited the handbook but
# kept no quote becomes the fixed referral, while one that cites nothing stands as written. A chat's
# title is checked at each edge.
import json

import pytest

from sage.advisor.checks import (
    REFERRAL,
    Answer,
    Quote,
    check,
    checked_title,
    quotes_kept,
)
from sage.shared.advisor import Reply


@pytest.fixture
def found(evidence):
    return evidence()


def short_id(found, section: str) -> str:
    return next(
        key for key, passage in found.passages.items() if passage.section == section
    )


def test_a_quote_counts_only_word_for_word_in_the_passage_it_cites(found):
    # EEE4022S's entry prints "is not eligible for additional" with "assessment" on the next line
    # (2026, page 138), and HUB4049F's entry doesn't print those words at all
    entry = short_id(found, "EEE4022S Research Project")
    other = short_id(
        found, "HUB4049F Introduction to Medical Imaging & Image Processing"
    )
    kept = [
        Quote(passage_id=entry, quote="not eligible for additional assessment"),
        Quote(passage_id=entry, quote="not  eligible for\nadditional   assessment"),
    ]
    dropped = [
        # One word changed, the right words in a passage that doesn't print them, a passage outside
        # her slice, and an empty quote, which every passage would otherwise hold
        Quote(passage_id=entry, quote="not eligible for further assessment"),
        Quote(passage_id=other, quote="not eligible for additional assessment"),
        Quote(passage_id="P99", quote="not eligible for additional assessment"),
        Quote(passage_id=entry, quote=" "),
    ]
    assert quotes_kept([*kept, *dropped], found.passages) == (kept, dropped)


def test_a_reply_that_kept_no_quote_is_the_fixed_referral_and_one_with_none_stands(
    found,
):
    entry = short_id(found, "EEE4022S Research Project")
    page = found.passages[entry]
    good = Quote(passage_id=entry, quote="not eligible for additional assessment")
    bad = Quote(passage_id=entry, quote="eligible for a supplementary examination")
    stated = {"content": "Made up.", "referral": False, "open_plan_id": "V01"}
    # Every quote dropped: the fixed line, a referral, and no plan offered, though V01 is open
    unchecked = check(Answer(**stated, citations=(bad,)), found, {"V01"}, "")
    assert unchecked.reply == Reply(content=REFERRAL, referral=True)
    # One of two kept: the reply stands, citing only the one kept, as its first
    one_kept = check(Answer(**stated, citations=(bad, good)), found, {"V01"}, "")
    assert (one_kept.reply.content, one_kept.reply.referral) == ("Made up.", False)
    assert [
        (cited.passage_id, cited.position, cited.quote, cited.page)
        for cited in one_kept.reply.citations
    ] == [(page.id, 1, good.quote, 138)]
    # No citations at all: facts about her plans, as written
    plain = check(Answer(**stated, citations=()), found, {"V01"}, "")
    assert plain.reply == Reply(
        content="Made up.", referral=False, open_plan_id=found.plans["V01"].id
    )


@pytest.mark.parametrize(
    ("title", "kept"),
    [
        ("Two Words", True),
        ("One", False),
        ("Six Words in This Title Here", True),
        ("Seven Words in This Title Right Here", False),
        ("A" * 18 + " " + "B" * 21, True),  # 40 characters
        ("A" * 18 + " " + "B" * 22, False),  # 41
        ("Fridays on\nPower", False),
        ("Fridays on Power.", False),
    ],
)
def test_a_title_is_2_to_6_words_and_40_characters_on_one_line_with_no_full_stop(
    title, kept
):
    assert checked_title(json.dumps({"title": title})) == (title if kept else None)


def test_a_reply_that_isnt_a_title_is_none():
    # Cut off, and not in the schema
    assert checked_title(None) is None
    assert checked_title('{"name": "Two Words"}') is None
