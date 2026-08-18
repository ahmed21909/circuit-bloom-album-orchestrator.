"""
Shared state objects for the Music Album Concept & Lyrics Designer.

All agents read from and write to a single AlbumState instance. The
orchestrator inspects this state after every agent call to decide which
agent runs next (dynamic routing) instead of following a hard-coded
if/else pipeline.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
import json


class TrackStatus(str, Enum):
    PLANNED = "planned"          # brief exists, no lyrics yet
    DRAFTED = "drafted"          # lyricist has produced a draft
    NEEDS_REVISION = "needs_revision"  # critic rejected the draft
    APPROVED = "approved"        # critic approved the draft
    MAX_REVISIONS_HIT = "max_revisions_hit"  # gave up after N tries


@dataclass
class CriticFeedback:
    approved: bool
    syllable_notes: str
    rhyme_notes: str
    flow_notes: str
    revision_instructions: str


@dataclass
class Track:
    index: int
    title: str
    brief: str                      # emotional intent / theme for this track
    tempo: str = ""
    mood: str = ""
    lyrics: str = ""
    status: TrackStatus = TrackStatus.PLANNED
    revision_count: int = 0
    feedback_history: List[CriticFeedback] = field(default_factory=list)

    def to_dict(self):
        d = dict(
            index=self.index,
            title=self.title,
            brief=self.brief,
            tempo=self.tempo,
            mood=self.mood,
            lyrics=self.lyrics,
            status=self.status.value,
            revision_count=self.revision_count,
            feedback_history=[fb.__dict__ for fb in self.feedback_history],
        )
        return d


@dataclass
class AlbumState:
    user_prompt: str
    album_title: str = ""
    concept_statement: str = ""
    overall_mood: str = ""
    genre: str = ""
    tracks: List[Track] = field(default_factory=list)
    cover_art_prompt: str = ""
    track_visual_prompts: List[str] = field(default_factory=list)
    max_revisions_per_track: int = 3
    event_log: List[str] = field(default_factory=list)

    def log(self, message: str):
        self.event_log.append(message)
        print(message)

    def all_tracks_resolved(self) -> bool:
        """True once every track is either approved or has exhausted revisions."""
        return all(
            t.status in (TrackStatus.APPROVED, TrackStatus.MAX_REVISIONS_HIT)
            for t in self.tracks
        )

    def next_unresolved_track(self) -> Optional[Track]:
        for t in self.tracks:
            if t.status not in (TrackStatus.APPROVED, TrackStatus.MAX_REVISIONS_HIT):
                return t
        return None

    def to_dict(self):
        return dict(
            user_prompt=self.user_prompt,
            album_title=self.album_title,
            concept_statement=self.concept_statement,
            overall_mood=self.overall_mood,
            genre=self.genre,
            tracks=[t.to_dict() for t in self.tracks],
            cover_art_prompt=self.cover_art_prompt,
            track_visual_prompts=self.track_visual_prompts,
            event_log=self.event_log,
        )

    def save(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
