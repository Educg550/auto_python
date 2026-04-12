"""
Remove duplicate tracks from Spotify playlists.

For every duplicate URI the script:
  1. Removes ALL occurrences from the playlist.
  2. Adds the track back exactly once.

Non-duplicate tracks and local files are never touched.

Usage
-----
    # Clean all playlists owned by the authenticated user
    uv run scripts/automation/spotify/dedupe_playlists.py

    # Clean specific playlists only
    uv run scripts/automation/spotify/dedupe_playlists.py --id <id1> <id2> ...

Environment variables required:
    SPOTIFY_CLIENT_ID
    SPOTIFY_CLIENT_SECRET
    SPOTIFY_REDIRECT_URI  (default: http://localhost:8888/callback)
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter

from lib.logger import get_logger, track

from scripts.automation.spotify import (
    add_playlist_tracks,
    fetch_current_user,
    fetch_playlist_by_id,
    fetch_playlist_tracks,
    fetch_user_playlists,
    get_client,
    remove_playlist_tracks,
)

log = get_logger(__name__)


def _collect_uris(items: list[dict]) -> list[str]:
    """Extract track URIs from raw playlist-track items.

    Skips null items (unavailable tracks) and local files which cannot be
    managed via the Web API.
    """
    uris = []
    for item in items:
        track = item.get("track")
        if not track:
            continue
        uri = track.get("uri") or ""
        if not uri or uri.startswith("spotify:local:"):
            continue
        uris.append(uri)
    return uris


def dedupe_playlist(playlist_id: str, sp) -> int:
    """Remove duplicate tracks from *playlist_id*.

    Returns the number of unique URIs that had duplicates removed.
    """
    items = fetch_playlist_tracks(playlist_id, sp=sp)
    uris = _collect_uris(items)

    if not uris:
        return 0

    counts = Counter(uris)
    duplicate_uris = [uri for uri, n in counts.items() if n > 1]

    if not duplicate_uris:
        return 0

    # Remove all occurrences, then re-add each once.
    remove_playlist_tracks(playlist_id, duplicate_uris, sp=sp)
    add_playlist_tracks(playlist_id, duplicate_uris, sp=sp)

    return len(duplicate_uris)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Remove duplicate tracks from Spotify playlists.",
    )
    parser.add_argument(
        "--id",
        nargs="+",
        dest="playlist_ids",
        metavar="PLAYLIST_ID",
        help="One or more playlist IDs to clean (default: all playlists owned by you).",
    )
    args = parser.parse_args()

    sp = get_client(user_auth=True)

    names: dict[str, str] = {}

    if args.playlist_ids:
        targets = args.playlist_ids
        for pid in targets:
            names[pid] = fetch_playlist_by_id(pid, sp=sp).get("name", pid)
    else:
        user = fetch_current_user(sp=sp)
        user_id = user["id"]
        all_playlists = fetch_user_playlists(user_id, sp=sp)
        owned = [p for p in all_playlists if p["owner"]["id"] == user_id]
        targets = [p["id"] for p in owned]
        names = {p["id"]: p.get("name", p["id"]) for p in owned}

        if not targets:
            log.warning("No playlists owned by you were found.")
            sys.exit(0)

        log.info(f"Found {len(targets)} playlist(s) owned by you.")

    def label(pid: str) -> str:
        return f"{names.get(pid, pid)} ({pid})"

    any_dupes = False
    for playlist_id in track(targets, "Scanning playlists"):
        n = dedupe_playlist(playlist_id, sp)
        if n:
            any_dupes = True
            log.info(
                f"[cleaned]  {label(playlist_id)}  — removed duplicates of {n} track(s)"
            )
        else:
            log.debug(f"[ok]       {label(playlist_id)}  — no duplicates")

    if not any_dupes:
        log.info("All playlists are already duplicate-free.")


if __name__ == "__main__":
    main()
