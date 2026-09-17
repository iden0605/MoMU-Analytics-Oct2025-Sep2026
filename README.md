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
| `data/prior-year/` | The same four files, for October 2024 to September 2025, used only for the "How this year compares" section. |
| `raw/` | The untouched scraper output, three runs. |
| `raw/prior-year/` | The HAR-derived scrape behind `data/prior-year/`. |
| `scripts/process.py` | Cleans and merges a `raw/` window into `data/`-shaped files. |
| `scripts/build_html.py` | Renders `index.html` from `summary.json`, and from `data/prior-year/summary.json` if it exists. |
| `scripts/parse_har.py` | Turns a DevTools network recording into a new `raw/` file. |

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

The "How this year compares" section pulls in the same twelve months a year
earlier, October 2024 to September 2025, gathered on 17 September 2026 by
recording Instagram's own network traffic rather than a console script — see
"Refreshing later" below for why and how. A handful of those reels came back
with no posting time, since the Reels tab doesn't send one; their dates are
estimated from where their post id falls among posts we do have a time for,
since Instagram hands out ids in posting order.

## Rebuilding

```
python3 scripts/process.py     # raw/ -> data/reels.json, data/posts.json, data/data.csv, data/summary.json
python3 scripts/build_html.py  # data/summary.json (+ data/prior-year/summary.json) -> index.html
```

## Refreshing later, or pulling a different year

Console scripts that call Instagram's API themselves no longer work: Instagram
answers `429 Too Many Requests` to anything fetched from the console and the
block does not clear, even while ordinary browsing is fine. The method below
instead records the requests Instagram's own page makes while you scroll, so
nothing unusual is sent.

Do it in Chrome, logged in to an account that admins @momuians.

**Record**

1. Open `instagram.com/momuians`. Wait for the grid of posts to appear.
2. Press `Option-Command-I` to open DevTools, then click the **Network** tab
   along the top of the DevTools panel.
3. Tick the checkbox labelled **Preserve log** (in the toolbar just under the
   tabs, next to "Disable cache"). Older Chrome calls this same checkbox
   **Keep log** — either way, tick it. This is what stops the recording being
   wiped when you move between tabs on the profile.
4. Click **Fetch/XHR** in the row of filter buttons below that. The list should
   start filling as you use the page.
5. Click the 🚫 "Clear" circle-with-a-slash button at the far left of the
   Network toolbar once, to start from an empty list.
6. Now scroll the profile grid slowly to the bottom, all the way past the
   oldest month you want. Scroll in bursts and pause a second or two; every
   pause lets Instagram load the next batch. Keep DevTools open the whole time.
7. When the grid stops loading anything new, click the profile's **REELS** tab
   and scroll that to the bottom the same way. Do not reload the page, do not
   close DevTools, and do not clear the list again — the grid requests must
   stay in the same recording.
8. Check before exporting: bottom-left of the Network panel shows a request
   count ("… requests"). After both tabs it should be well past 100 — the real
   run for the 2024/25 pull hit 517. If it is still under 50, you have not
   scrolled far enough — keep scrolling.
9. Export the recording: click the **download icon** in the Network toolbar
   (the down-arrow next to the up-arrow import icon, near "No throttling").
   That saves everything currently in the list as a HAR, bodies included, with
   no menu needed. (Right-clicking a single request only gives options for
   that one request — for "Save all as HAR" from the right-click menu instead,
   right-click the empty space below the last row, not a row itself.) It
   downloads as `www.instagram.com.har`.

**Convert and rebuild**

```
python3 scripts/parse_har.py grid-2024 ~/Downloads/www.instagram.com.har
```

This writes `raw/scrape_grid-2024.json` and prints what it found: the number
of posts and reels, how many belong to @momuians, and the date span. If most
of the media is not @momuians, DevTools recorded the home feed instead of the
profile — start again from step 1 on `instagram.com/momuians` itself, not
`instagram.com`.

Reels scrolled from the Reels tab come back with a view count but no posting
time (Instagram just doesn't send one on that query); `parse_har.py` estimates
it from the post's id, which Instagram hands out in posting order, calibrated
against every post in the same capture that does have a real timestamp. Watch
for the "estimated the date for N reels" line — if the estimated dates print
because the grid pass never covered the year you needed, scroll the grid
further and re-export.

`scripts/process.py` defaults to globbing `raw/*.json`, which would fold a
new capture straight into the current report's own numbers, so move it out of
`raw/`'s top level first — e.g. `mkdir raw/prior-year && mv raw/scrape_grid-2024.json raw/prior-year/`.
Then build that year's `data/` files explicitly, pointing `process.py` at just
that file and the window it covers:

```
python3 scripts/process.py --raw raw/prior-year/scrape_grid-2024.json \
    --start 2024-10-01 --end 2025-10-01 --out data/prior-year
python3 scripts/build_html.py
```

`build_html.py` picks up `data/prior-year/summary.json` automatically if it
exists and adds the "How this year compares" section; delete that folder (or
just don't create it) to build the report without a comparison.
