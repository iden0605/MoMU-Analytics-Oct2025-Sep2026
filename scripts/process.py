"""Merge the raw Instagram scrapes into clean, analysis-ready files.

Reads every raw/*.json scrape, dedupes by media pk, drops carousel children,
sponsored ads and anything outside Oct 2025 - Sep 2026, then writes:

    data/reels.json   data/posts.json   data/data.csv   data/summary.json

Run:  python3 scripts/process.py
"""

import csv
import glob
import json
import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "raw")
DATA = os.path.join(ROOT, "data")
os.makedirs(DATA, exist_ok=True)
MELB = ZoneInfo("Australia/Melbourne")
START = datetime(2025, 10, 1, tzinfo=timezone.utc)
END = datetime(2026, 10, 1, tzinfo=timezone.utc)

HASHTAG = __import__("re").compile(r"#\w+")
OWNER_ID = "4730946554"  # instagram.com/momuians


def score(rec):
    """How complete a record is, used to keep the best copy of a duplicate."""
    return sum(
        1
        for v in (
            rec.get("like_count"),
            rec.get("comment_count"),
            rec.get("view_count"),
            rec.get("date"),
        )
        if v is not None
    )


def load_union():
    best = {}
    for path in sorted(glob.glob(os.path.join(RAW, "*.json"))):
        for item in json.load(open(path))["media"]:
            pk = item["pk"]
            if pk not in best or score(item) > score(best[pk]):
                best[pk] = item
    return list(best.values())


def clean(item):
    if item.get("product_type") in ("carousel_item", "ad"):
        return None
    # the DOM sweep also picks up recommended reels from other accounts
    if (item.get("id") or "").split("_")[-1] != OWNER_ID:
        return None
    if not item.get("date"):
        return None
    dt = datetime.fromisoformat(item["date"].replace("Z", "+00:00"))
    if not (START <= dt < END):
        return None

    local = dt.astimezone(MELB)
    caption = item.get("caption") or ""
    is_reel = bool(item.get("is_reel"))
    likes = item.get("like_count") or 0
    comments = item.get("comment_count") or 0
    views = item.get("view_count")

    # Some reels come back with the play count sitting in the like field and no
    # separate view field. Real reel like counts top out under 600, so a
    # four-figure "like" count with no view count is the view count.
    likes_known = True
    if is_reel and not views and likes > 600:
        views = likes
        likes = 0
        likes_known = False

    return {
        "pk": item["pk"],
        "shortcode": item.get("code"),
        "url": item.get("url"),
        "type": "reel" if is_reel else "post",
        "format": {1: "image", 2: "video", 8: "carousel"}.get(item.get("media_type"), "other"),
        "carousel_count": item.get("carousel_count"),
        "datetime_utc": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "date": local.strftime("%Y-%m-%d"),
        "time": local.strftime("%H:%M"),
        "day_of_week": local.strftime("%A"),
        "iso_week": local.strftime("%G-W%V"),
        "month": local.strftime("%Y-%m"),
        "caption": caption,
        "caption_length": len(caption),
        "hashtag_count": len(HASHTAG.findall(caption)),
        "likes": likes if likes_known else None,
        "comments": comments,
        "views": views,
        "interactions": (likes + comments) if likes_known else None,
        "engagement_per_view": round((likes + comments) / views, 4) if views and likes_known else None,
    }


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs)) if xs else None


