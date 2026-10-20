# The prompts file as types: every candidate prompt, the four chosen for each stressor with their
# labels, and check_eligibility's verdicts for courses outside her plans. I edit data/prompts.toml
# in VS Code, and check_labels.py checks it against the evidence.
import tomllib
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, field_validator
from sage.shared.base import Row
from sage.shared.planning import Eligibility, EligibilityStatus
from sage.shared.rules import TermCode

FILE = Path(__file__).parent / "data" / "prompts.toml"
# The eight stressors, four in each part
STRESSORS = {
    "A": ("control", "buried", "prior trap", "refer"),
    "B": ("control", "conditional", "not eligible", "plan action"),
}
Stressor = Literal[
    "control",
    "buried",
    "prior trap",
    "refer",
    "conditional",
    "not eligible",
    "plan action",
]


class Prompt(Row):
    id: str
    part: Literal["A", "B"]
    stressor: Stressor
    chosen: bool = False
    plans: tuple[str, ...]  # the open plan, or the pair being compared
    term: TermCode = "sem1"  # the term on screen
    question: str
    why: str = ""  # the drafting note: the tempting wrong answer, and where to look
    # The label, from print. An empty value is one not filled in yet.
    outcome: Literal["answer", "refer", ""] = ""
    passages: tuple[str, ...] = ()  # sections, as the slice heads them
    key: tuple[str, ...] = ()  # words or numbers a right answer states
    trap: tuple[str, ...] = ()  # words or numbers that mark the tempting wrong answer
    tool: Literal["get_course", "find_plan", "check_eligibility", ""] = ""
    # The least a right call asks for
    arguments: dict[str, Any] = Field(default_factory=dict)
    verdict: EligibilityStatus | Literal[""] = ""
    plan: str = ""  # on a plan action: the plan to offer, or "none"
    notes: str = ""


class Sheet(Row):
    prompts: tuple[Prompt, ...]
    # By course code, each written from print
    verdicts: dict[str, Eligibility] = Field(default_factory=dict)

    @field_validator("verdicts", mode="before")
    @classmethod
    def _no_empty_fields(cls, verdicts: dict) -> dict:
        # A field left empty in the file is one not given, so an eligible verdict's empty reason
        # becomes none, as the engine gives an eligible course no reason
        return {
            code: {name: value for name, value in fields.items() if value != ""}
            for code, fields in verdicts.items()
        }


def raw(path: Path = FILE) -> dict:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def load(path: Path = FILE) -> Sheet:
    return Sheet.model_validate(raw(path))


def chosen(sheet: Sheet) -> list[Prompt]:
    return [prompt for prompt in sheet.prompts if prompt.chosen]
