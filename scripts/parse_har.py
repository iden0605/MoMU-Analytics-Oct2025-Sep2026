"""Pull media records out of one or more DevTools HAR exports.

How the data is gathered: record the Network tab with Preserve log on, scroll
the profile grid and then the Reels tab, "Save all as HAR with content", run
this. It walks every JSON response body looking for Instagram media objects and
writes a raw/scrape_*.json that process.py can read. See README for the full
click-by-click capture steps.

Instagram splits the data across queries: the profile grid's timeline query
carries taken_at/caption/likes/comments but no view count for reels, and the
Reels tab's clips query carries the view count but no timestamp or caption.
Neither response alone is a complete record, so this merges partial sightings
of the same pk field-by-field (first non-null value wins) rather than picking
one response over the other. One HAR covering both tabs is enough; several
HARs merge the same way.

Run:  python3 scripts/parse_har.py out-label ~/Downloads/momu.har [more.har ...]
"""

import base64
import bisect
import json
import os
import re
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OWNER_ID = "4730946554"  # instagram.com/momuians, for the sanity count only
SHORTCODE = re.compile(r"^[A-Za-z0-9_-]{8,15}$")
# carousel frames repeat their parent's counts under a different pk; process.py
# drops them anyway, but there is no reason to walk into them
SKIP_KEYS = ("carousel_media", "edge_sidecar_to_children", "carousel_media_children")


def body_text(entry):
    content = entry.get("response", {}).get("content") or {}
    text = content.get("text")
    if not text:
        return None
    if content.get("encoding") == "base64":
        try:
            text = base64.b64decode(text).decode("utf-8", "replace")
        except Exception:
            return None
    return text


def json_blobs(text):
    """HAR bodies are sometimes one JSON doc, sometimes newline-delimited chunks."""
    text = text.strip()
    if not text:
        return
    if text.startswith("for (;;);"):
        text = text[len("for (;;);"):]
    try:
        yield json.loads(text)
        return
    except ValueError:
        pass
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                yield json.loads(line)
            except ValueError:
                continue


def views_of(m):
    for key in ("play_count", "ig_play_count", "view_count", "video_view_count"):
        if m.get(key) is not None:
            return m[key]
    return None


def from_v1(m):
    """A media object from the api/v1 or graphql shape. Any field may be missing
    depending on which query returned it — the caller merges sightings later.

    A HAR of a profile page carries far more than media: users, suggested-user
    chaining, DM threads, config blobs. Plenty of those have a pk or an id, and
    some have an unrelated `code`, so a media object has to look like one: a
    numeric pk, a shortcode-shaped code, and either a real media_type or the
    clips product_type the Reels tab sends."""
    code = m.get("code")
    pk = m.get("pk") or (str(m.get("id")).split("_")[0] if m.get("id") else None)
    if not code or not pk:
        return None
    if not isinstance(code, str) or not SHORTCODE.match(code):
        return None
    if not str(pk).isdigit():
        return None
    media_type = m.get("media_type")
    product = m.get("product_type") or ("carousel_container" if media_type == 8 else None)
    if media_type not in (1, 2, 8) and product != "clips":
        return None
    is_reel = product == "clips" or media_type == 2
    caption = m.get("caption")
    taken_at = m.get("taken_at")
    return {
        "pk": str(pk),
        "id": str(m.get("id") or pk),
        "code": code,
        "taken_at": taken_at,
        "date": datetime.fromtimestamp(taken_at, timezone.utc).isoformat().replace("+00:00", "Z")
        if taken_at
        else None,
        "media_type": media_type,
        "product_type": product,
        "is_reel": is_reel,
        "caption": (caption or {}).get("text", "") if isinstance(caption, dict) else (caption or None),
        "like_count": m.get("like_count"),
        "comment_count": m.get("comment_count"),
        "view_count": views_of(m),
        "reshare_count": m.get("reshare_count"),
        "carousel_count": m.get("carousel_media_count"),
        "url": "https://www.instagram.com/%s/%s/" % ("reel" if is_reel else "p", code),
    }


def from_graphql_node(n):
    """The older edge_media shape, still served on some surfaces."""
    code = n.get("shortcode")
    if not isinstance(code, str) or not SHORTCODE.match(code):
        return None
    if not str(n.get("id") or "").isdigit():
        return None
    ts = n.get("taken_at_timestamp")
    typename = n.get("__typename") or ""
    is_reel = bool(n.get("is_video")) and n.get("product_type") == "clips"
    media_type = 8 if typename == "GraphSidecar" else (2 if n.get("is_video") else 1)
    caption = None
    edges = (n.get("edge_media_to_caption") or {}).get("edges") or []
    if edges:
        caption = edges[0].get("node", {}).get("text", "")
    children = (n.get("edge_sidecar_to_children") or {}).get("edges") or []
    return {
        "pk": str(n.get("id")),
        "id": str(n.get("id")),
        "code": code,
        "taken_at": ts,
        "date": datetime.fromtimestamp(ts, timezone.utc).isoformat().replace("+00:00", "Z") if ts else None,
        "media_type": media_type,
        "product_type": "clips" if is_reel else ("carousel_container" if media_type == 8 else None),
        "is_reel": is_reel,
        "caption": caption,
        "like_count": (n.get("edge_media_preview_like") or {}).get("count"),
        "comment_count": (n.get("edge_media_to_comment") or {}).get("count"),
        "view_count": n.get("video_view_count") or n.get("video_play_count"),
        "reshare_count": None,
        "carousel_count": len(children) or None,
        "url": "https://www.instagram.com/%s/%s/" % ("reel" if is_reel else "p", code),
    }


