# Daily AI playlist

A small tool that keeps one Spotify playlist filled with fresh AI and tech podcast episodes, so there's always something new to listen to without hunting for it.

## The problem

Following ten or so daily and weekly podcasts on Spotify gets messy. New episodes are spread across different show pages. Ones you've already heard stay in your queue. Old ones you never got to pile up until the list is hard to use. Keeping a single "listen next" playlist tidy by hand takes a few minutes every day, and it's easy to let it slide.

## What it does

Every morning it tidies a Spotify playlist called **daily ai**:

- **Adds new episodes.** Anything released in the last two days from the shows it follows goes to the top, so the newest is always first.
- **Removes what you've finished.** Episodes you've marked as played, or stopped within the last couple of minutes, are taken off.
- **Clears out old episodes.** Anything still unplayed after two weeks is removed, so the list never gets stale.
- **Respects your edits.** If you remove an episode yourself, it won't come back.

It runs on GitHub on a daily schedule, so it works even when your laptop is off.

## Shows it follows

The AI Daily Brief, Tech Brew Ride Home, The Rundown, FT News Briefing, TBPN, Hard Fork, No Priors, Latent Space, Software Engineering Daily and TLDR AI.

The list lives in `config.json` and can be changed at any time.

## How it works

- `daily_ai_playlist.py` is the script. It talks to Spotify to check new releases and your listening progress, then updates the playlist.
- `config.json` lists the playlist and the shows to follow.
- `state.json` remembers which episodes have already been added. That's how it knows not to re-add ones you've removed. It saves itself back to the repo after each run.
- A GitHub Actions workflow runs the script every morning at 06:17 UTC.

Your Spotify login details are stored as GitHub secrets, so they never appear in the code or the run logs.
