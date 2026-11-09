# Daily AI playlist

Keeps your Spotify playlist "daily ai" stocked with new podcast episodes. It runs every morning on GitHub, so your laptop doesn't need to be on. Each run:

- **Adds** episodes released in the last 2 days, at the top. The playlist is always ordered most recently added first.
- **Removes** episodes you've listened to: either marked played, or stopped within 2 minutes of the end.
- **Removes** unplayed episodes once they're 14 days old.

Anything you remove by hand stays removed.

## 1. Create a Spotify app (once)

Go to https://developer.spotify.com/dashboard and click **Create app**. Add this Redirect URI: `http://127.0.0.1:8888/callback`. Then copy the **Client ID** and **Client secret**.

## 2. Run setup on your Mac (once)

```bash
cd ~/spotify-daily-ai                      # wherever you saved this folder
python3 -m venv .venv && .venv/bin/pip install spotipy
export SPOTIPY_CLIENT_ID=paste_id SPOTIPY_CLIENT_SECRET=paste_secret
.venv/bin/python daily_ai_playlist.py setup      # browser opens: log in to Spotify
.venv/bin/python daily_ai_playlist.py --dry-run  # shows what it would change
.venv/bin/python daily_ai_playlist.py token      # prints your refresh token: copy it
```

Setup prints the show it matched for each name. If one is wrong, open `config.json` and replace its id with the one from that show's **Share → Copy link** (the part after `/show/`).

## 3. Put it on your personal GitHub

Check which GitHub account the `gh` command is using first. You probably want your personal one, not the Electric Twin one:

```bash
gh auth status                  # if it shows your work account: gh auth login
git init && git add . && git status   # .spotify_token must NOT be in the list
git commit -m "Daily AI playlist"
gh repo create daily-ai-playlist --private --source=. --push
```

The repo can be public or private. Your Spotify keys live in GitHub secrets, which are never shown, even on a public repo. On a public repo, though, anyone can read the run logs and `state.json`, so they can see which episodes get added. Actions minutes are free on public repos. On a private repo the daily run uses about 1 minute of your 2,000 free monthly minutes.

## 4. Add the secrets

```bash
gh secret set SPOTIPY_CLIENT_ID          # paste each value when asked
gh secret set SPOTIPY_CLIENT_SECRET
gh secret set SPOTIFY_REFRESH_TOKEN      # the token from step 2
```

Or do it on github.com: repo → **Settings → Secrets and variables → Actions → New repository secret**.

## 5. Test it

```bash
gh workflow run daily.yml && gh run watch
```

Or go to the repo's **Actions** tab, open **Refresh daily ai playlist** and click **Run workflow**. After that it runs every day at 06:17 UTC on its own. GitHub can start scheduled runs a little late.

## Changing it

- **Settings:** `LOOKBACK_DAYS`, `MAX_AGE_DAYS` and `DONE_WITHIN_SECONDS` are at the top of `daily_ai_playlist.py`.
- **Shows:** edit `config.json`, then commit and push.
- **If runs start failing with an auth error:** run `token` on your Mac again and update the `SPOTIFY_REFRESH_TOKEN` secret.

`state.json` is how it remembers what it has already added. The workflow saves it back to the repo after each run.
