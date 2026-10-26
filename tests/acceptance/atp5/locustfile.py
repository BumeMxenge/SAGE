# The simulated student for ATP-5. On start she claims an unused test account, finishes setup if it
# is fresh (timed "first plan set"), answers the questionnaire (timed "narrow"), then loops through
# reading her plan set, one plan ("open"), a pair, Explore Electives ("check", the read that runs
# the eligibility checker) and Course History, with a few seconds between each. A separate paced
# loop asks the advisor a question about every three minutes (timed "reply"), capped at 600 for the
# whole window. Every request is logged to requests.csv through an event hook, so the time series
# can be drawn, and a LoadTestShape runs the ramp, hold and spike stages when it is switched on.
from __future__ import annotations

import json
import os
import random
import threading
import time
from pathlib import Path

import gevent
from locust import HttpUser, LoadTestShape, between, events, task
from locust.exception import StopUser

from common import (
    REPO_ROOT,
    Config,
    Tokens,
    load_manifest,
    save_manifest,
    write_csv,
)

# The record each student onboards with. Ziyela's plans leave a complementary slot, so "check" has
# a slot to read; the dry run confirms the choice and Stop 2 records it.
RECORD = Path(
    os.environ.get("SAGE_LOAD_RECORD", REPO_ROOT / "data/synthetic/ziyela.json")
)
SEED = json.loads(RECORD.read_text(encoding="utf-8"))
CURRICULUM = SEED["students"][0]["curriculum_code"]
LINES = SEED["course_history"]

# Mbali's vetted questions (docs/advisor-validation.md): three about one plan and two about a pair,
# a mix of ordinary replies and a referral, with known-safe answers. Each is tagged with the chat
# it belongs in.
QUESTIONS = [
    ("Roughly how many hours of work does one credit stand for?", "single"),
    (
        "What does AST1000S Introduction to Astronomy need, and am I allowed to take it?",
        "single",
    ),
    ("On this plan, could I do EEE4114F instead of EEE4120F?", "single"),
    ("Which of these two plans has more classes on Fridays?", "pair"),
    ("Does either of them have a class over the meridian on Mondays?", "pair"),
]
QUESTION_CAP = 600
# Seconds between a student's questions, roughly; the dry run shortens it to exercise replies
ASK_EVERY = int(os.environ.get("SAGE_ASK_EVERY", "180"))
TIMEOUT = 30  # seconds before a request counts as a failed, hung operation
REPLY_TIMEOUT = (
    60  # a reply is allowed longer, as the advisor's turn runs up to 50 seconds
)

# The stages, each (name, seconds, target users, spawn rate). The two holds at 35 are where NF-4 is
# judged: the first, and the second after the spike to 70.
STAGES = [
    ("single", 300, 1, 1.0),
    ("ramp_up_35", 120, 35, 0.29),
    ("hold_35a", 600, 35, 35.0),
    ("ramp_up_70", 60, 70, 0.59),
    ("hold_70", 300, 70, 70.0),
    ("ramp_down_35", 60, 35, 0.59),
    ("hold_35b", 600, 35, 35.0),
]

# The output file, so the rescaled run writes beside the stage run rather than over it
REQUESTS_CSV = (
    Path(__file__).resolve().parent
    / "results"
    / os.environ.get("SAGE_LOAD_OUT", "requests.csv")
)
STAGES_CSV = Path(__file__).resolve().parent / "results" / "stages.csv"
TOKEN_MAX_AGE = (
    3000  # refresh a token older than 50 minutes, before its one-hour expiry
)

_claim_lock = threading.Lock()
_question_lock = threading.Lock()
_questions_asked = 0
_rows_lock = threading.Lock()
_rows: list[dict[str, object]] = []
_started_at: list[float] = []


def claim_account() -> dict[str, object] | None:
    # One unused load account per student, marked in the manifest so the rescaled run picks up the
    # 35 still unused and times their first plan set on fresh setups too
    with _claim_lock:
        accounts = load_manifest()
        for account in accounts:
            if account["role"] == "load" and not account["claimed"]:
                account["claimed"] = True
                save_manifest(accounts)
                return account
    return None


def take_question_slot() -> bool:
    global _questions_asked
    with _question_lock:
        if _questions_asked >= QUESTION_CAP:
            return False
        _questions_asked += 1
        return True


@events.request.add_listener
def on_request(**kw: object) -> None:
    # Every request, success or failure, with the class of any failure so the report can give error
    # rates per operation
    exception = kw.get("exception")
    response = kw.get("response")
    status = int(getattr(response, "status_code", 0) or 0)
    if exception is not None:
        error_class = (
            "timeout" if "timeout" in type(exception).__name__.lower() else "error"
        )
    elif status >= 500:
        error_class = "5xx"
    elif status >= 400:
        error_class = "4xx"
    else:
        error_class = ""
    start_time = kw.get("start_time") or time.time()
    with _rows_lock:
        _rows.append(
            {
                "timestamp": round(float(start_time), 3),
                "name": kw.get("name"),
                "status": status,
                "bytes": int(kw.get("response_length") or 0),
                "latency_ms": round(float(kw.get("response_time") or 0), 1),
                "error_class": error_class,
            }
        )


@events.test_start.add_listener
def on_test_start(**kw: object) -> None:
    _started_at.append(time.time())


