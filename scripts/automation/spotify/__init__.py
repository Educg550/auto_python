"""
Spotify API utilities — atomic helpers wrapping spotipy.

Authentication
--------------
Two flows are supported:

* **Client Credentials** (default) — no user interaction; read-only access to
  public data (playlists, tracks, artists …).
* **OAuth / Authorization Code** — required for user-scoped endpoints such as
  liked songs.  Set ``user_auth=True`` when calling :func:`get_client`.

Environment variables (set them or pass explicitly):
  SPOTIFY_CLIENT_ID      – your Spotify application client ID
  SPOTIFY_CLIENT_SECRET  – your Spotify application client secret
  SPOTIFY_REDIRECT_URI   – redirect URI registered in your app (OAuth only)

Usage
-----
    from scripts.automation.spotify import get_client, fetch_playlist_tracks

    sp = get_client()
    tracks = fetch_playlist_tracks("37i9dQZF1DXcBWIGoYBM5M", sp=sp)
"""

from __future__ import annotations

import os
from typing import Iterator
from dotenv import load_dotenv

load_dotenv()

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth

# Scopes needed for user-specific endpoints.
_USER_SCOPES = (
    "user-library-read "
    "playlist-read-private "
    "playlist-read-collaborative "
    "playlist-modify-public "
    "playlist-modify-private "
    "user-top-read "
    "user-read-recently-played"
)

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


def get_client(
    *,
    user_auth: bool = False,
    client_id: str | None = None,
    client_secret: str | None = None,
    redirect_uri: str | None = None,
    scopes: str = _USER_SCOPES,
) -> spotipy.Spotify:
    """Return an authenticated :class:`spotipy.Spotify` client.

    Parameters
    ----------
    user_auth:
        ``True`` → Authorization Code flow (required for liked songs and other
        user-scoped endpoints). ``False`` → Client Credentials flow (public data).
    client_id / client_secret:
        Override the ``SPOTIFY_CLIENT_ID`` / ``SPOTIFY_CLIENT_SECRET`` env vars.
    redirect_uri:
        Override ``SPOTIFY_REDIRECT_URI`` (only used when ``user_auth=True``).
    scopes:
        Space-separated Spotify scopes (only used when ``user_auth=True``).
    """
    cid = client_id or os.environ["SPOTIFY_CLIENT_ID"]
    secret = client_secret or os.environ["SPOTIFY_CLIENT_SECRET"]

    if user_auth:
        uri = redirect_uri or os.environ.get(
            "SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback"
        )
        auth_manager = SpotifyOAuth(
            client_id=cid,
            client_secret=secret,
            redirect_uri=uri,
            scope=scopes,
        )
    else:
        auth_manager = SpotifyClientCredentials(
            client_id=cid,
            client_secret=secret,
        )

    return spotipy.Spotify(auth_manager=auth_manager)


# ---------------------------------------------------------------------------
# Internal pagination helper
# ---------------------------------------------------------------------------


def _paginate(sp: spotipy.Spotify, page: dict) -> Iterator[dict]:
    """Yield every item from a paged Spotify response, following ``next`` links."""
    while page:
        yield from page["items"]
        page = sp.next(page) if page.get("next") else None


# ---------------------------------------------------------------------------
# Playlist endpoints
# ---------------------------------------------------------------------------


def fetch_playlist_by_id(
    playlist_id: str, *, sp: spotipy.Spotify | None = None
) -> dict:
    """Return full playlist metadata for *playlist_id*.

    Parameters
    ----------
    playlist_id:
        Spotify playlist ID, URI (``spotify:playlist:…``), or URL.
    sp:
        Authenticated client; a Client Credentials client is created if omitted.
    """
    sp = sp or get_client()
    return sp.playlist(playlist_id)


def fetch_playlist_tracks(
    playlist_id: str,
    *,
    sp: spotipy.Spotify | None = None,
    fields: str | None = None,
    market: str | None = None,
) -> list[dict]:
    """Return every track item in a playlist (handles pagination automatically).

    Each item is the raw Spotify ``PlaylistTrackObject`` which includes
    ``track``, ``added_at``, and ``added_by`` fields.

    Parameters
    ----------
    playlist_id:
        Playlist ID, URI, or URL.
    fields:
        Optional comma-separated field filter (e.g. ``"items(track(name,id))"``).
    market:
        ISO 3166-1 alpha-2 country code for track relinking.
    """
    sp = sp or get_client()
    kwargs: dict = {"limit": 100}
    if fields:
        kwargs["fields"] = fields
    if market:
        kwargs["market"] = market

    first_page = sp.playlist_tracks(playlist_id, **kwargs)
    return list(_paginate(sp, first_page))


def fetch_user_playlists(
    user_id: str, *, sp: spotipy.Spotify | None = None
) -> list[dict]:
    """Return all playlists owned or followed by *user_id*.

    Parameters
    ----------
    user_id:
        Spotify user ID or URI.
    """
    sp = sp or get_client()
    first_page = sp.user_playlists(user_id, limit=50)
    return list(_paginate(sp, first_page))


