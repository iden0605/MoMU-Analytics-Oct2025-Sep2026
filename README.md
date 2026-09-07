# MoMU Instagram Analytics, October 2025 to September 2026

A single-page report on how the @momuians reels and posts performed over the
2025/26 term, in the same spirit as the January to March 2026 report.

## What is here

| File | What it is |
| --- | --- |
| `index.html` | The report. Self-contained, opens from disk or GitHub Pages. |
| `data/reels.json` | Every reel in the window, one object each. |
| `data/posts.json` | Every post in the window, one object each. |
| `data/data.csv` | Reels and posts together, one row each, for spreadsheets. |
| `data/summary.json` | Pre-computed aggregates that `build_html.py` bakes into `index.html`. |
| `raw/` | The untouched scraper output, three runs. |
| `scripts/process.py` | Cleans and merges `raw/` into the files above. |
| `scripts/build_html.py` | Renders `index.html` from `summary.json`. |

## How the data was gathered

Instagram removed public access to the insight metrics the previous report used
(reach, profile visits, link taps, follower splits, follows). Those only live in
the account's own insights now.

What is in here was pulled from the public @momuians profile and reels tab on
7 September 2026 using a browser-console script:

- Reels: view count, likes, comments, caption, timestamp.
- Posts: likes, comments, caption, timestamp. Instagram exposes no public view
  count for photos or carousels, so posts have no `views`.

The scrape also picked up a handful of recommended reels from other accounts.
`process.py` drops anything whose owner id is not `4730946554`, plus carousel
child frames, one sponsored object, and anything outside the date window. A few
reels came back with the play count sitting in the like field and no separate
view field; those are corrected in `process.py`.

## Rebuilding

```
python3 scripts/process.py     # raw/ -> data/reels.json, data/posts.json, data/data.csv, data/summary.json
python3 scripts/build_html.py  # data/summary.json -> index.html
```

## Refreshing later

Re-run the scraper (kept on the Desktop as `momu-instagram-scrape.js`), drop the
new JSON into `raw/`, and run both scripts. Widen the window in
`scripts/process.py` (`START`, `END`) if the date range changes.
