#!/usr/bin/env python3
"""Find a freely licensed photo URL for each attraction on Wikimedia.

Usage:
    python3 scripts/wiki_images.py "Eiffel Tower" "Louvre" "Sagrada Família"
    python3 scripts/wiki_images.py --trip trip.json            # fill spots[*].img where it is empty
    python3 scripts/wiki_images.py --trip trip.json --write    # ...and save the result back

Lookup order for each name: English Wikipedia page image → Wikimedia Commons file search.
Use the attraction's English name (spots[*].en) for the best hit rate.
Always open a few results to check the photo really shows the place before publishing.
Only the Python standard library is used. Requests are spaced out to stay polite to the API.
"""
import argparse
import json
import sys
import time
import urllib.parse
import urllib.request

UA = "travel-itinerary-page/1.0 (personal itinerary builder)"
WIDTH = 960


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def from_wikipedia(name):
    q = urllib.parse.urlencode({"action": "query", "titles": name, "prop": "pageimages", "piprop": "thumbnail",
                                "pithumbsize": str(WIDTH), "format": "json", "redirects": "1"})
    data = get("https://en.wikipedia.org/w/api.php?" + q)
    for page in data.get("query", {}).get("pages", {}).values():
        src = (page.get("thumbnail") or {}).get("source", "")
        # skip logos and maps, which pageimages sometimes returns
        if src and not src.lower().endswith((".svg.png", "logo.png")) and "logo" not in src.lower():
            return src
    return None


def from_commons(name):
    q = urllib.parse.urlencode({"action": "query", "generator": "search", "gsrsearch": f"{name} filetype:bitmap",
                                "gsrnamespace": "6", "gsrlimit": "3", "prop": "imageinfo", "iiprop": "url",
                                "iiurlwidth": str(WIDTH), "format": "json"})
    data = get("https://commons.wikimedia.org/w/api.php?" + q)
    pages = sorted(data.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 99))
    for page in pages:
        info = (page.get("imageinfo") or [{}])[0]
        if info.get("thumburl"):
            return info["thumburl"]
    return None


def strip_tracking(url):
    return url.split("?")[0] if url else url


def find(name):
    for fn in (from_wikipedia, from_commons):
        try:
            url = fn(name)
            if url:
                return strip_tracking(url)
        except Exception as e:  # network hiccups should not stop the batch
            print(f"  ({fn.__name__} failed for {name!r}: {e})", file=sys.stderr)
        time.sleep(1)
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("names", nargs="*", help="attraction names (English works best)")
    ap.add_argument("--trip", help="trip JSON; looks up spots whose img is empty")
    ap.add_argument("--write", action="store_true", help="with --trip: write found URLs back into the file")
    args = ap.parse_args()

    if args.trip:
        trip = json.load(open(args.trip, encoding="utf-8"))
        changed = 0
        for key, s in (trip.get("spots") or {}).items():
            if s.get("img"):
                continue
            name = s.get("en") or s.get("name")
            url = find(name)
            print(f"{key}\t{name}\t{url or 'NOT FOUND'}")
            if url:
                s["img"] = url
                changed += 1
        if args.write and changed:
            json.dump(trip, open(args.trip, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            print(f"wrote {changed} image URL(s) to {args.trip}")
    for name in args.names:
        print(f"{name}\t{find(name) or 'NOT FOUND'}")
    if not args.trip and not args.names:
        ap.print_help()


if __name__ == "__main__":
    main()
