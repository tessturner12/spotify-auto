# Daily playlist

Keeps a Spotify playlist of podcast episodes up to date automatically.

Following several podcasts on Spotify means checking each show for new episodes, and the queue fills up with episodes that have already been played or are too old to bother with. This replaces that with one playlist that is refreshed every morning.

Each day it adds episodes released in the last two days to the top of the playlist, removes episodes that have been played, and removes anything left unplayed for two weeks. Episodes removed by hand are not added back.

It runs on a schedule with GitHub Actions, so no computer needs to be on.

## Files

- `daily_playlist.py` updates the playlist.
- `config.json` sets the playlist and the shows to follow.
- `state.json` records which episodes have been added. It is saved back to the repo after each run.
- `.github/workflows/daily.yml` runs the script every morning.

Spotify credentials are stored as GitHub secrets, not in the code.
