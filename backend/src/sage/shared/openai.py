# GPT-6 Luna, SAGE's one language model since E4, through OpenAI's Responses API, filling
# shared/language_model.py. Each call is sent as E4's asking.py sent Luna: the instructions, the tools
# and the reply schema both strict, and each earlier output passed back as it came, reasoning items
# included. It sets no sampling or reasoning unless asked, so Luna runs at its defaults, and the SDK
# keeps its two retries. The one difference from E4's requests: OpenAI stores none of them.
import json
from collections.abc import Sequence
from typing import Any

from openai import APIConnectionError, InternalServerError, OpenAI, RateLimitError

from sage.shared.language_model import (
    ModelUnavailable,
    Response,
    Said,
    Schema,
    Tokens,
    Tool,
    ToolCall,
    ToolResult,
)

# Seconds one attempt at a call may take, so a slow call ends inside the advisor's 50-second turn
CALL_LIMIT = 45
# The errors the SDK retries, which mean the model can't be reached once its retries run out: no
# connection or a timeout, too many requests, and a server error. Any other error, such as a bad key
# or a malformed request, is a fault in SAGE, so it isn't caught.
UNREACHABLE = (APIConnectionError, RateLimitError, InternalServerError)
# USD per million tokens, by model, from developers.openai.com/api/docs/pricing on 22 October 2026.
# Writing the cache costs 1.25 times fresh input, for its default 30 minutes.
PRICES = {
    "gpt-6-luna": {"fresh": 0.10, "cached": 0.01, "written": 0.125, "output": 0.50}
}


class OpenAIModel:
    def __init__(self, api_key: str, model: str) -> None:
        self.client = OpenAI(api_key=api_key, timeout=CALL_LIMIT)
        self.model = model

    def respond(
        self,
        instructions: str,
        conversation: Sequence[Said | Response | ToolResult],
        schema: Schema | None = None,
        tools: Sequence[Tool] = (),
        effort: str | None = None,
    ) -> Response:
        body: dict[str, Any] = {
            "model": self.model,
            "instructions": instructions,
            # SAGE never reads a response back, so OpenAI keeps none, beyond its abuse logs
            "store": False,
        }
        if tools:
            body["tools"] = [
                {
                    "type": "function",
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                    "strict": True,
                }
                for tool in tools
            ]
        if schema:
            body["text"] = {
                "format": {
                    "type": "json_schema",
                    "name": schema.name,
                    "schema": schema.shape,
                    "strict": True,
                }
            }
        if effort:
            body["reasoning"] = {"effort": effort}
        body["input"] = [item for turn in conversation for item in _items(turn)]
        try:
            reply = self.client.responses.create(**body)
        except UNREACHABLE as error:
            raise ModelUnavailable(type(error).__name__) from error
        return _read(reply.model_dump(mode="json"))

    def cost(self, tokens: Tokens) -> float:
        # In USD, from the price line
        prices = PRICES[self.model]
        return (
            sum(getattr(tokens, kind) * price for kind, price in prices.items()) / 1e6
        )


def _items(turn: Said | Response | ToolResult) -> list[dict[str, Any]]:
    # One turn of the conversation as the Responses API takes it
    if isinstance(turn, Said):
        return [{"role": turn.role, "content": turn.text}]
    if isinstance(turn, ToolResult):
        return [
            {
                "type": "function_call_output",
                "call_id": turn.call_id,
                "output": json.dumps(turn.output),
            }
        ]
    return list(turn.output)


def _read(raw: dict[str, Any]) -> Response:
    # A reply's tool calls, text and tokens. OpenAI counts every input token in input_tokens, those
    # read from the cache and written to it among them.
    output = raw["output"]
    calls = tuple(
        ToolCall(
            id=item["call_id"],
            name=item["name"],
            arguments=json.loads(item["arguments"]),
        )
        for item in output
        if item["type"] == "function_call"
    )
    text = None
    if raw["status"] == "completed" and not calls:
        text = "".join(
            part["text"]
            for item in output
            if item["type"] == "message"
            for part in item["content"]
            if part["type"] == "output_text"
        )
    usage = raw["usage"]
    details = usage["input_tokens_details"]
    cached, written = details["cached_tokens"], details.get("cache_write_tokens") or 0
    return Response(
        calls=calls,
        text=text,
        tokens=Tokens(
            fresh=usage["input_tokens"] - cached - written,
            cached=cached,
            written=written,
            output=usage["output_tokens"],
        ),
        output=tuple(_echo(item) for item in output),
    )


def _echo(value: Any) -> Any:
    # An output item as the API takes it back: unchanged, less the empty fields the SDK fills in
    if isinstance(value, dict):
        return {key: _echo(item) for key, item in value.items() if item is not None}
    if isinstance(value, list):
        return [_echo(item) for item in value]
    return value
