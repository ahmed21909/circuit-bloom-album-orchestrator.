"""
Visual Style (Prompt) agent.

Responsibility: once every track is resolved (approved or max-revisions
escalated), generate an image-generation prompt (Midjourney/DALL-E style)
for the album cover, plus one short mood-board prompt per track.
"""

from state import AlbumState
from llm_client import call_agent_json

SYSTEM_PROMPT = """You are the Visual Style Prompt Agent for a concept
album. Given the album concept and its finished tracklist, write one
detailed album-cover image-generation prompt (composition, color palette,
lighting, style references to *art movements*, never to real living
artists or copyrighted characters) and one short per-track mood-board
prompt for each track. Respond ONLY with strict JSON:
{
  "cover_art_prompt": "string",
  "track_visual_prompts": ["string", "..."]
}
The track_visual_prompts array must have exactly as many entries as tracks,
in the same order."""


def _demo_fn(user_prompt: str) -> str:
    import json
    return json.dumps({
        "cover_art_prompt": (
            "Album cover, wide shot of a rain-slicked city street at night, neon signage "
            "reflected in puddles, a single silhouette walking away from camera, "
            "cyan-and-magenta color palette, soft volumetric fog, synthwave illustration "
            "style, painterly digital art, high contrast, 1:1 square composition"
        ),
        "track_visual_prompts": [
            "Neon-lit alley reflected in a puddle, cyan and magenta glow, lonely figure in the distance",
            "Close-up of a hand touching a glowing phone screen in the dark, warm light against cold blue shadows",
            "Demolition site at dusk, dust catching amber light, a lone photograph on the ground",
            "Old radio tower against a starless sky, a single window lit in an empty apartment block",
            "A cracked circuit board with a small flower growing through it, soft golden light",
        ],
    })


def run(state: AlbumState) -> AlbumState:
    state.log("[Visual Stylist] Generating album cover and per-track visual prompts...")
    tracklist = "\n".join(f"{t.index}. {t.title} -- {t.mood}" for t in state.tracks)
    user_prompt = (
        f"Album: {state.album_title} ({state.genre})\n"
        f"Concept: {state.concept_statement}\nOverall mood: {state.overall_mood}\n"
        f"Tracklist:\n{tracklist}"
    )
    data = call_agent_json(SYSTEM_PROMPT, user_prompt, _demo_fn)
    state.cover_art_prompt = data["cover_art_prompt"]
    state.track_visual_prompts = data["track_visual_prompts"]
    state.log("[Visual Stylist] Done.")
    return state
