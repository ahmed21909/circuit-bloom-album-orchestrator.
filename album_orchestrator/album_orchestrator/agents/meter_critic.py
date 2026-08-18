"""
Rhythm / Meter Critic agent.

Responsibility: audit a lyric draft for syllable-count consistency across
matching sections (e.g. both choruses should scan the same), rhyme scheme
integrity, and overall flow against the requested tempo. Produces a
structured, machine-readable verdict that the orchestrator uses to decide
whether to route back to the Lyricist (feedback loop) or forward to the
Visual Style agent.
"""

from state import AlbumState, Track, TrackStatus, CriticFeedback
from llm_client import call_agent_json

SYSTEM_PROMPT = """You are the Rhythm/Meter Critic for a concept album.
Audit the given lyric draft against its brief and tempo. Check: (1) do the
repeated choruses/refrains scan with consistent syllable counts, (2) is the
rhyme scheme intentional and consistent within each section, (3) does the
pacing (line length, word density) match the requested tempo and mood.
Be a real critic -- do not rubber-stamp every draft; on the first pass find
at least one concrete issue unless the draft is genuinely flawless.
Respond ONLY with strict JSON matching this schema:
{
  "approved": true/false,
  "syllable_notes": "string",
  "rhyme_notes": "string",
  "flow_notes": "string",
  "revision_instructions": "string -- empty if approved, otherwise concrete, actionable instructions"
}"""


def _demo_fn(user_prompt: str) -> str:
    """
    Deterministic offline stand-in. To make the feedback loop visible in the
    demo transcript, the FIRST pass on every track is rejected with a
    concrete note, and the SECOND pass (after revision) is approved.
    """
    import json
    if "revision instructions" in user_prompt.lower() or "previous draft" in user_prompt.lower():
        return json.dumps({
            "approved": True,
            "syllable_notes": "Both chorus passes now scan at a consistent 9-10 syllables per line.",
            "rhyme_notes": "AABB pattern is now held consistently through verse 2.",
            "flow_notes": "Line lengths match the requested tempo; the bridge lands as a breath before the final chorus.",
            "revision_instructions": "",
        })
    return json.dumps({
        "approved": False,
        "syllable_notes": "Line 3 of verse 1 runs noticeably longer (14 syllables) than its neighbors (~9-10), breaking the scan.",
        "rhyme_notes": "Verse 2 drifts from the AABB pattern established in verse 1 -- the third line doesn't rhyme with the fourth.",
        "flow_notes": "The bridge is a touch too long for the requested tempo and slows momentum right before the final chorus.",
        "revision_instructions": (
            "Trim verse 1 line 3 to roughly 9-10 syllables to match its neighbors. "
            "Fix the verse 2 rhyme so lines 3-4 rhyme, matching the AABB pattern from verse 1. "
            "Shorten the bridge by one line to keep momentum into the final chorus."
        ),
    })


def run(state: AlbumState, track: Track) -> AlbumState:
    state.log(f"[Meter Critic] Reviewing track {track.index}: '{track.title}' "
              f"(pass {track.revision_count + 1})")
    user_prompt = (
        f"Track title: {track.title}\nBrief: {track.brief}\n"
        f"Tempo: {track.tempo}\nMood: {track.mood}\n\n"
        f"Lyrics draft:\n{track.lyrics}"
    )
    if track.revision_count > 0:
        user_prompt += "\n\n(This is a revision -- check whether prior revision instructions were addressed.)"

    data = call_agent_json(SYSTEM_PROMPT, user_prompt, _demo_fn)
    feedback = CriticFeedback(
        approved=data["approved"],
        syllable_notes=data["syllable_notes"],
        rhyme_notes=data["rhyme_notes"],
        flow_notes=data["flow_notes"],
        revision_instructions=data["revision_instructions"],
    )
    track.feedback_history.append(feedback)

    if feedback.approved:
        track.status = TrackStatus.APPROVED
        state.log(f"[Meter Critic] APPROVED: '{track.title}'")
    else:
        track.revision_count += 1
        if track.revision_count >= state.max_revisions_per_track:
            track.status = TrackStatus.MAX_REVISIONS_HIT
            state.log(f"[Meter Critic] REJECTED again -- max revisions "
                      f"({state.max_revisions_per_track}) reached for '{track.title}', "
                      f"escalating as-is.")
        else:
            track.status = TrackStatus.NEEDS_REVISION
            state.log(f"[Meter Critic] REJECTED: '{track.title}' -- "
                      f"{feedback.revision_instructions}")
    return state
