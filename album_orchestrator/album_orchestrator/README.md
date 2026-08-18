# Music Album Concept & Lyrics Designer

Multi-agent orchestration system for SENG 456 (Agent Orchestration and
Multimodal Systems). Four LLM agents collaborate through a **dynamically
routed** state machine (no fixed if/else pipeline) to turn a one-line theme
into a full concept album: title, per-track lyrics, and image-generation
prompts for the cover art.

## Agents

| Agent | File | Role |
|---|---|---|
| Creative Director | `agents/creative_director.py` | Sets album title, concept, genre, and a brief for every track |
| Lyricist | `agents/lyricist.py` | Writes/revises full lyrics per track brief (and per critic feedback) |
| Rhythm/Meter Critic | `agents/meter_critic.py` | Audits syllable consistency, rhyme scheme, and flow; approves or rejects with concrete revision instructions |
| Visual Style Agent | `agents/visual_stylist.py` | Generates a Midjourney/DALL-E-style cover prompt and one mood-board prompt per track |

## Orchestration design

`orchestrator.py` implements `route(state) -> next_agent_name`, a pure
function of the current `AlbumState` (see `state.py`). Each loop iteration:

1. Reads the current state (which tracks exist, their status, revision counts).
2. Decides the single next agent to call -- **dynamic routing**, not a
   hard-coded call sequence.
3. Runs that agent, which mutates state.
4. Repeats until every track is `approved` or `max_revisions_hit`, then
   routes to the Visual Stylist, then stops.

The Lyricist <-> Meter Critic loop is the **feedback loop**: a rejected
track goes back to the Lyricist with the critic's `revision_instructions`
attached; the Lyricist's next draft must address them. A
`max_revisions_per_track` cap (default 3) prevents infinite loops -- a
track that still fails after the cap is escalated as `max_revisions_hit`
rather than blocking the album forever.

## Running it

```bash
pip install -r requirements.txt

# DEMO mode (no API key needed) -- runs offline simulated agents so the
# whole state machine / feedback loop / routing logic can be graded without
# any credentials:
python main.py "Cyberpunk Melancholy"

# LIVE mode -- set your own key to call the real Claude API for every agent:
export ANTHROPIC_API_KEY=sk-ant-...
python main.py "Quiet Rebellion" --max-revisions 3
```

Output: console transcript of every agent call and routing decision, plus a
JSON file (`sample_output/album.json` by default) with the full album --
concept, every track's final lyrics and revision history, and the visual
prompts.

## Files

```
album_orchestrator/
  state.py                 # AlbumState, Track, CriticFeedback dataclasses
  llm_client.py             # Anthropic API wrapper + offline demo fallback
  orchestrator.py            # route() dynamic router + main pipeline loop
  agents/
    creative_director.py
    lyricist.py
    meter_critic.py
    visual_stylist.py
  main.py                   # CLI entry point
  sample_output/
    run_transcript.txt      # full console log from a demo run
    album.json              # full album state from a demo run
    album_edge_case.json    # demo run with max-revisions=1 to show escalation path
```

## Notes on demo vs. live mode

No API key is bundled with this submission (per the security checklist).
`llm_client.py` auto-detects `ANTHROPIC_API_KEY`; without it, every agent
call is served by a small deterministic local function (`_demo_fn` in each
agent module) instead of a real completion. This keeps the orchestration
logic -- state management, the critic feedback loop, and dynamic routing --
fully testable and reproducible without credentials, while the exact same
`orchestrator.py`/`route()` code path drives real Claude agents the moment
a key is present.
