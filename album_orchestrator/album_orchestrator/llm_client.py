"""
Thin wrapper around the Anthropic API.

LIVE mode: if ANTHROPIC_API_KEY is set in the environment, every agent call
goes to the real Claude API (model configurable via CLAUDE_MODEL, default
claude-sonnet-4-6).

DEMO mode: if no API key is present, calls fall back to small local
"simulated agent" functions so the whole orchestration graph (state
management, feedback loops, dynamic routing) can be run, tested and graded
without requiring anyone to hand out an API key. This is what generated
sample_output/ in this repo.

Every agent module below calls `call_agent(system_prompt, user_prompt,
demo_fn)` -- `demo_fn` is only ever invoked in DEMO mode.
"""

import os
import json

MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")
LIVE_MODE = bool(os.environ.get("ANTHROPIC_API_KEY"))

_client = None
if LIVE_MODE:
    try:
        import anthropic
        _client = anthropic.Anthropic()
    except ImportError:
        LIVE_MODE = False


def call_agent(system_prompt: str, user_prompt: str, demo_fn, max_tokens: int = 1200) -> str:
    """
    Returns raw text from the agent. In LIVE_MODE this is a real Claude
    completion; otherwise it is the output of demo_fn(user_prompt), a
    deterministic local stand-in used for offline testing.
    """
    if LIVE_MODE:
        resp = _client.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return "".join(block.text for block in resp.content if block.type == "text")
    return demo_fn(user_prompt)


def call_agent_json(system_prompt: str, user_prompt: str, demo_fn, max_tokens: int = 1200) -> dict:
    """Same as call_agent but parses the response as JSON, stripping code fences."""
    raw = call_agent(system_prompt, user_prompt, demo_fn, max_tokens=max_tokens)
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    return json.loads(cleaned)
