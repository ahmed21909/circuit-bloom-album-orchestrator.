"""
Entry point.

Usage:
    python main.py "Cyberpunk Melancholy"
    python main.py "Cyberpunk Melancholy" --max-revisions 2 --out sample_output/album.json

Runs LIVE against the Claude API if ANTHROPIC_API_KEY is set in the
environment, otherwise runs in offline DEMO mode (see llm_client.py).
"""

import argparse
import os
from orchestrator import run_album_pipeline
from llm_client import LIVE_MODE, MODEL


def main():
    parser = argparse.ArgumentParser(description="Music Album Concept & Lyrics Designer")
    parser.add_argument("theme", nargs="?", default="Cyberpunk Melancholy",
                         help="One-line album theme, e.g. 'Cyberpunk Melancholy'")
    parser.add_argument("--max-revisions", type=int, default=3,
                         help="Max Lyricist<->Critic revision rounds per track")
    parser.add_argument("--out", default="sample_output/album.json",
                         help="Where to save the final album state as JSON")
    args = parser.parse_args()

    print(f"Mode: {'LIVE (Anthropic API, model=' + MODEL + ')' if LIVE_MODE else 'DEMO (offline simulated agents)'}")
    print(f"Theme: {args.theme}")
    print("-" * 70)

    state = run_album_pipeline(args.theme, max_revisions_per_track=args.max_revisions)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    state.save(args.out)

    print("-" * 70)
    print(f"Saved final album state to {args.out}")
    print(f"\nAlbum: {state.album_title}  ({state.genre})")
    for t in state.tracks:
        print(f"  {t.index}. {t.title:<20} status={t.status.value:<18} revisions={t.revision_count}")


if __name__ == "__main__":
    main()
