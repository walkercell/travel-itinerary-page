#!/usr/bin/env python3
"""Validate a trip JSON file and build a single-file itinerary page from the template.

Usage:
    python3 scripts/build_page.py trip.json -o my-trip.html
    python3 scripts/build_page.py trip.json --check        # validate only

Exit code 1 means the data has errors that would break the page; warnings are printed but do not fail.
Only the Python standard library is used.
"""
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_TEMPLATE = HERE.parent / "assets" / "template.html"
PLACEHOLDER = "/*__TRIP_DATA__*/"
SPOT_TOKEN = re.compile(r"\[\[([A-Za-z0-9_-]+)\]\]")


def collect_text(value):
    """Yield every string inside a nested JSON value."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for v in value:
            yield from collect_text(v)
    elif isinstance(value, dict):
        for v in value.values():
            yield from collect_text(v)


def validate(t):
    errors, warnings = [], []
    meta = t.get("meta") or {}
    if not meta.get("title"):
        errors.append("meta.title is required")

    segments = {s.get("id") for s in t.get("segments", [])}
    spots = t.get("spots") or {}

    for r in t.get("route", []):
        if r.get("seg") not in segments:
            errors.append(f"route item '{r.get('label')}' uses unknown segment '{r.get('seg')}'")

    # [[spot]] tokens anywhere in the text must point at a defined spot
    for text in collect_text({k: v for k, v in t.items() if k != "spots"}):
        for key in SPOT_TOKEN.findall(text):
            if key not in spots:
                errors.append(f"text references [[{key}]] but spots.{key} is not defined")

    for key, s in spots.items():
        for field in ("name", "desc", "ticket"):
            if not s.get(field):
                warnings.append(f"spots.{key}.{field} is empty")
        if not s.get("img"):
            warnings.append(f"spots.{key} has no image (run scripts/wiki_images.py)")

    dates = []
    for i, d in enumerate(t.get("days", [])):
        if d.get("seg") not in segments:
            errors.append(f"days[{i}] ({d.get('date')}) uses unknown segment '{d.get('seg')}'")
        if not d.get("slots"):
            warnings.append(f"days[{i}] ({d.get('date')}) has no slots")
        for sl in d.get("slots", []):
            if not (isinstance(sl, list) and len(sl) == 2):
                errors.append(f"days[{i}] slot must be [when, text], got {sl!r}")
        dates.append(d.get("date"))
    if len(dates) != len(set(dates)):
        errors.append("days[].date values must be unique (they key the map routes)")

    for i, f in enumerate(t.get("flights", [])):
        for field in ("no", "from", "to", "depart", "departTime", "arriveTime"):
            if not f.get(field):
                errors.append(f"flights[{i}] is missing '{field}'")
        dep = f.get("depart", "")
        try:
            parsed = datetime.fromisoformat(dep.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                errors.append(f"flights[{i}].depart '{dep}' needs a UTC offset, e.g. 2027-05-01T08:30:00+08:00")
        except ValueError:
            errors.append(f"flights[{i}].depart '{dep}' is not an ISO date-time")

    m = t.get("map") or {}
    places = m.get("places") or {}
    for pid, p in places.items():
        if not isinstance(p.get("lat"), (int, float)) or not isinstance(p.get("lng"), (int, float)):
            errors.append(f"map.places.{pid} needs numeric lat and lng")
        elif not (-90 <= p["lat"] <= 90 and -180 <= p["lng"] <= 180):
            errors.append(f"map.places.{pid} has out-of-range coordinates")
        if p.get("kind") not in ("spot", "hotel", "airport", "station", None):
            warnings.append(f"map.places.{pid}.kind '{p.get('kind')}' is not spot/hotel/airport/station")
        if p.get("spot") and p["spot"] not in spots:
            errors.append(f"map.places.{pid}.spot '{p['spot']}' is not defined in spots")
    for day, ids in (m.get("routes") or {}).items():
        if day not in dates:
            errors.append(f"map.routes key '{day}' does not match any days[].date")
        for pid in ids:
            if pid not in places:
                errors.append(f"map.routes['{day}'] uses unknown place '{pid}'")
        if len(ids) < 2:
            warnings.append(f"map.routes['{day}'] has fewer than 2 places, nothing to draw")
    for leg in m.get("airLegs", []):
        for pid in leg:
            if pid not in places:
                errors.append(f"map.airLegs uses unknown place '{pid}'")

    seen = set()
    for it in (t.get("budget") or {}).get("items", []):
        iid = it.get("id")
        if iid in seen:
            errors.append(f"budget item id '{iid}' is duplicated")
        seen.add(iid)
        opts = it.get("options") or []
        if not opts:
            errors.append(f"budget item '{iid}' has no options")
            continue
        for o in opts:
            if not isinstance(o.get("amount"), (int, float)):
                errors.append(f"budget item '{iid}' option '{o.get('label')}' needs a numeric amount")
        for name, p in (it.get("presets") or {}).items():
            idxs = p if isinstance(p, list) else [p]
            if bool(it.get("multi")) != isinstance(p, list):
                errors.append(f"budget item '{iid}' preset '{name}' must be {'a list' if it.get('multi') else 'a single index'}")
            for x in idxs:
                if not isinstance(x, int) or not 0 <= x < len(opts):
                    errors.append(f"budget item '{iid}' preset '{name}' index {x} is out of range")

    if not t.get("disclaimer"):
        warnings.append("no disclaimer: add a line telling readers to check official sources before travelling")
    return errors, warnings


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("trip", help="trip JSON file (see references/data-format.md)")
    ap.add_argument("-o", "--out", help="output HTML path (default: <trip name>.html)")
    ap.add_argument("--template", default=str(DEFAULT_TEMPLATE))
    ap.add_argument("--check", action="store_true", help="validate only, do not write HTML")
    args = ap.parse_args()

    trip_path = Path(args.trip)
    try:
        trip = json.loads(trip_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"ERROR: {trip_path} is not valid JSON: {e}")

    errors, warnings = validate(trip)
    for w in warnings:
        print(f"warning: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    if errors:
        sys.exit(1)
    print(f"validate: OK ({len(trip.get('days', []))} days, {len(trip.get('spots', {}))} spots, "
          f"{len((trip.get('budget') or {}).get('items', []))} budget items)")
    if args.check:
        return

    template = Path(args.template).read_text(encoding="utf-8")
    if PLACEHOLDER not in template:
        sys.exit(f"ERROR: template has no {PLACEHOLDER} placeholder")
    # "</" would end the <script> block early; JSON.parse reads "<\/" back as "</"
    payload = json.dumps(trip, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = template.replace(PLACEHOLDER, payload, 1)
    html = html.replace("<title>Travel Itinerary</title>",
                        f"<title>{(trip.get('meta') or {}).get('pageTitle') or trip['meta']['title']}</title>", 1)
    out = Path(args.out) if args.out else trip_path.with_suffix(".html")
    out.write_text(html, encoding="utf-8")
    print(f"built: {out}")


if __name__ == "__main__":
    main()
