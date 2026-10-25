# Asks the real advisor about a student's plans, with no database: Mbali's seed by default, another
# seed file in its shape, or a student on track in a curriculum and year, as show_plans.py makes
# one. Her record goes into the in-memory stores beside the approved snapshot of the year SAGE
# plans, and a record with no plans gets them from the engine, as onboarding would. A set of more
# than five plans needs her questionnaire answers before she can chat. The engine's eligibility
# checker and Luna answer. It takes a plan or a pair, the term on screen, and one or more questions
# asked in turn in one new chat, and prints each reply with what went into it, then the run's cost
# and turn times. Every question calls OpenAI, which costs money, so OPENAI_API_KEY must be in
# backend/.env.
# From backend/: uv run python scripts/ask_advisor.py --plan V01 --term sem1 "First?" "Then?"
# or: uv run python scripts/ask_advisor.py --curriculum EB022EEE02 --year 3 --plan V01 "First?"
import argparse
import json
import logging
import statistics
import sys
from pathlib import Path
from typing import get_args
from uuid import UUID

from show_plans import ACCOUNT, SYMBOLS, on_track

from sage.advisor.replies import Answered, GroundedAdvisor
from sage.config import get_settings
from sage.engine.eligibility import EntryRuleEligibility
from sage.engine.generator import ClingoPlanGenerator
from sage.features.chats import service as chats
from sage.features.onboarding import service as onboarding
from sage.features.questionnaire import service as questionnaire
from sage.ingestion.ingest import approved_snapshot
from sage.shared.advisor import Reply
from sage.shared.language_model import Tokens
from sage.shared.memory.rules import InMemoryRuleRepository
from sage.shared.memory.students import InMemoryStudentRepository
from sage.shared.openai import MODEL, OpenAIModel
from sage.shared.rulebook import Rulebook
from sage.shared.rules import ResultSymbol, TermCode
from sage.shared.seed import SEED_FILE, load_seed, seed
from sage.shared.students import Chat, Plan, StudentState

YEAR = 2026  # the year SAGE plans, whose approved rules every run loads


class Recorded:
    # The advisor, keeping the details of its last answer for printing
    def __init__(self, advisor: GroundedAdvisor) -> None:
        self.advisor = advisor
        self.last: Answered | None = None

    def reply(self, chat: Chat, question: str, term: str | None) -> Reply:
        self.last = self.advisor.answer(chat, question, term)
        return self.last.reply


def show(
    number: int,
    question: str,
    answered: Answered,
    plans: dict[UUID, Plan],
    model: OpenAIModel,
) -> float:
    # Prints one reply with what went into it, and returns its cost in USD
    reply, checked, turn = answered.reply, answered.checked, answered.turn
    offered = plans.get(reply.open_plan_id)
    print(f"\n{number}. {question}")
    print(f"Reply: {reply.content}")
    print(f"Referral: {'yes' if reply.referral else 'no'}")
    if offered:
        hidden = "hidden" if offered.hidden else "shown"
        print(f"Plan offered: V{offered.position:02d} {offered.name}, {hidden}")
    else:
        print("Plan offered: none")
    for citation in reply.citations:
        print(
            f'Citation {citation.position}: "{citation.quote}" '
            f"({citation.section}, page {citation.page})"
        )
    for quote in checked.dropped:
        print(f'Quote dropped: {quote.passage_id} "{quote.quote}"')
    if checked.unoffered:
        print(f"Plan offer dropped: {checked.unoffered}")
    for flag in checked.flags:
        print(f"Flag: {flag.kind} {flag.mark}")
    for called in turn.called:
        print(f"Tool: {called.name} {json.dumps(called.arguments)}")
        print(f"  gave {json.dumps(called.result)}")
    title = reply.title or "none (the chat had one, or it wasn't ready or failed)"
    print(f"Title: {title}")
    for call, response in enumerate(turn.responses, start=1):
        tokens = response.tokens
        given = tokens.fresh + tokens.cached + tokens.written
        print(
            f"Call {call}: {given:,} tokens in ({tokens.cached:,} cached, "
            f"{tokens.written:,} written), {tokens.output:,} out"
        )
    used = sum((response.tokens for response in turn.responses), Tokens())
    if answered.named:
        used += answered.named.tokens
    cost = model.cost(used)
    print(f"Seconds: {answered.seconds:.1f}, cost: USD {cost:.5f}")
    return cost


