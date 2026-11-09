#!/usr/bin/env python3
"""Keep a Spotify playlist filled with new episodes from your chosen podcasts.

Each run:
  1. Removes episodes you've listened to: marked fully played, or stopped
     within DONE_WITHIN_SECONDS of the end.
  2. Removes episodes older than MAX_AGE_DAYS that you never got round to.
  3. Adds new episodes (released in the last LOOKBACK_DAYS) to the top, so the
     playlist is always ordered most recently added first.

Anything you remove by hand is remembered in state.json and never re-added.

Usage:
  python daily_ai_playlist.py setup   # first time: log in, find the playlist and shows
  python daily_ai_playlist.py token   # print the refresh token for GitHub secrets
  python daily_ai_playlist.py         # the daily run (what the scheduler calls)
  python daily_ai_playlist.py --dry-run

Credentials come from the environment (never commit them):
  SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, and on GitHub SPOTIFY_REFRESH_TOKEN
"""
import datetime as dt
import json
import os
import sys
from pathlib import Path

import spotipy
from spotipy.oauth2 import SpotifyOAuth

# ---------- settings you might change ----------
PLAYLIST_NAME = "daily ai"
SHOWS = [  # searched by name during `setup`; check the matches it prints
    "The AI Daily Brief",
    "Tech Brew Ride Home",
    "TLDR AI",
    "The Rundown",
    "FT News Briefing",
    "TBPN",
    "Hard Fork",
    "No Priors",
    "Latent Space",
]
MARKET = "GB"
LOOKBACK_DAYS = 2    # only add episodes released this recently
MAX_AGE_DAYS = 14    # drop unplayed episodes older than this (0 = never)
DONE_WITHIN_SECONDS = 120  # stopped this close to the end counts as listened
# -----------------------------------------------

HERE = Path(__file__).resolve().parent
CONFIG = HERE / "config.json"   # playlist id + show ids (written by setup)
STATE = HERE / "state.json"     # every episode ever added, so removals stick
SCOPES = ("playlist-read-private playlist-modify-private "
          "playlist-modify-public user-read-playback-position")


TOKEN = HERE / ".spotify_token"


def client():
    # On GitHub Actions there is no browser: seed the token cache from a secret
    refresh = os.environ.get("SPOTIFY_REFRESH_TOKEN")
    if refresh and not TOKEN.exists():
        TOKEN.write_text(json.dumps({"access_token": "", "token_type": "Bearer",
                                     "expires_at": 0, "scope": SCOPES,
                                     "refresh_token": refresh}))
    auth = SpotifyOAuth(scope=SCOPES,
                        redirect_uri="http://127.0.0.1:8888/callback",
                        cache_path=str(TOKEN),
                        open_browser=not refresh)
    return spotipy.Spotify(auth_manager=auth)


def listened(ep):
    rp = ep.get("resume_point") or {}
    if rp.get("fully_played"):
        return True
    pos, length = rp.get("resume_position_ms") or 0, ep.get("duration_ms") or 0
    return pos > 0 and length - pos <= DONE_WITHIN_SECONDS * 1000


def load(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def save(path, data):
    path.write_text(json.dumps(data, indent=2))


def parse_date(s):
    # release_date can be "2026-11-05", "2026-11" or "2026"
    parts = (s.split("-") + ["1", "1"])[:3]
    return dt.date(*map(int, parts))


def paged(sp, page):
    while page:
        yield from page["items"]
        page = sp.next(page) if page.get("next") else None


# ---------------- setup ----------------
def setup(sp):
    playlist = next((p for p in paged(sp, sp.current_user_playlists(limit=50))
                     if p and p["name"].lower() == PLAYLIST_NAME.lower()), None)
    if not playlist:
        # POST /me/playlists: Spotify blocks /users/{id}/playlists for newer apps
        playlist = sp.current_user_playlist_create(
            PLAYLIST_NAME, public=False,
            description="New AI podcast episodes, auto-refreshed daily")
        print(f"Created playlist '{PLAYLIST_NAME}'")
    print(f"Playlist: {playlist['name']}  {playlist['external_urls']['spotify']}\n")

    shows = {}
    for name in SHOWS:
        hits = sp.search(q=name, type="show", market=MARKET, limit=1)["shows"]["items"]
        hit = hits[0] if hits else None
        if not hit:
            print(f"  NOT FOUND: {name}")
            continue
        shows[hit["id"]] = hit["name"]
        publisher = hit.get("publisher") or "publisher not shown"
        print(f"  {name!r:28} -> {hit['name']} ({publisher})")
    save(CONFIG, {"playlist_id": playlist["id"], "shows": shows})
    print(f"\nSaved {CONFIG.name}. If a match is wrong, replace its id with the one "
          "from the show's Share > Copy link (open.spotify.com/show/<id>).")


# ---------------- daily run ----------------
def run(sp, dry_run=False, today=None):
    cfg = load(CONFIG, None)
    if not cfg:
        sys.exit("No config.json yet - run `python daily_ai_playlist.py setup` first.")
    state = load(STATE, {"added": {}})
    today = today or dt.date.today()
    pid = cfg["playlist_id"]

    # 1 & 2: clean out finished and stale episodes
    items = sp.playlist_items(pid, additional_types=("episode",), market=MARKET)
    in_playlist = []
    for it in paged(sp, items):
        obj = it.get("track") or it.get("item")
        if obj and obj.get("type") == "episode":
            in_playlist.append(obj["id"])

    remove = []
    for i in range(0, len(in_playlist), 50):
        for ep in sp.episodes(in_playlist[i:i + 50], market=MARKET)["episodes"]:
            if not ep:
                continue
            age = (today - parse_date(ep["release_date"])).days
            if listened(ep) or (MAX_AGE_DAYS and age > MAX_AGE_DAYS):
                remove.append(ep)
    if remove:
        print("Removing:", *[f"  - {e['name']}" for e in remove], sep="\n")
        if not dry_run:
            uris = [e["uri"] for e in remove]
            for i in range(0, len(uris), 100):
                sp.playlist_remove_all_occurrences_of_items(pid, uris[i:i + 100])

    # 3: add new episodes not seen before
    cutoff = today - dt.timedelta(days=LOOKBACK_DAYS)
    new = []
    for show_id, show_name in cfg["shows"].items():
        for ep in sp.show_episodes(show_id, limit=5, market=MARKET)["items"]:
            if not ep or ep["id"] in state["added"]:
                continue
            if parse_date(ep["release_date"]) >= cutoff:
                new.append((ep["release_date"], show_name, ep))
    new.sort(key=lambda x: x[0], reverse=True)  # newest first
    if new:
        print("Adding:", *[f"  + [{s}] {e['name']}" for _, s, e in new], sep="\n")
        if not dry_run:
            sp.playlist_add_items(pid, [e["uri"] for _, _, e in new], position=0)
            for _, _, e in new:
                state["added"][e["id"]] = today.isoformat()

    if not remove and not new:
        print("Nothing to change.")

    # forget episodes added long ago, to keep state.json small
    keep_from = (today - dt.timedelta(days=60)).isoformat()
    state["added"] = {k: v for k, v in state["added"].items() if v >= keep_from}
    if not dry_run:
        save(STATE, state)


if __name__ == "__main__":
    sp = client()
    if "setup" in sys.argv:
        setup(sp)
    elif "token" in sys.argv:
        sp.current_user()  # makes sure the token is fresh
        print(json.loads(TOKEN.read_text())["refresh_token"])
    else:
        run(sp, dry_run="--dry-run" in sys.argv)
