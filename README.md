# Podcast playlist

This keeps a Spotify playlist of podcast episodes up to date automatically.

I follow a handful of podcasts, and keeping up with them on Spotify was a chore. New episodes are scattered across different show pages, the ones I'd already listened to hung around, and older ones I never got to built up over time. I wanted one playlist I could open each morning that just had what was new.

So every morning this script goes through the shows I follow and adds anything released in the last couple of days to the top of the playlist. It also takes off episodes I've finished, and anything I haven't played after two weeks. If I remove an episode myself, it stays gone.

It runs on a schedule with GitHub Actions, so it doesn't need my laptop to be on.

## Files

- `daily_ai_playlist.py` is the script that updates the playlist.
- `config.json` has the playlist and the shows to follow.
- `state.json` keeps track of what's already been added, and is saved back to the repo after each run.
- `.github/workflows/daily.yml` runs it every morning.

Spotify login details are kept in GitHub secrets, not in the code.
