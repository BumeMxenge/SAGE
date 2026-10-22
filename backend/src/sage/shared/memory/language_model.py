# A language model that answers from a script, so the unit tests never call a real one. Each call
# takes the next answer queued under its schema's name, such as "reply" or "title", so two calls that
# run at once never take each other's answers. A queued error is raised instead of answered. Every
# call is kept, so a test can read what was asked.
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

from sage.shared.language_model import Response, Said, Schema, Tool, ToolResult


@dataclass(frozen=True)
class Call:
    instructions: str
    conversation: tuple[Said | Response | ToolResult, ...]
    schema: Schema | None
    tools: tuple[Tool, ...]
    effort: str | None


class ScriptedModel:
    def __init__(
        self, script: Mapping[str | None, Iterable[Response | Exception]]
    ) -> None:
        self._script = {name: list(answers) for name, answers in script.items()}
        self.calls: list[Call] = []

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
        answer = self._script[schema.name if schema else None].pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer
