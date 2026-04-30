"""
Merge all niche playlists into a single master playlist.

The master playlist is identified by the "[MASTER]" marker in its description.
All other playlists owned by the authenticated user are treated as sources.

The script performs a diff:
  - Tracks present in any niche playlist but missing from master → added.
  - Tracks in master but absent from all niche playlists → removed.
  - Duplicate tracks within master are collapsed to one occurrence.

Local files (spotify:local:…) are skipped.

Usage
-----
    uv run scripts/automation/spotify/merge_playlists.py

Environment variables required:
    SPOTIFY_CLIENT_ID
    SPOTIFY_CLIENT_SECRET
    SPOTIFY_REDIRECT_URI  (default: http://localhost:8888/callback)
"""

from __future__ import annotations

import sys

from lib.logger import get_logger, track

from scripts.automation.spotify import (
    add_playlist_tracks,
    fetch_current_user,
    fetch_playlist_tracks,
    fetch_user_playlists,
    get_client,
    remove_playlist_tracks,
)

log = get_logger(__name__)

MASTER_MARKER = "[MASTER]"


def _collect_uris(items: list[dict]) -> list[str]:
    uris = []
    for item in items:
        t = item.get("track")
        if not t:
            continue
        uri = t.get("uri") or ""
        if not uri or uri.startswith("spotify:local:"):
            continue
        uris.append(uri)
    return uris


def main() -> None:
    sp = get_client(user_auth=True)

    user = fetch_current_user(sp=sp)
    user_id = user["id"]

    all_playlists = fetch_user_playlists(user_id, sp=sp)
    owned = [p for p in all_playlists if p["owner"]["id"] == user_id]

    master = next(
        (p for p in owned if MASTER_MARKER in (p.get("description") or "")),
        None,
    )
    if master is None:
        log.error(
            f'No master playlist found. Add "{MASTER_MARKER}" to a playlist description.'
        )
        sys.exit(1)

    master_id = master["id"]
    master_name = master.get("name", master_id)
    log.info(f'Master playlist: "{master_name}" ({master_id})')

    niche_playlists = [p for p in owned if p["id"] != master_id]
    if not niche_playlists:
        log.warning("No niche playlists found — nothing to merge.")
        sys.exit(0)

    log.info(f"Scanning {len(niche_playlists)} niche playlist(s)…")

    niche_uris: set[str] = set()
    for playlist in track(niche_playlists, "Reading niche playlists"):
        items = fetch_playlist_tracks(playlist["id"], sp=sp)
        niche_uris.update(_collect_uris(items))

    master_items = fetch_playlist_tracks(master_id, sp=sp)
    master_uris: list[str] = _collect_uris(master_items)
    master_uri_set: set[str] = set(master_uris)

    to_add = sorted(niche_uris - master_uri_set)
    to_remove = sorted(master_uri_set - niche_uris)

    # Also remove duplicates that already exist in master.
    seen: set[str] = set()
    duplicates_in_master: list[str] = []
    for uri in master_uris:
        if uri in seen:
            duplicates_in_master.append(uri)
        seen.add(uri)
    # Remove duplicates that will stay in master (not already in to_remove).
    extra_to_remove = [u for u in duplicates_in_master if u not in to_remove]

    if not to_add and not to_remove and not extra_to_remove:
        log.info("Master playlist is already up to date.")
        return

    if to_remove or extra_to_remove:
        all_removals = list(set(to_remove + extra_to_remove))
        log.info(f"Removing {len(to_remove)} stale + {len(extra_to_remove)} duplicate track(s)…")
        remove_playlist_tracks(master_id, all_removals, sp=sp)
        # Re-add the duplicates that should stay (they were valid niche tracks).
        duplicates_to_readd = [u for u in extra_to_remove if u in niche_uris]
        if duplicates_to_readd:
            add_playlist_tracks(master_id, duplicates_to_readd, sp=sp)

    if to_add:
        log.info(f"Adding {len(to_add)} new track(s)…")
        add_playlist_tracks(master_id, to_add, sp=sp)

    log.info("Done.")


if __name__ == "__main__":
    main()
