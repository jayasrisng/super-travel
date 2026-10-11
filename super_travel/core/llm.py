"""Shared Claude client and per-request defaults."""

from __future__ import annotations

from functools import cache
from typing import Any

import anthropic
from dotenv import load_dotenv

MODEL = "claude-opus-5-5"

# Server-side refusal fallback: a declined request is re-run on Anthropic's
# recommended model for that refusal category, inside the same call.
FALLBACK_KWARGS: dict[str, Any] = {
    "betas": ["server-side-fallback-2026-07-01"],
    "fallbacks": "default",
}

WEB_SEARCH_TOOL = {"type": "web_search_20260209", "name": "web_search", "max_uses": 8}
WEB_FETCH_TOOL = {"type": "web_fetch_20260209", "name": "web_fetch", "max_uses": 5}


@cache
def client() -> anthropic.Anthropic:
    load_dotenv()
    return anthropic.Anthropic()


def inline_refs(schema: dict[str, Any]) -> dict[str, Any]:
    """Inline pydantic's $defs/$ref so tool input schemas are self-contained."""
    defs = schema.get("$defs", {})

    def resolve(node: Any) -> Any:
        if isinstance(node, dict):
            if "$ref" in node:
                return resolve(defs[node["$ref"].split("/")[-1]])
            return {k: resolve(v) for k, v in node.items() if k != "$defs"}
        if isinstance(node, list):
            return [resolve(v) for v in node]
        return node

    return resolve(schema)