# ---------------------------------------------------------------------------
# User-scoped endpoints  (require OAuth / user_auth=True)
# ---------------------------------------------------------------------------


def fetch_liked_songs(*, sp: spotipy.Spotify | None = None) -> list[dict]:
    """Return all tracks saved in the authenticated user's *Liked Songs*.

    Requires an OAuth client with the ``user-library-read`` scope:

        sp = get_client(user_auth=True)
        liked = fetch_liked_songs(sp=sp)

    Each item is a Spotify ``SavedTrackObject`` containing ``track`` and
    ``added_at`` fields.
    """
    sp = sp or get_client(user_auth=True)
    first_page = sp.current_user_saved_tracks(limit=50)
    return list(_paginate(sp, first_page))


def fetch_current_user(*, sp: spotipy.Spotify | None = None) -> dict:
    """Return the profile of the currently authenticated user.

    Requires an OAuth client.
    """
    sp = sp or get_client(user_auth=True)
    return sp.current_user()


def fetch_user_top_tracks(
    *,
    sp: spotipy.Spotify | None = None,
    time_range: str = "medium_term",
    limit: int = 50,
) -> list[dict]:
    """Return the authenticated user's top tracks.

    Parameters
    ----------
    time_range:
        ``"short_term"`` (~4 weeks), ``"medium_term"`` (~6 months),
        or ``"long_term"`` (several years).
    limit:
        Number of tracks to return (1–50).
    """
    sp = sp or get_client(user_auth=True)
    result = sp.current_user_top_tracks(limit=limit, time_range=time_range)
    return result["items"]


def fetch_recently_played(
    *,
    sp: spotipy.Spotify | None = None,
    limit: int = 50,
) -> list[dict]:
    """Return the authenticated user's recently played tracks.

    Each item is a Spotify ``PlayHistoryObject`` containing ``track``,
    ``played_at``, and ``context`` fields.

    Parameters
    ----------
    limit:
        Number of items to return (1–50).
    """
    sp = sp or get_client(user_auth=True)
    result = sp.current_user_recently_played(limit=limit)
    return result["items"]


# ---------------------------------------------------------------------------
# Playlist mutation endpoints  (require OAuth / user_auth=True)
# ---------------------------------------------------------------------------


def remove_playlist_tracks(
    playlist_id: str,
    uris: list[str],
    *,
    sp: spotipy.Spotify | None = None,
) -> None:
    """Remove **all occurrences** of the given track URIs from a playlist.

    The API accepts at most 100 URIs per request; larger lists are chunked
    automatically.

    Parameters
    ----------
    playlist_id:
        Playlist ID, URI, or URL.
    uris:
        List of Spotify track URIs to remove (e.g. ``["spotify:track:…"]``).
    """
    sp = sp or get_client(user_auth=True)
    for i in range(0, len(uris), 100):
        sp.playlist_remove_all_occurrences_of_items(playlist_id, uris[i : i + 100])


def add_playlist_tracks(
    playlist_id: str,
    uris: list[str],
    *,
    sp: spotipy.Spotify | None = None,
    position: int | None = None,
) -> None:
    """Append track URIs to a playlist.

    The API accepts at most 100 URIs per request; larger lists are chunked
    automatically.

    Parameters
    ----------
    playlist_id:
        Playlist ID, URI, or URL.
    uris:
        List of Spotify track URIs to add.
    position:
        Zero-based index at which to insert the tracks.  Appends to the end
        when ``None``.
    """
    sp = sp or get_client(user_auth=True)
    for i in range(0, len(uris), 100):
        sp.playlist_add_items(playlist_id, uris[i : i + 100], position=position)


# ---------------------------------------------------------------------------
# Track endpoints
# ---------------------------------------------------------------------------


def fetch_track_by_id(track_id: str, *, sp: spotipy.Spotify | None = None) -> dict:
    """Return full track metadata for *track_id*.

    Parameters
    ----------
    track_id:
        Spotify track ID, URI, or URL.
    """
    sp = sp or get_client()
    return sp.track(track_id)


def fetch_tracks_by_ids(
    track_ids: list[str],
    *,
    sp: spotipy.Spotify | None = None,
    market: str | None = None,
) -> list[dict]:
    """Return track metadata for up to 50 track IDs in a single request.

    For larger batches the list is automatically chunked into groups of 50.

    Parameters
    ----------
    track_ids:
        List of Spotify track IDs, URIs, or URLs.
    market:
        ISO 3166-1 alpha-2 country code for track relinking.
    """
    sp = sp or get_client()
    kwargs: dict = {}
    if market:
        kwargs["market"] = market

    tracks: list[dict] = []
    for i in range(0, len(track_ids), 50):
        chunk = track_ids[i : i + 50]
        result = sp.tracks(chunk, **kwargs)
        tracks.extend(result["tracks"])
    return tracks
