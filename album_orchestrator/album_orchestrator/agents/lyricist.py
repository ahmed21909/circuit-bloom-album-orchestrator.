"""
Lyricist agent.

Responsibility: write original lyrics for one track from its brief. When
called again after a rejection, it must incorporate the Meter/Flow Critic's
revision_instructions from the previous round (this is the feedback loop).
"""

from state import AlbumState, Track, TrackStatus
from llm_client import call_agent

SYSTEM_PROMPT = """You are the Lyricist for a concept album. Write complete,
original song lyrics (verse/chorus/verse/chorus/bridge/chorus structure is
fine, adapt as needed) for the track described below. Match the requested
tempo and mood. Do not reference or imitate any real existing song, artist,
or copyrighted lyric. Return ONLY the lyrics text, no commentary, no title
line repeated, no markdown fences."""


def _demo_fn(user_prompt: str) -> str:
    """Deterministic offline stand-in -- produces a short structured lyric."""
    # crude parse of the brief for flavor text so demo output still varies
    return (
        "[Verse 1]\n"
        "Streetlights blink in a language I don't know\n"
        "Every window's a screen with nowhere left to go\n"
        "I keep walking through the same electric rain\n"
        "Looking for a signal that still knows my name\n\n"
        "[Chorus]\n"
        "Hold on, hold on, the static's calling loud\n"
        "Hold on, hold on, I'm just a shape in the crowd\n"
        "But somewhere in the wires there's a light still on\n"
        "Hold on, hold on, until the night is gone\n\n"
        "[Verse 2]\n"
        "Chrome and ash are falling where the old house stood\n"
        "They said it's progress, said it's all for good\n"
        "I saved a photograph before the walls came down\n"
        "The only proof that I was ever in this town\n\n"
        "[Bridge]\n"
        "Maybe the wreckage is where the flowers grow\n"
        "Maybe the static is the only truth I know\n\n"
        "[Chorus]\n"
        "Hold on, hold on, the static's calling loud\n"
        "Hold on, hold on, I'm just a shape in the crowd\n"
        "But somewhere in the wires there's a light still on\n"
        "Hold on, hold on, until the night is gone"
    )


def run(state: AlbumState, track: Track) -> AlbumState:
    if track.revision_count == 0:
        state.log(f"[Lyricist] Writing first draft for track {track.index}: '{track.title}'")
        user_prompt = (
            f"Track title: {track.title}\n"
            f"Brief: {track.brief}\n"
            f"Tempo: {track.tempo}\nMood: {track.mood}\n"
            f"Album context: '{state.album_title}' ({state.genre}) -- {state.concept_statement}"
        )
    else:
        last_feedback = track.feedback_history[-1]
        state.log(f"[Lyricist] Revising track {track.index}: '{track.title}' "
                  f"(revision {track.revision_count})")
        user_prompt = (
            f"Track title: {track.title}\nBrief: {track.brief}\n"
            f"Tempo: {track.tempo}\nMood: {track.mood}\n\n"
            f"Previous draft:\n{track.lyrics}\n\n"
            f"Critic's revision instructions (you MUST address these):\n"
            f"{last_feedback.revision_instructions}"
        )

    track.lyrics = call_agent(SYSTEM_PROMPT, user_prompt, _demo_fn, max_tokens=800)
    track.status = TrackStatus.DRAFTED
    return state