def main() -> None:
    parser = argparse.ArgumentParser(prog="ask_advisor")
    parser.add_argument(
        "--plan",
        action="append",
        required=True,
        help="a plan by its id, such as V01, once or twice for a pair",
    )
    parser.add_argument("--term", default="sem1", choices=get_args(TermCode))
    parser.add_argument(
        "--seed",
        type=Path,
        help="a seed file whose student to ask about, Mbali's if none",
    )
    parser.add_argument(
        "--curriculum", help="a curriculum code, for an on-track student"
    )
    parser.add_argument(
        "--year", type=int, help="her year of study, for an on-track student"
    )
    parser.add_argument(
        "--answers",
        type=json.loads,
        help='her questionnaire answers, which over five plans need, as {"course": "EEE4121F"}',
    )
    parser.add_argument("questions", nargs="+", help="asked in turn in one chat")
    arguments = parser.parse_args()
    if len(arguments.plan) > 2:
        parser.error("give one plan, or two for a pair")
    if bool(arguments.curriculum) != bool(arguments.year):
        parser.error("give --curriculum with --year")
    if arguments.seed and arguments.curriculum:
        parser.error("give --seed or --curriculum, not both")
    settings = get_settings()
    if not settings.openai_api_key:
        sys.exit("Set OPENAI_API_KEY in backend/.env first.")
    # Each warning and turn line goes to the terminal, as it would to the app's logs
    logging.basicConfig(format="%(levelname)s %(name)s: %(message)s")
    logging.getLogger("sage").setLevel(logging.INFO)

    symbols = tuple(
        ResultSymbol.model_validate(row)
        for row in json.loads(SYMBOLS.read_text(encoding="utf-8"))
    )
    rules, students = InMemoryRuleRepository(symbols), InMemoryStudentRepository()
    rules.replace_year(approved_snapshot(YEAR).rules)
    rulebook = Rulebook(rules)
    if arguments.curriculum:
        student, history = on_track(
            rulebook.year(YEAR), arguments.curriculum, arguments.year
        )
        state = StudentState(student=student, course_history=tuple(history))
    else:
        state = load_seed(arguments.seed or SEED_FILE, ACCOUNT)
    seed(rules, students, state)
    # A record with no plans gets them as onboarding gives them, from the engine
    if students.current_plan_set(ACCOUNT) is None:
        onboarding.complete(
            ACCOUNT,
            state.student.curriculum_code,
            state.course_history,
            students,
            rulebook,
            ClingoPlanGenerator(),
        )
    # She answers the questionnaire before she can chat, as the app asks her to
    if arguments.answers:
        questionnaire.answer(
            students, rulebook, students.get(ACCOUNT).student, arguments.answers
        )
    plans = {plan.id: plan for plan in students.get(ACCOUNT).plans}
    by_position = {plan.position: plan for plan in plans.values()}
    chosen = [by_position[int(plan.removeprefix("V"))].id for plan in arguments.plan]
    chat = chats.start(students, ACCOUNT, chosen[0], chosen[1] if chosen[1:] else None)

    model = OpenAIModel(settings.openai_api_key, MODEL)
    advisor = Recorded(
        GroundedAdvisor(model, students, rulebook, EntryRuleEligibility())
    )
    costs, seconds = [], []
    for number, question in enumerate(arguments.questions, start=1):
        chats.ask(students, advisor, ACCOUNT, chat.id, question, arguments.term)
        costs.append(show(number, question, advisor.last, plans, model))
        seconds.append(advisor.last.seconds)
    print(f"\n{len(seconds)} turns, cost USD {sum(costs):.5f}")
    if len(seconds) > 1:
        p95 = statistics.quantiles(seconds, n=100, method="inclusive")[94]
        print(f"95th-percentile turn {p95:.1f} s, slowest {max(seconds):.1f} s")


if __name__ == "__main__":
    main()
