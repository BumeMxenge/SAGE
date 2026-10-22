# The one language model SAGE calls, as an interface: a call with instructions and the conversation
# so far, and optionally a reply schema, tools and a reasoning effort. The advisor depends on this,
# so the provider changes in one adapter, shared/openai.py, and the tests use a scripted fake that
# never calls a model.
from collections.abc import Sequence
from typing import Any, Literal, Protocol

from sage.shared.base import Row


def strict_object(**properties: dict[str, Any]) -> dict[str, Any]:
    # A JSON schema for an object with exactly these properties, all required, as a strict tool or
    # reply needs
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }


class ModelUnavailable(Exception):
    # The model can't be reached: no connection or a timeout, too many requests, or a server error,
    # still failing once the SDK's retries have run out
    pass


class Tool(Row):
    # A function the model may call, its arguments held to the parameters' JSON schema
    name: str
    description: str
    parameters: dict[str, Any]


class Schema(Row):
    # The JSON schema a reply is held to, under the name the provider asks for
    name: str
    shape: dict[str, Any]


class ToolCall(Row):
    id: str  # the provider's id for the call, which its result answers
    name: str
    arguments: dict[str, Any]


class Tokens(Row):
    # A call's tokens: input that was fresh, read from the cache or written to it, and output,
    # reasoning included
    fresh: int = 0
    cached: int = 0
    written: int = 0
    output: int = 0

    def __add__(self, other: "Tokens") -> "Tokens":
        return Tokens(
            **{
                name: getattr(self, name) + getattr(other, name)
                for name in Tokens.model_fields
            }
        )


class Response(Row):
    # One call's answer: the tools it asks for, its text, its tokens, and its output as the provider
    # gave it, which goes back unchanged in the next call's conversation
    calls: tuple[ToolCall, ...] = ()
    text: str | None = None  # None when it was cut off or is still calling tools
    tokens: Tokens = Tokens()
    output: tuple[dict[str, Any], ...] = ()


class Said(Row):
    # Words in the conversation: the student's, or an earlier reply's
    role: Literal["user", "assistant"]
    text: str


class ToolResult(Row):
    # What a tool gave back for one call
    call_id: str
    output: dict[str, Any]


class LanguageModel(Protocol):
    # The model's answer to the conversation under these instructions: held to the schema when one is
    # given, free to call the tools, and reasoning at the effort given or else at the model's default.
    # Raises ModelUnavailable when the model can't be reached.
    def respond(
        self,
        instructions: str,
        conversation: Sequence[Said | Response | ToolResult],
        schema: Schema | None = None,
        tools: Sequence[Tool] = (),
        effort: str | None = None,
    ) -> Response: ...
