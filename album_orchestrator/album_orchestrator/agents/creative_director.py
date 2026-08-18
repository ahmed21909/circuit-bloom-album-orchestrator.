"""
Creative Director agent.

Responsibility: turn a one-line user prompt (e.g. "Cyberpunk Melancholy")
into an album concept: title, overall mood/genre, concept statement, and a
list of per-track briefs (title + emotional intent + tempo/mood) that the
Lyricist will expand into full lyrics.
"""

from state import AlbumState, Track, TrackStatus
from llm_client import call_agent_json

SYSTEM_PROMPT = """You are the Creative Director of a concept album studio.
Given a short theme from the user, invent an original album concept.
Respond ONLY with strict JSON, no prose, no markdown fences, matching this
schema exactly:
{
  "album_title": "string",
  "genre": "string",
  "overall_mood": "string",
  "concept_statement": "2-3 sentence paragraph describing the album's narrative arc",
  "tracks": [
    {"title": "string", "brief": "1-2 sentence emotional intent for the song",
     "tempo": "e.g. slow/mid/uptempo", "mood": "1-3 words"}
  ]
}
Produce between 4 and 6 tracks. All content must be original -- do not
reference or imitate any real existing album, artist, or song."""


def _demo_fn(user_prompt: str) -> str:
    """Deterministic offline stand-in used when no API key is configured."""
    theme = user_prompt.strip() or "Cyberpunk Melancholy"
    tracks = [
        {"title": "Neon Rain", "brief": "Arriving in a city that never remembers your name.",
         "tempo": "mid", "mood": "wistful"},
        {"title": "Static Heartbeat", "brief": "Falling for someone through a screen, unsure if it's real.",
         "tempo": "uptempo", "mood": "anxious"},
        {"title": "Chrome and Ash", "brief": "Watching an old neighborhood get demolished for progress.",
         "tempo": "slow", "mood": "grieving"},
        {"title": "Ghost Signal", "brief": "A late-night radio broadcast to no one, hoping someone hears it.",
         "tempo": "slow", "mood": "lonely"},
        {"title": "Circuit Bloom", "brief": "Finding something like hope in a broken machine.",
         "tempo": "mid", "mood": "fragile hope"},
    ]
    import json
    return json.dumps({
        "album_title": "Circuit Bloom",
        "genre": "synth-pop / dark wave",
        "overall_mood": theme,
        "concept_statement": (
            f"An album about a city drowning in {theme.lower()}, told through the eyes of "
            "someone who keeps looking for warmth in cold, artificial light. Each track moves "
            "the listener one step closer to deciding whether connection is still possible."
        ),
        "tracks": tracks,
    })


def run(state: AlbumState) -> AlbumState:
    state.log("[Creative Director] Drafting album concept from user prompt...")
    data = call_agent_json(SYSTEM_PROMPT, state.user_prompt, _demo_fn)

    state.album_title = data["album_title"]
    state.genre = data["genre"]
    state.overall_mood = data["overall_mood"]
    state.concept_statement = data["concept_statement"]

    for i, t in enumerate(data["tracks"], start=1):
        state.tracks.append(Track(
            index=i,
            title=t["title"],
            brief=t["brief"],
            tempo=t.get("tempo", ""),
            mood=t.get("mood", ""),
            status=TrackStatus.PLANNED,
        ))

    state.log(f"[Creative Director] Concept: '{state.album_title}' "
              f"({state.genre}) -- {len(state.tracks)} tracks planned.")
    return state
