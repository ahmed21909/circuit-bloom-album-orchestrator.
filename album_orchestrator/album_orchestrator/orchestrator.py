"""
Orchestrator: the dynamic router.

This is deliberately NOT a fixed if-else pipeline. At every step it looks
at the *current AlbumState* and decides which agent should act next:

    state has no concept yet         -> Creative Director
    a track is PLANNED               -> Lyricist (first draft)
    a track is DRAFTED               -> Meter Critic (review)
    a track is NEEDS_REVISION        -> Lyricist again (revision loop)
    all tracks APPROVED/MAX_HIT      -> Visual Stylist
    visuals done                     -> STOP

Because routing is a function of state rather than a hard-coded call
sequence, the same orchestrator loop handles albums of any length and any
number of revision rounds per track without code changes -- this is the
"Dynamic Routing" and "Reflection & Feedback Loops" requirement from the
course brief.
"""

from state import AlbumState, TrackStatus
from agents import creative_director, lyricist, meter_critic, visual_stylist


def route(state: AlbumState) -> str:
    """Pure function: state -> name of the next agent to run, or 'DONE'."""
    if not state.tracks:
        return "creative_director"

    track = state.next_unresolved_track()
    if track is None:
        if not state.cover_art_prompt:
            return "visual_stylist"
        return "DONE"

    if track.status in (TrackStatus.PLANNED, TrackStatus.NEEDS_REVISION):
        return "lyricist"
    if track.status == TrackStatus.DRAFTED:
        return "meter_critic"

    # Should not be reachable, but fail safe rather than loop forever.
    return "DONE"


def run_album_pipeline(user_prompt: str, max_revisions_per_track: int = 3) -> AlbumState:
    state = AlbumState(user_prompt=user_prompt, max_revisions_per_track=max_revisions_per_track)

    step_guard = 0
    MAX_STEPS = 200  # safety valve against any unforeseen routing cycle

    while True:
        step_guard += 1
        if step_guard > MAX_STEPS:
            state.log("[Orchestrator] Step guard tripped -- stopping to avoid an infinite loop.")
            break

        next_agent = route(state)

        if next_agent == "DONE":
            state.log("[Orchestrator] All tracks resolved and visuals generated. Album complete.")
            break

        elif next_agent == "creative_director":
            state = creative_director.run(state)

        elif next_agent == "lyricist":
            track = state.next_unresolved_track()
            state = lyricist.run(state, track)

        elif next_agent == "meter_critic":
            track = state.next_unresolved_track()
            state = meter_critic.run(state, track)

        elif next_agent == "visual_stylist":
            state = visual_stylist.run(state)

    return state
