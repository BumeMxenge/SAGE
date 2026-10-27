# ATP-4's checks on made-up runs: each check passes on a run that stays in step and fails on one that
# breaks only its own rule, so a check that never fails can't hide behind the others. The expected
# results come from the brief's four rules, read by hand for each run.
import copy

import pytest
from check import CHECKERS, address_scope
from serve import delay

QUESTION = "[S1-01-1] [d=1.5] Is this plan clash-free?"
REPLY = "S1-01-1 answered for Alpha"


def consistent() -> dict:
    # S1 as built: asked on Alpha, switched to Beta before the reply, then back, then reloaded
    return {
        "scenario": "S1",
        "run": 1,
        "plans": {"a": "Alpha", "b": "Beta", "h": "Hidden"},
        "asked": [{"question": "S1-01-1", "plan_id": "a", "other_plan_id": None}],
        "offered": None,
        "views": [
            {"address": "/plan/b", "header": "Reading Beta", "messages": []},
            {
                "address": "/plan/a?term=sem2",
                "header": "Reading Alpha",
                "messages": [f"You asked: {QUESTION}", f"SAGE replied: {REPLY}"],
            },
        ],
        "chats": [
            {
                "plan_id": "a",
                "other_plan_id": None,
                "messages": [
                    {"role": "user", "content": QUESTION},
                    {"role": "assistant", "content": REPLY},
                ],
            },
            {"plan_id": "b", "other_plan_id": None, "messages": []},
        ],
        "plans_before": [{"id": "a", "hidden": False}, {"id": "h", "hidden": True}],
        "plans_after": [{"id": "a", "hidden": False}, {"id": "h", "hidden": True}],
    }


def test_a_run_in_step_passes_every_check():
    run = consistent()
    assert {name: check(run) for name, check in CHECKERS.items()} == dict.fromkeys(
        CHECKERS, True
    )


def test_a_reply_naming_another_plan_is_in_the_wrong_chat():
    run = consistent()
    run["chats"][0]["messages"][1]["content"] = "S1-01-1 answered for Beta"
    assert not CHECKERS["in_right_chat"](run)


def test_a_late_reply_shown_in_the_open_chat_fails_where_it_shows():
    # The planted fault: Beta's screen shows Alpha's exchange, and Alpha's doesn't
    run = consistent()
    run["views"][0]["messages"] = run["views"][1]["messages"]
    run["views"][1]["messages"] = []
    assert not CHECKERS["in_right_chat"](run)
    assert not CHECKERS["exchanges_once"](run)


def test_an_exchange_stored_twice_is_not_once():
    run = consistent()
    run["chats"][0]["messages"] *= 2
    assert not CHECKERS["exchanges_once"](run)


def test_a_question_stored_in_no_chat_is_not_once():
    run = consistent()
    run["chats"][0]["messages"] = []
    run["views"][1]["messages"] = []
    assert not CHECKERS["exchanges_once"](run)


def test_a_rail_naming_another_plan_does_not_match_the_address():
    run = consistent()
    run["views"][1]["header"] = "Reading Beta"
    assert not CHECKERS["address_matches_chat"](run)


def test_a_pair_is_named_in_either_order():
    run = consistent()
    run["asked"][0]["other_plan_id"] = "b"
    pair = "S1-01-1 answered for Beta | Alpha"
    run["chats"] = [
        {
            "plan_id": "b",
            "other_plan_id": "a",
            "messages": [
                {"role": "user", "content": QUESTION},
                {"role": "assistant", "content": pair},
            ],
        }
    ]
    run["views"] = [
        {
            "address": "/plan/a?compare=b",
            "header": "Comparing Beta and Alpha",
            "messages": [f"You asked: {QUESTION}", f"SAGE replied: {pair}"],
        }
    ]
    assert all(check(run) for check in CHECKERS.values())


def test_an_offered_plan_may_join_the_shown_list_and_nothing_else_may_change():
    run = consistent()
    run["plans_after"][1]["hidden"] = False
    assert not CHECKERS["plan_set_unchanged"](run)
    offered = copy.deepcopy(run)
    offered["offered"] = "h"
    assert CHECKERS["plan_set_unchanged"](offered)


@pytest.mark.parametrize(
    ("address", "plans"),
    [
        ("/plan/a", {"a"}),
        ("/plan/a?term=sem2", {"a"}),
        ("/plan/a?compare=b&term=sem2", {"a", "b"}),
    ],
)
def test_an_address_names_its_plan_or_pair(address, plans):
    assert address_scope(address) == plans


def test_the_fake_advisor_reads_the_delay_a_question_names():
    assert delay(QUESTION) == 1.5
    assert delay("[S1-01-1] no delay") == 0.0