@events.test_stop.add_listener
def on_test_stop(**kw: object) -> None:
    write_csv(
        REQUESTS_CSV,
        ["timestamp", "name", "status", "bytes", "latency_ms", "error_class"],
        list(_rows),
    )
    # The stage windows in absolute time, so the report can slice requests.csv by stage. Written
    # only for a shaped run, where the stages mean something.
    if _started_at and os.environ.get("SAGE_LOAD_SHAPE") == "1":
        rows, elapsed = [], 0
        for name, seconds, users, _rate in STAGES:
            rows.append(
                {
                    "stage": name,
                    "target_users": users,
                    "start": round(_started_at[0] + elapsed, 3),
                    "end": round(_started_at[0] + elapsed + seconds, 3),
                }
            )
            elapsed += seconds
        write_csv(STAGES_CSV, ["stage", "target_users", "start", "end"], rows)


class Student(HttpUser):
    host = os.environ.get("HOSTED_API_URL", "http://localhost:8000")
    wait_time = between(2, 6)  # a few seconds of think time between operations

    def on_start(self) -> None:
        self._tokens = Tokens(Config())
        self._account = claim_account()
        if self._account is None:
            raise StopUser()  # no accounts left to claim
        self._email = self._account["email"]
        self.client.headers["Authorization"] = (
            f"Bearer {self._tokens.access_token(self._email)}"
        )
        self.plans: list[str] = []
        self._single_chat: str | None = None
        self._pair_chat: str | None = None
        self._setup()
        self._asker = gevent.spawn(self._ask_loop)

    def on_stop(self) -> None:
        asker = getattr(self, "_asker", None)
        if asker is not None:
            asker.kill()

    def _refresh_if_stale(self) -> None:
        # Outside the timed requests, so an auth refresh never counts as an operation
        if self._tokens.refresh_if_older_than(self._email, TOKEN_MAX_AGE):
            self.client.headers["Authorization"] = (
                f"Bearer {self._tokens.access_token(self._email)}"
            )

    def _setup(self) -> None:
        me = self.client.get("/v1/me", name="me", timeout=TIMEOUT).json()
        if not me.get("onboarding_complete"):
            self.client.post(
                "/v1/onboarding/complete",
                json={"curriculum_code": CURRICULUM, "lines": LINES},
                name="first plan set",
                timeout=TIMEOUT,
            )
        questionnaire = self.client.get(
            "/v1/questionnaire", name="questionnaire", timeout=TIMEOUT
        ).json()
        if questionnaire.get("needed"):
            self.client.post(
                "/v1/questionnaire",
                json={"week": "no_preference"},
                name="narrow",
                timeout=TIMEOUT,
            )
        self._load_plans()
        self._open_chats()

    def _load_plans(self) -> None:
        body = self.client.get("/v1/plans", name="plan set", timeout=TIMEOUT).json()
        self.plans = [plan["id"] for plan in body.get("plans", [])]

    def _open_chats(self) -> None:
        if len(self.plans) >= 1:
            chat = self.client.post(
                "/v1/chats",
                json={"plan_id": self.plans[0]},
                name="start chat",
                timeout=TIMEOUT,
            )
            if chat.status_code == 201:
                self._single_chat = chat.json()["id"]
        if len(self.plans) >= 2:
            pair = self.client.post(
                "/v1/chats",
                json={"plan_id": self.plans[0], "other_plan_id": self.plans[1]},
                name="start chat",
                timeout=TIMEOUT,
            )
            if pair.status_code == 201:
                self._pair_chat = pair.json()["id"]

    @task(3)
    def plan_set(self) -> None:
        self._refresh_if_stale()
        self.client.get("/v1/plans", name="plan set", timeout=TIMEOUT)

    @task(3)
    def open_plan(self) -> None:
        self._refresh_if_stale()
        if self.plans:
            self.client.get(
                f"/v1/plans/{random.choice(self.plans)}", name="open", timeout=TIMEOUT
            )

    @task(1)
    def compare(self) -> None:
        self._refresh_if_stale()
        if len(self.plans) >= 2:
            first, second = random.sample(self.plans, 2)
            self.client.get(
                "/v1/plans/compare",
                params={"first": first, "second": second},
                name="pair",
                timeout=TIMEOUT,
            )

    @task(2)
    def check(self) -> None:
        self._refresh_if_stale()
        self.client.get("/v1/electives", name="check", timeout=TIMEOUT)

    @task(2)
    def history(self) -> None:
        self._refresh_if_stale()
        self.client.get("/v1/history", name="history", timeout=TIMEOUT)

    def _ask_loop(self) -> None:
        # Paced apart from the task loop, so questions come about every three minutes rather than
        # mixed in by weight. Stops once the window's 600-question budget is spent.
        index = 0
        while True:
            gevent.sleep(ASK_EVERY + random.uniform(-20, 20))
            question, scope = QUESTIONS[index % len(QUESTIONS)]
            index += 1
            chat = self._single_chat if scope == "single" else self._pair_chat
            if chat is None or not take_question_slot():
                continue
            self._refresh_if_stale()
            self.client.post(
                f"/v1/chats/{chat}/messages",
                json={"content": question},
                name="reply",
                timeout=REPLY_TIMEOUT,
            )


if os.environ.get("SAGE_LOAD_SHAPE") == "1":

    class Stages(LoadTestShape):
        def tick(self) -> tuple[int, float] | None:
            run_time = self.get_run_time()
            elapsed = 0
            for _name, seconds, users, rate in STAGES:
                if run_time < elapsed + seconds:
                    return users, rate
                elapsed += seconds
            return None