def write_summary(rows, reels, posts, meta):
    from statistics import median

    months = sorted({r["month"] for r in rows})
    by_month = []
    for m in months:
        mr = [r for r in reels if r["month"] == m]
        mp = [p for p in posts if p["month"] == m]
        by_month.append({
            "month": m,
            "reels": len(mr),
            "posts": len(mp),
            "avg_reel_views": _mean([r["views"] for r in mr]),
            "avg_reel_likes": _mean([r["likes"] for r in mr]),
            "avg_post_likes": _mean([p["likes"] for p in mp]),
        })

    dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    dow = []
    for d in dow_order:
        dr = [r["views"] for r in reels if r["day_of_week"] == d and r["views"]]
        dow.append({"day": d, "avg_views": _mean(dr), "n": len(dr)})

    def slim(x):
        return {
            "date": x["date"], "type": x["type"], "format": x["format"],
            "views": x["views"], "likes": x["likes"], "comments": x["comments"],
            "url": x["url"],
            "caption": x["caption"].replace("\n", " ").strip()[:140],
        }

    rv = [r["views"] for r in reels]
    er = [r["engagement_per_view"] for r in reels if r["engagement_per_view"]]
    carousels = [p for p in posts if p["format"] == "carousel"]
    singles = [p for p in posts if p["format"] == "image"]

    summary = {
        **meta,
        "headline": {
            "reels": len(reels),
            "posts": len(posts),
            "first": rows[0]["date"],
            "last": rows[-1]["date"],
            "total_reel_views": sum(rv),
            "avg_reel_views": _mean(rv),
            "median_reel_views": round(median(rv)),
            "total_interactions": sum(
                (r["likes"] or 0) + r["comments"] for r in reels
            ) + sum(p["likes"] + p["comments"] for p in posts),
            "avg_engagement_rate": round(sum(er) / len(er), 4),
        },
        "reels_timeline": [
            {"date": r["date"], "views": r["views"], "interactions": r["interactions"]}
            for r in reels
        ],
        "posts_timeline": [
            {"date": p["date"], "likes": p["likes"], "comments": p["comments"], "format": p["format"]}
            for p in posts
        ],
        "by_month": by_month,
        "day_of_week": dow,
        "format_split": {
            "carousel": {"n": len(carousels), "avg_likes": _mean([p["likes"] for p in carousels])},
            "single": {"n": len(singles), "avg_likes": _mean([p["likes"] for p in singles])},
        },
        "top_reels": [slim(r) for r in sorted(reels, key=lambda x: -(x["views"] or 0))[:5]],
        "top_posts": [slim(p) for p in sorted(posts, key=lambda x: -x["likes"])[:5]],
    }
    with open(os.path.join(DATA, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)


def main():
    rows = [c for c in (clean(i) for i in load_union()) if c]
    rows.sort(key=lambda r: r["datetime_utc"])

    reels = [r for r in rows if r["type"] == "reel"]
    posts = [r for r in rows if r["type"] == "post"]

    meta = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "window": "2025-10-01 to 2026-09-30",
        "source": "instagram.com/momuians public grid + reels tab, scraped 2026-09-07",
        "count": len(rows),
    }

    with open(os.path.join(DATA, "reels.json"), "w") as f:
        json.dump({**meta, "count": len(reels), "reels": reels}, f, indent=2, ensure_ascii=False)
    with open(os.path.join(DATA, "posts.json"), "w") as f:
        json.dump({**meta, "count": len(posts), "posts": posts}, f, indent=2, ensure_ascii=False)

    cols = [
        "pk", "shortcode", "url", "type", "format", "carousel_count",
        "datetime_utc", "date", "time", "day_of_week", "iso_week", "month",
        "caption_length", "hashtag_count", "likes", "comments", "views",
        "interactions", "engagement_per_view", "caption",
    ]
    with open(os.path.join(DATA, "data.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({**r, "caption": r["caption"].replace("\n", " ").strip()})

    write_summary(rows, reels, posts, meta)

    span_days = (
        datetime.fromisoformat(rows[-1]["datetime_utc"].replace("Z", "+00:00"))
        - datetime.fromisoformat(rows[0]["datetime_utc"].replace("Z", "+00:00"))
    ).days or 1
    print(f"reels {len(reels)}  posts {len(posts)}  total {len(rows)}")
    print(f"span  {rows[0]['date']} -> {rows[-1]['date']}  ({span_days} days)")
    print(f"reels with views: {sum(1 for r in reels if r['views'])}/{len(reels)}")
    print("wrote data/: reels.json, posts.json, data.csv, summary.json")


if __name__ == "__main__":
    main()
