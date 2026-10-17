# Claude drafts a rule tree for wording the grammar refuses, provisionally until the advisor milestone
# picks one model for drafting and the advisor. It's asked as E2 asked it: E2's prompt, the field's
# name with its printed text, room for the thinking that's on by default, and no output_config, as
# Haiku's structured output compiles a rule tree only three levels deep. translate checks every draft
# against EntryRule before keeping it.
import json
import re
from collections import Counter
from pathlib import Path
from typing import Literal

from anthropic import Anthropic
from pydantic import JsonValue

# E2's prompt.md, copied unchanged, sent from after its opening note for people, split as E2's
# drafting.py splits it
PROMPT = (
    Path(__file__)
    .with_name("drafting_prompt.md")
    .read_text(encoding="utf-8")
    .split("\n---\n", 1)[1]
    .strip()
)
# Room for the model's thinking as well as its answer
MAX_TOKENS = 16_000
# A code fence around an answer, which the model may add with no schema holding it to plain JSON
FENCE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)
# The label each need is printed under, which the model reads with the text
FIELDS = {"pass": "Course entry requirements", "concurrent": "Co-requisites"}
# USD per million tokens, by model, from platform.claude.com/docs/en/about-claude/pricing on
# 13 October 2026, as E2 priced them
PRICES = {"claude-haiku-5-5": {"input": 0.10, "cached": 0.01, "output": 0.50}}


class ClaudeDrafter:
    def __init__(self, api_key: str, model: str) -> None:
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.tokens: Counter[str] = Counter()  # over every draft asked for

    def draft(self, printed: str, need: Literal["pass", "concurrent"]) -> JsonValue:
        reply = self.client.messages.create(
            model=self.model,
            max_tokens=MAX_TOKENS,
            system=PROMPT,
            messages=[{"role": "user", "content": f"{FIELDS[need]}: {printed}"}],
        )
        self.tokens.update(
            input=reply.usage.input_tokens,
            cached=reply.usage.cache_read_input_tokens or 0,
            output=reply.usage.output_tokens,
        )
        text = "".join(b.text for b in reply.content if b.type == "text").strip()
        fenced = FENCE.match(text)
        # An answer that isn't JSON holding a rule raises, and the run stops
        return json.loads(fenced[1] if fenced else text)["rule"]

    @property
    def cost(self) -> float:
        # In USD, for every draft asked for
        prices = PRICES[self.model]
        return sum(self.tokens[kind] * price for kind, price in prices.items()) / 1e6