def merge(existing, new):
    """Fill in whatever `existing` is missing from `new`; never overwrite a known value."""
    for k, v in new.items():
        if v is not None and existing.get(k) is None:
            existing[k] = v
    # is_reel/product_type: trust whichever sighting is more specific (clips beats a guess)
    if new.get("product_type") == "clips":
        existing["product_type"] = "clips"
        existing["is_reel"] = True


def walk(node, out):
    if isinstance(node, dict):
        rec = from_v1(node) or from_graphql_node(node)
        if rec:
            if rec["pk"] in out:
                merge(out[rec["pk"]], rec)
            else:
                out[rec["pk"]] = rec
        for k, v in node.items():
            if k not in SKIP_KEYS:
                walk(v, out)
    elif isinstance(node, list):
        for v in node:
            walk(v, out)


def estimate_missing_dates(found):
    """Instagram's pk is a Snowflake-style id, so it's monotonic with taken_at.
    The Reels tab's clips query never sends a timestamp, so fill it in for any
    reel it didn't come with by interpolating between whatever items in this
    same scrape did come with a real taken_at."""
    calibration = sorted(
        (int(m["pk"]), m["taken_at"]) for m in found.values() if m.get("date")
    )
    if len(calibration) < 2:
        return 0
    pks = [p for p, _ in calibration]
    n = 0
    for m in found.values():
        if m.get("date"):
            continue
        pk = int(m["pk"])
        i = bisect.bisect_left(pks, pk)
        if i == 0:
            est = calibration[0][1]
        elif i == len(pks):
            est = calibration[-1][1]
        else:
            p0, t0 = calibration[i - 1]
            p1, t1 = calibration[i]
            est = t0 if p1 == p0 else t0 + (pk - p0) / (p1 - p0) * (t1 - t0)
        est = int(est)
        m["taken_at"] = est
        m["date"] = datetime.fromtimestamp(est, timezone.utc).isoformat().replace("+00:00", "Z")
        m["date_estimated"] = True
        n += 1
    return n


def load_har(path, out):
    har = json.load(open(path, encoding="utf-8"))
    entries = har.get("log", {}).get("entries", [])
    bodies = empty = 0
    for entry in entries:
        text = body_text(entry)
        if not text:
            empty += 1
            continue
        if "{" not in text:
            continue
        bodies += 1
        for blob in json_blobs(text):
            walk(blob, out)
    print(f"{os.path.basename(path)}: {len(entries)} entries, {bodies} with a JSON body, {empty} with no body captured")


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit("usage: python3 scripts/parse_har.py <out-label> <file.har> [more.har ...]")
    # allow the old one-argument form (just a HAR path) for convenience
    if args[0].endswith(".har"):
        label, paths = "har", args
    else:
        label, paths = args[0], args[1:]
    if not paths:
        sys.exit("usage: python3 scripts/parse_har.py <out-label> <file.har> [more.har ...]")

    found = {}
    for path in paths:
        load_har(path, found)

    estimated = estimate_missing_dates(found)
    if estimated:
        print(f"estimated the date for {estimated} reels with no timestamp, from pk order")

    dated = [m for m in found.values() if m["date"]]
    undated = [m for m in found.values() if not m["date"]]
    media = sorted(dated, key=lambda m: -m["taken_at"]) + undated
    if not media:
        sys.exit(
            "No media found. The HAR probably has no response bodies — re-export with\n"
            '"Save all as HAR (with content)" and keep DevTools open for the whole scroll.'
        )

    no_views = sum(1 for m in media if m["is_reel"] and m["view_count"] is None)
    payload = {
        "scrapedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "count": len(media),
        "reels": sum(1 for m in media if m["is_reel"]),
        "posts": sum(1 for m in media if not m["is_reel"]),
        "undated": len(undated),
        "media": media,
    }
    out = os.path.join(ROOT, "raw", f"scrape_{label}.json")
    with open(out, "w") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    ours = [m for m in media if m["id"].split("_")[-1] == OWNER_ID]
    print(f"{len(media)} media ({payload['reels']} reels, {payload['posts']} posts, {len(undated)} undated)")
    print(f"{len(ours)} of them belong to @momuians; process.py drops the rest")
    if dated:
        print(f"span {dated[-1]['date'][:10]} -> {dated[0]['date'][:10]}")
    if len(ours) < len(media) / 2:
        print("Most of this is other accounts' media — that looks like the home feed, not")
        print("the profile. Re-record starting from instagram.com/momuians.")
    if no_views:
        print(f"{no_views} reels have no view count — scroll the Reels tab further and re-run with both HARs")
    print(f"wrote {os.path.relpath(out, ROOT)}")


if __name__ == "__main__":
    main()
