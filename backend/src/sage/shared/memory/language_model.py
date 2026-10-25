# A language model that answers from a script, so the unit tests never call a real one. Each call
# takes the next answer queued under its schema's name, such as "reply" or "title", so two calls that
# run at once never take each other's answers. A queued error is raised instead of answered. Calls
# under a held name wait until release(), as a slow model's do. Every call is kept, so a test can
# read what was asked.
from collections.abc import Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass
from threading import Event

from sage.shared.language_model import Response, Said, Schema, Tool, ToolResult


@dataclass(frozen=True)
class Call:
    instructions: str
    conversation: tuple[Said | Response | ToolResult, ...]
    schema: Schema | None
    tools: tuple[Tool, ...]
    effort: str | None


class ScriptedModel:
    model = "a scripted model"

    def __init__(
        self,
        script: Mapping[str | None, Iterable[Response | Exception]],
        held: Collection[str] = (),
    ) -> None:
        self._script = {name: list(answers) for name, answers in script.items()}
        self._held = held
        self._released = Event()
        self.calls: list[Call] = []

    def release(self) -> None:
        self._released.set()

    def respond(
        self,
        instructions: str,
        conversation: Sequence[Said | Response | ToolResult],
        schema: Schema | None = None,
        tools: Sequence[Tool] = (),
        effort: str | None = None,
    ) -> Response:
        self.calls.append(
            Call(instructions, tuple(conversation), schema, tuple(tools), effort)
        )
        name = schema.name if schema else None
        # Long enough for any test to release it, short enough that a forgotten one ends the run
        if name in self._held:
            self._released.wait(10)
        answer = self._script[name].pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer
