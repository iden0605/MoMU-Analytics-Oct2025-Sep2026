"""Render index.html from summary.json.

The report is a single self-contained file: the summary data is inlined so it
opens straight from disk as well as from GitHub Pages. Re-run after process.py.

Run:  python3 scripts/build_html.py
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = json.load(open(os.path.join(ROOT, "data", "summary.json")))

MONTH_LABEL = {
    "2025-10": "Oct", "2025-11": "Nov", "2025-12": "Dec", "2026-01": "Jan",
    "2026-02": "Feb", "2026-03": "Mar", "2026-04": "Apr", "2026-05": "May",
    "2026-06": "Jun", "2026-07": "Jul", "2026-08": "Aug", "2026-09": "Sep",
}


def fdate(iso):
    y, m, d = iso.split("-")
    return f"{int(d)} {MONTH_LABEL[y + '-' + m]}"


h = S["headline"]
data_js = json.dumps(S, ensure_ascii=False)

HTML = f"""<!DOCTYPE html>
<html lang="en">

<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>MoMU Social Report 2025/26</title>
  <meta name="description" content="How the Malaysians of Melbourne University reels and posts performed from October 2025 to September 2026." />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link
    href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;0,6..72,700;1,6..72,400;1,6..72,500&family=Spline+Sans:wght@400;500;600&display=swap"
    rel="stylesheet" />
  <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
  <style>
    :root {{
      --paper: #f3ede0;
      --paper-raised: #fbf8f1;
      --paper-sunk: #ece4d3;
      --ink: #211c15;
      --ink-soft: #5f5647;
      --ink-faint: #8a8071;
      --rule: #d8cfbc;
      --rule-strong: #c3b8a0;
      --ochre: #a8551d;
      --ochre-soft: #c98a54;
      --slate: #3d5a63;
      --slate-soft: #7fa0a6;
      --good: #4a6b3f;
      --measure: 66ch;
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}

    html {{ -webkit-text-size-adjust: 100%; overflow-x: hidden; }}
    body {{ overflow-x: hidden; }}
    p {{ overflow-wrap: break-word; }}

    body {{
      background: var(--paper);
      color: var(--ink);
      font-family: "Spline Sans", system-ui, sans-serif;
      font-size: 1.0625rem;
      line-height: 1.68;
      -webkit-font-smoothing: antialiased;
      text-rendering: optimizeLegibility;
    }}

    ::selection {{ background: rgba(168, 85, 29, 0.22); color: var(--ink); }}

    a {{ color: var(--ochre); text-decoration-thickness: 1px; text-underline-offset: 2px; }}

    :focus-visible {{ outline: 2px solid var(--ochre); outline-offset: 3px; border-radius: 2px; }}

    ::-webkit-scrollbar {{ width: 11px; height: 11px; }}
    ::-webkit-scrollbar-track {{ background: var(--paper-sunk); }}
    ::-webkit-scrollbar-thumb {{ background: var(--rule-strong); border: 3px solid var(--paper-sunk); border-radius: 8px; }}
    * {{ scrollbar-color: var(--rule-strong) var(--paper-sunk); }}

    .wrap {{ max-width: 940px; margin: 0 auto; padding: 0 28px; }}

    /* ---- masthead ---- */
    .masthead {{
      border-bottom: 1px solid var(--rule);
      padding: 34px 0 26px;
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: baseline;
      gap: 6px 24px;
      font-size: 0.78rem;
      letter-spacing: 0.13em;
      text-transform: uppercase;
      color: var(--ink-soft);
    }}
    .masthead span:last-child {{ white-space: nowrap; }}
    .masthead b {{ color: var(--ink); font-weight: 600; }}

    .hero {{ padding: 92px 0 64px; border-bottom: 1px solid var(--rule); }}
    .hero h1 {{
      font-family: "Newsreader", Georgia, serif;
      font-weight: 600;
      font-size: clamp(3rem, 9vw, 5.75rem);
      line-height: 0.98;
      letter-spacing: -0.025em;
      text-wrap: balance;
      margin-bottom: 30px;
    }}
    .hero h1 em {{ font-style: italic; font-weight: 500; color: var(--ochre); }}
    .hero .standfirst {{
      font-size: 1.3rem;
      line-height: 1.6;
      color: var(--ink-soft);
      max-width: 52ch;
      font-weight: 400;
    }}
    .hero .meta {{
      margin-top: 38px;
      display: flex;
      flex-wrap: wrap;
      gap: 10px 34px;
      font-size: 0.9rem;
      letter-spacing: 0.04em;
      color: var(--ink-faint);
    }}
    .hero .meta b {{ color: var(--ink); font-weight: 600; font-variant-numeric: tabular-nums; }}

    /* ---- sections ---- */
    section {{ padding: 66px 0; border-bottom: 1px solid var(--rule); }}
    section:last-of-type {{ border-bottom: none; }}

    h2 {{
      font-family: "Newsreader", Georgia, serif;
      font-weight: 600;
      font-size: clamp(1.85rem, 4.4vw, 2.7rem);
      line-height: 1.08;
      letter-spacing: -0.02em;
      text-wrap: balance;
      margin-bottom: 22px;
    }}

    h3 {{
      font-family: "Newsreader", Georgia, serif;
      font-weight: 600;
      font-size: 1.32rem;
      letter-spacing: -0.01em;
      margin-bottom: 8px;
    }}

    p {{ max-width: var(--measure); margin-bottom: 1.1rem; }}
    p:last-child {{ margin-bottom: 0; }}
    .lead {{ font-size: 1.16rem; color: var(--ink-soft); }}

    strong {{ font-weight: 600; }}
    .num {{ font-variant-numeric: tabular-nums; }}

    /* ---- the ledger (big numbers) ---- */
    .ledger {{ margin-top: 40px; border-top: 2px solid var(--ink); }}
    .ledger .row {{
      display: grid;
      grid-template-columns: minmax(0, 5.5rem) 1fr;
      gap: 8px 30px;
      align-items: baseline;
      padding: 20px 0;
      border-bottom: 1px solid var(--rule);
    }}
    .ledger .fig {{
      font-family: "Newsreader", Georgia, serif;
      font-weight: 600;
      font-size: clamp(2.1rem, 5.5vw, 3rem);
      line-height: 1;
      letter-spacing: -0.03em;
      font-variant-numeric: tabular-nums;
      color: var(--ink);
      white-space: nowrap;
    }}
    .ledger .fig .unit {{ font-size: 0.9rem; letter-spacing: 0; color: var(--ink-faint); margin-left: 4px; }}
    .ledger .say {{ color: var(--ink-soft); font-size: 1rem; align-self: center; }}
    .ledger .say b {{ color: var(--ink); }}

    /* ---- figure / chart ---- */
    figure {{ margin: 40px 0 0; }}
    .figure-head {{ margin-bottom: 18px; }}
    .figure-head .cap {{
      font-family: "Newsreader", Georgia, serif;
      font-weight: 600;
      font-size: 1.12rem;
      letter-spacing: -0.01em;
    }}
    .figure-head .sub {{ font-size: 0.9rem; color: var(--ink-faint); margin-top: 2px; }}
    .plot {{
      background: var(--paper-raised);
      border: 1px solid var(--rule);
      border-radius: 3px;
      padding: 22px 20px 16px;
    }}
    .plot.tall {{ position: relative; height: 400px; }}
    .plot.mid {{ position: relative; height: 320px; }}

    figcaption {{
      margin-top: 16px;
      padding-left: 18px;
      border-left: 2px solid var(--ochre);
      font-size: 0.98rem;
      color: var(--ink-soft);
      max-width: var(--measure);
    }}
    figcaption b {{ color: var(--ink); }}

    /* ---- spotlight ---- */
    .spotlight {{ margin-top: 40px; display: grid; gap: 1px; background: var(--rule); border: 1px solid var(--rule); border-radius: 3px; overflow: hidden; }}
    @media (min-width: 720px) {{ .spotlight {{ grid-template-columns: 1fr 1fr; }} }}
    .spotlight article {{ background: var(--paper-raised); padding: 30px 28px; }}
    .spotlight .when {{ font-size: 0.82rem; letter-spacing: 0.12em; text-transform: uppercase; color: var(--ochre); margin-bottom: 12px; }}
    .spotlight .quote {{ color: var(--ink-soft); font-size: 0.98rem; margin-bottom: 20px; }}
    .spotlight dl {{ display: flex; flex-wrap: wrap; gap: 22px 30px; }}
    .spotlight dt {{ font-size: 0.78rem; letter-spacing: 0.08em; text-transform: uppercase; color: var(--ink-faint); }}
    .spotlight dd {{
      font-family: "Newsreader", Georgia, serif;
      font-weight: 600;
      font-size: 1.7rem;
      line-height: 1.1;
      font-variant-numeric: tabular-nums;
      margin-top: 2px;
    }}

    /* ---- action plan ---- */
    .plan {{ margin-top: 36px; counter-reset: step; }}
    .plan li {{
      list-style: none;
      counter-increment: step;
      display: grid;
      grid-template-columns: 2.4rem 1fr;
      gap: 4px 22px;
      padding: 24px 0;
      border-bottom: 1px solid var(--rule);
    }}
    .plan li:first-child {{ border-top: 2px solid var(--ink); }}
    .plan li::before {{
      content: counter(step);
      font-family: "Newsreader", Georgia, serif;
      font-weight: 600;
      font-size: 1.5rem;
      color: var(--ochre);
      line-height: 1;
    }}
    .plan .body {{ color: var(--ink-soft); }}
    .plan .body p {{ margin: 0; }}

    /* ---- close ---- */
    .close {{ padding: 76px 0 60px; }}
    .close h2 {{ font-size: clamp(2rem, 5vw, 3rem); }}
    .close p {{ font-size: 1.16rem; color: var(--ink-soft); }}

    footer {{
      border-top: 1px solid var(--rule);
      padding: 34px 0 60px;
      font-size: 0.85rem;
      color: var(--ink-faint);
    }}
    footer p {{ max-width: var(--measure); margin-bottom: 0.6rem; }}

    .anno-dot {{ display: inline-block; width: 9px; height: 9px; border-radius: 50%; background: var(--ochre); vertical-align: middle; margin: 0 6px 2px; }}

    @media (max-width: 620px) {{
      body {{ font-size: 1rem; }}
      .wrap {{ padding: 0 20px; }}
      .hero {{ padding: 60px 0 46px; }}
      section {{ padding: 50px 0; }}
      .ledger .row {{ grid-template-columns: 1fr; gap: 4px; padding: 18px 0; }}
      .plot.tall {{ height: 340px; }}
      .plan li {{ grid-template-columns: 1fr; gap: 8px; }}
      .plan li::before {{ font-size: 1.25rem; }}
    }}

    @media (prefers-reduced-motion: no-preference) {{
      .reveal {{ opacity: 0; transform: translateY(14px); }}
      .reveal.in {{ opacity: 1; transform: none; transition: opacity 0.7s cubic-bezier(0.16, 1, 0.3, 1), transform 0.7s cubic-bezier(0.16, 1, 0.3, 1); }}
    }}
  </style>
</head>

<body>
  <div class="wrap">

    <div class="masthead">
      <span>MoMU <b>&middot;</b> Malaysians of Melbourne University</span>
      <span>Social Report <b>2025 / 26</b></span>
    </div>

    <header class="hero">
      <h1>The year in <em>reels</em> and posts</h1>
      <p class="standfirst">Everything we put on Instagram from October 2025 to September 2026, and what the numbers show.</p>
      <div class="meta">
        <span><b class="num">{h['reels']}</b> reels</span>
        <span><b class="num">{h['posts']}</b> posts</span>
        <span><b>{fdate(h['first'])}</b> to <b>{fdate(h['last'])}</b></span>
      </div>
    </header>

    <section>
      <h2>The big numbers</h2>
      <div class="ledger">
        <div class="row">
          <div class="fig num">{round(h['total_reel_views'] / 1000)}<span class="unit">k</span></div>
          <div class="say">Total <b>reel views</b> for the year. That works out to about <b class="num">{h['avg_reel_views']:,}</b> a reel.</div>
        </div>
        <div class="row">
          <div class="fig num">{h['total_interactions'] / 1000:.1f}<span class="unit">k</span></div>
          <div class="say"><b>Likes and comments</b> across everything we posted. Reels get around <b class="num">18</b> comments each.</div>
        </div>
        <div class="row">
          <div class="fig num">{h['avg_engagement_rate'] * 100:.1f}<span class="unit">%</span></div>
          <div class="say">Of the people who watch a reel, this many <b>like or comment</b>. It has stayed about the same all year.</div>
        </div>
        <div class="row">
          <div class="fig num">18.7<span class="unit">k</span></div>
          <div class="say">Views on our <b>best reel</b>, from 11 August. The 23 January one was almost level with it.</div>
        </div>
      </div>
    </section>

    <section>
      <h2>How the reels did</h2>
      <p>Reels get seen far more than posts do. Each bar is one reel, in the order we posted them. The three biggest are marked in <span class="anno-dot"></span> ochre.</p>
      <figure>
        <div class="figure-head">
          <div class="cap">Views per reel, October 2025 to September 2026</div>
          <div class="sub">88 reels, oldest on the left</div>
        </div>
        <div class="plot tall"><canvas id="reelViews"></canvas></div>
        <figcaption>We started the year well, with reels in October and November often getting <b>8,000 to 14,000 views</b>. Over autumn and winter that dropped to more like <b>4,000 to 5,000</b>, then picked back up in August. Two reels did much better than everything else, one in January and one in August.</figcaption>
      </figure>
    </section>

    <section>
      <h2>Did posting more often help</h2>
      <p>We posted a lot more in some months than others, it did not make a big difference.</p>
      <figure>
        <div class="figure-head">
          <div class="cap">Reels posted per month against average views</div>
          <div class="sub">bars are the count, the line is average views that month</div>
        </div>
        <div class="plot mid"><canvas id="cadence"></canvas></div>
        <figcaption>April to June was our busiest run, <b>29 reels</b> in three months, and also our worst, averaging about <b>5,400 views</b>. The quieter months from October to January averaged closer to <b>7,700</b>. Posting more often just meant each reel got seen less. Over the year we did <b>about two reels a week</b>, and six in our busiest week.</figcaption>
      </figure>
    </section>

    <section>
      <h2>The two great posts</h2>
      <div class="spotlight">
        <article>
          <div class="when">Posted 11 August 2026</div>
          <h3>The student visa Q and A reel</h3>
          <p class="quote">"Your future in Australia starts here. Got questions about visas, work, study or staying post-grad?"</p>
          <dl>
            <div><dt>Views</dt><dd class="num">18,710</dd></div>
            <div><dt>Likes</dt><dd class="num">213</dd></div>
            <div><dt>Comments</dt><dd class="num">14</dd></div>
          </dl>
        </article>
        <article>
          <div class="when">Posted 23 January 2026</div>
          <h3>The "they made a reel" reel</h3>
          <p class="quote">"They made a reel. #unimelb #student #relatable #momuians"</p>
          <dl>
            <div><dt>Views</dt><dd class="num">18,372</dd></div>
            <div><dt>Likes</dt><dd class="num">271</dd></div>
            <div><dt>Comments</dt><dd class="num">11</dd></div>
          </dl>
        </article>
      </div>
    </section>

    <section>
      <h2>How the posts did</h2>
      <p>Posts get seen by fewer people than reels.</p>
      <figure>
        <div class="figure-head">
          <div class="cap">Likes per post</div>
          <div class="sub">46 posts, oldest on the left</div>
        </div>
        <div class="plot mid"><canvas id="postLikes"></canvas></div>
        <figcaption>Most posts sit between <b>50 and 150 likes</b>. The one that stood out was the 14 August carousel about finding pieces of Malaysia around Melbourne, at <b>779 likes</b>. The 25/26 committee reveal in May came next at <b>388</b>.</figcaption>
      </figure>
      <figure>
        <div class="figure-head">
          <div class="cap">Carousels against single images</div>
          <div class="sub">average likes per post</div>
        </div>
        <div class="plot mid"><canvas id="format"></canvas></div>
        <figcaption>Carousels got <b>more than double</b> the likes of single images, {S['format_split']['carousel']['avg_likes']} against {S['format_split']['single']['avg_likes']} on average. They are worth the extra effort.</figcaption>
      </figure>
    </section>

    <section>
      <h2>Does the day matter</h2>
      <p>Average reel views by the day of the week we posted. Some days only have a few reels behind them, so this is rough.</p>
      <figure>
        <div class="figure-head">
          <div class="cap">Average reel views by day of week</div>
          <div class="sub">number of reels shown on each bar</div>
        </div>
        <div class="plot mid"><canvas id="dow"></canvas></div>
        <figcaption><b>Tuesday</b> is highest, with Wednesday to Friday close behind. <b>Monday</b> is lowest and weekends sit in the middle. Midweek does a bit better, but not by much.</figcaption>
      </figure>
    </section>

    <section>
      <h2>What to try next</h2>
      <ol class="plan">
        <li><div class="body"><h3>Post fewer reels and put more into each one</h3><p>Our busiest months were our worst ones. Two or three good reels a week beats one every other day. Give each one a few days before the next goes up.</p></div></li>
        <li><div class="body"><h3>Keep reels quick and simple</h3><p>Both of our best reels were short and funny. It is the same story all year. Committee members just being themselves on camera does better than anything that looks staged.</p></div></li>
        <li><div class="body"><h3>Use carousels for posts</h3><p>They get more than double the likes of a single photo. Recaps, guides and reveals all work well as a swipe. Use one whenever there is more than one thing to show.</p></div></li>
        <li><div class="body"><h3>Aim for midweek</h3><p>Tuesday to Friday has done better than Monday or the weekend. Not a strict rule, but worth leaning that way when we can.</p></div></li>
        <li><div class="body"><h3>Ask people to follow, in the reel</h3><p>Lots of people who see our reels do not follow us. A simple "follow @momuians for more" on screen and in the caption is free and it helps.</p></div></li>
      </ol>
    </section>

    <footer>
      <p>Pulled from the public @momuians profile and reels tab on 7 September 2026. Reel view counts are from Instagram directly. Likes and comments are from that date and will have gone up a little since. Posting times are rounded by Instagram, so the day of the week can be off by a few hours around midnight.</p>
      <p>Not in here: reach, impressions, profile visits, link taps, follower splits and follows. Instagram no longer shows these publicly, they are only in the account's own insights.</p>
      <p>MoMU, October 2025 to September 2026.</p>
    </footer>

  </div>

  <script id="report-data" type="application/json">{data_js}</script>
  <script>
    const D = JSON.parse(document.getElementById('report-data').textContent);
    const ML = {{ '2025-10': 'Oct', '2025-11': 'Nov', '2025-12': 'Dec', '2026-01': 'Jan', '2026-02': 'Feb', '2026-03': 'Mar', '2026-04': 'Apr', '2026-05': 'May', '2026-06': 'Jun', '2026-07': 'Jul', '2026-08': 'Aug', '2026-09': 'Sep' }};
    const shortDate = iso => {{ const [y, m, d] = iso.split('-'); return (+d) + ' ' + ML[y + '-' + m]; }};

    const ink = '#211c15', inkSoft = '#5f5647', inkFaint = '#8a8071';
    const ochre = '#a8551d', ochreSoft = 'rgba(168,85,29,0.16)';
    const slate = '#3d5a63', slateSoft = 'rgba(61,90,99,0.14)';
    const rule = 'rgba(33,28,21,0.10)';

    Chart.defaults.font.family = "'Spline Sans', system-ui, sans-serif";
    Chart.defaults.font.size = 12;
    Chart.defaults.color = inkFaint;

    const tip = {{
      backgroundColor: '#fbf8f1', borderColor: '#c3b8a0', borderWidth: 1,
      titleColor: ink, bodyColor: inkSoft, padding: 12, cornerRadius: 3,
      displayColors: false, titleFont: {{ weight: '600' }},
    }};
    const xAxis = extra => Object.assign({{ grid: {{ display: false }}, border: {{ color: rule }}, ticks: {{ color: inkFaint, maxRotation: 0, autoSkipPadding: 16 }} }}, extra || {{}});
    const yAxis = extra => Object.assign({{ grid: {{ color: rule }}, border: {{ display: false }}, ticks: {{ color: inkFaint, padding: 8 }} }}, extra || {{}});

    // --- reel views ---
    const rt = D.reels_timeline;
    const rvMax = Math.max(...rt.map(r => r.views));
    new Chart(document.getElementById('reelViews'), {{
      type: 'bar',
      data: {{
        labels: rt.map(r => shortDate(r.date)),
        datasets: [{{
          data: rt.map(r => r.views),
          backgroundColor: rt.map(r => r.views >= 14000 ? ochre : ochreSoft),
          borderColor: rt.map(r => r.views >= 14000 ? ochre : 'rgba(168,85,29,0.32)'),
          borderWidth: 1, borderRadius: 2, borderSkipped: false,
          hoverBackgroundColor: ochre,
          categoryPercentage: 0.98, barPercentage: 0.92,
        }}],
      }},
      options: {{
        maintainAspectRatio: false, responsive: true,
        plugins: {{ legend: {{ display: false }}, tooltip: {{ ...tip, callbacks: {{ title: c => 'Reel, ' + c[0].label, label: c => c.raw.toLocaleString() + ' views' }} }} }},
        scales: {{ x: xAxis({{ ticks: {{ color: inkFaint, maxRotation: 0, autoSkip: true, autoSkipPadding: 24 }} }}), y: yAxis({{ suggestedMax: Math.ceil(rvMax / 5000) * 5000, ticks: {{ color: inkFaint, padding: 8, callback: v => v >= 1000 ? v / 1000 + 'k' : v }} }}) }},
      }},
    }});

    // --- cadence vs avg views ---
    const bm = D.by_month;
    new Chart(document.getElementById('cadence'), {{
      data: {{
        labels: bm.map(m => ML[m.month]),
        datasets: [
          {{ type: 'bar', label: 'Reels posted', data: bm.map(m => m.reels), backgroundColor: slateSoft, borderColor: slate, borderWidth: 1, borderRadius: 2, borderSkipped: false, yAxisID: 'y', order: 2 }},
          {{ type: 'line', label: 'Avg views', data: bm.map(m => m.avg_reel_views), borderColor: ochre, backgroundColor: ochre, borderWidth: 2, pointRadius: 3, pointHoverRadius: 5, tension: 0.3, yAxisID: 'y1', order: 1 }},
        ],
      }},
      options: {{
        maintainAspectRatio: false, responsive: true,
        layout: {{ padding: {{ top: 10 }} }},
        interaction: {{ mode: 'index', intersect: false }},
        plugins: {{
          legend: {{ position: 'top', align: 'end', labels: {{ color: inkSoft, boxWidth: 10, boxHeight: 10, usePointStyle: true, pointStyle: 'rectRounded', padding: 16 }} }},
          tooltip: {{ ...tip, displayColors: true, callbacks: {{ label: c => c.dataset.label + ': ' + c.raw.toLocaleString() + (c.dataset.yAxisID === 'y1' ? ' views' : '') }} }},
        }},
        scales: {{
          x: xAxis(),
          y: yAxis({{ position: 'left', ticks: {{ color: inkFaint, padding: 8, precision: 0 }} }}),
          y1: {{ position: 'right', grid: {{ display: false }}, border: {{ display: false }}, ticks: {{ color: inkFaint, padding: 8, callback: v => v >= 1000 ? v / 1000 + 'k' : v }} }},
        }},
      }},
    }});

    // --- post likes ---
    const pt = D.posts_timeline;
    new Chart(document.getElementById('postLikes'), {{
      type: 'bar',
      data: {{
        labels: pt.map(p => shortDate(p.date)),
        datasets: [{{
          data: pt.map(p => p.likes),
          backgroundColor: pt.map(p => p.likes >= 300 ? slate : slateSoft),
          borderColor: pt.map(p => p.likes >= 300 ? slate : 'rgba(61,90,99,0.3)'),
          borderWidth: 1, borderRadius: 2, borderSkipped: false, hoverBackgroundColor: slate,
          categoryPercentage: 0.96, barPercentage: 0.86,
        }}],
      }},
      options: {{
        maintainAspectRatio: false, responsive: true,
        plugins: {{ legend: {{ display: false }}, tooltip: {{ ...tip, callbacks: {{ label: c => c.raw.toLocaleString() + ' likes' }} }} }},
        scales: {{ x: xAxis({{ ticks: {{ color: inkFaint, maxRotation: 0, autoSkip: true, autoSkipPadding: 20 }} }}), y: yAxis({{ ticks: {{ color: inkFaint, padding: 8 }} }}) }},
      }},
    }});

    // --- format split ---
    const fs = D.format_split;
    new Chart(document.getElementById('format'), {{
      type: 'bar',
      data: {{
        labels: ['Carousel  (' + fs.carousel.n + ')', 'Single image  (' + fs.single.n + ')'],
        datasets: [{{
          data: [fs.carousel.avg_likes, fs.single.avg_likes],
          backgroundColor: [ochre, slateSoft],
          borderColor: [ochre, slate], borderWidth: 1, borderRadius: 2, borderSkipped: false,
          barPercentage: 0.6,
        }}],
      }},
      options: {{
        indexAxis: 'y', maintainAspectRatio: false, responsive: true,
        plugins: {{ legend: {{ display: false }}, tooltip: {{ ...tip, callbacks: {{ label: c => c.raw + ' likes on average' }} }} }},
        scales: {{ x: yAxis({{ ticks: {{ color: inkFaint, padding: 8 }} }}), y: xAxis({{ ticks: {{ color: ink, font: {{ size: 13 }} }} }}) }},
      }},
    }});

    // --- day of week ---
    const dw = D.day_of_week;
    const dwMax = Math.max(...dw.map(d => d.avg_views));
    new Chart(document.getElementById('dow'), {{
      type: 'bar',
      data: {{
        labels: dw.map(d => d.day.slice(0, 3)),
        datasets: [{{
          data: dw.map(d => d.avg_views),
          backgroundColor: dw.map(d => d.avg_views === dwMax ? ochre : ochreSoft),
          borderColor: dw.map(d => d.avg_views === dwMax ? ochre : 'rgba(168,85,29,0.32)'),
          borderWidth: 1, borderRadius: 2, borderSkipped: false, hoverBackgroundColor: ochre,
        }}],
      }},
      options: {{
        maintainAspectRatio: false, responsive: true,
        plugins: {{
          legend: {{ display: false }},
          tooltip: {{ ...tip, callbacks: {{ title: c => dw[c[0].dataIndex].day, label: c => c.raw.toLocaleString() + ' avg views', afterLabel: c => 'from ' + dw[c.dataIndex].n + ' reels' }} }},
        }},
        scales: {{ x: xAxis({{ ticks: {{ color: inkFaint }} }}), y: yAxis({{ ticks: {{ color: inkFaint, padding: 8, callback: v => v >= 1000 ? v / 1000 + 'k' : v }} }}) }},
      }},
    }});

    // --- one authored reveal ---
    if (matchMedia('(prefers-reduced-motion: no-preference)').matches) {{
      const io = new IntersectionObserver((es) => {{
        es.forEach(e => {{ if (e.isIntersecting) {{ e.target.classList.add('in'); io.unobserve(e.target); }} }});
      }}, {{ rootMargin: '0px 0px -12% 0px' }});
      document.querySelectorAll('section, .close').forEach(el => {{ el.classList.add('reveal'); io.observe(el); }});
    }}
  </script>
</body>

</html>
"""

with open(os.path.join(ROOT, "index.html"), "w") as f:
    f.write(HTML)
print("wrote index.html", len(HTML), "bytes")
