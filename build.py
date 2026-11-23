#!/usr/bin/env python3
"""Rebuild dist/index.html from the DNR shooting-hours PDFs.

Usage:  python build.py [--year 2026]
Needs:  pip install pypdf zipcodes
"""
import argparse, calendar, collections, json, re, shutil, sys
from pathlib import Path

ROOT = Path(__file__).parent
STATIC = ["sw.js", "manifest.webmanifest", "icons/icon-180.png", "icons/icon-192.png", "icons/icon-512.png"]
MDAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]  # Feb is set from --year in main()

# Chart kinds: key in the page data -> PDF file name part. Both use the same zones/offsets.
KINDS = {
    "big": "shooting-hours",            # deer, bear, small game, fall turkey: to 20 min after sunset
    "bird": "waterfowl-shooting-hours", # waterfowl, spring turkey: to sunset
}


def parse_chart(pdf: Path):
    """Return [month][day] -> [open_min, close_min] (minutes after midnight, Zone A)."""
    from pypdf import PdfReader
    text = "\n".join(p.extract_text() for p in PdfReader(pdf).pages)
    rows = {}
    for line in text.splitlines():
        m = re.match(r"\s*(\d{1,2})\s+(.*)\s+(\d{1,2})\s*$", line)
        if m:
            rows[int(m.group(1))] = m.group(2).split()
    out = []
    for mi, n in enumerate(MDAYS):
        col = []
        for d in range(1, n + 1):
            present = [i for i in range(12) if d <= MDAYS[i]]
            # Some charts have a junk Feb 29 cell ("#### 12:20") in non-leap years; others leave it blank.
            if d == 29 and 1 not in present and len(rows[d]) == 2 * len(present) + 2:
                present = list(range(12))
            if len(rows[d]) != 2 * len(present):
                sys.exit(f"{pdf.name}: day {d} has {len(rows[d])} cells, expected {2 * len(present)}")
            i = present.index(mi)
            a, p = rows[d][2 * i], rows[d][2 * i + 1]
            h, mm = map(int, a.split(":")); h2, m2 = map(int, p.split(":"))
            col.append([h * 60 + mm, (h2 + 12) * 60 + m2])
        out.append(col)
    # Sanity check: only the two DST changes should jump more than 3 minutes.
    prev = None
    for mi, col in enumerate(out):
        for d, r in enumerate(col):
            if prev and (abs(r[0] - prev[0]) > 3 or abs(r[1] - prev[1]) > 3):
                print(f"{pdf.name}: jump at {mi+1}/{d+1} (expected only at DST changes)", file=sys.stderr)
            prev = r
    return out


def build_places():
    """Wisconsin towns from ZIP data: [name, county, lat, lon_west]."""
    import zipcodes
    g = collections.defaultdict(list)
    for z in zipcodes.filter_by(state="WI"):
        if not z["lat"] or not z["active"]:
            continue
        for c in [z["city"]] + z["acceptable_cities"]:
            g[c.title().replace("'S", "'s")].append(z)
    out = []
    for name, zs in g.items():
        std = [z for z in zs if z["zip_code_type"] == "STANDARD"] or zs
        lat = sum(float(z["lat"]) for z in std) / len(std)
        lon = sum(float(z["long"]) for z in std) / len(std)
        county = collections.Counter(z["county"].replace(" County", "") for z in std).most_common(1)[0][0]
        name = re.sub(r"^Mc ?([a-z])", lambda m: "Mc" + m.group(1).upper(), name.replace("Mc ", "Mc"))
        name = name.replace(" Du ", " du ").replace(" De ", " de ")
        out.append([name, county, round(lat, 3), round(-lon, 3)])
    return sorted(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2026)
    a = ap.parse_args()
    MDAYS[1] = 29 if calendar.isleap(a.year) else 28
    data = {
        kind: {
            "N": parse_chart(ROOT / "data" / f"{a.year}-northern-{part}.pdf"),
            "S": parse_chart(ROOT / "data" / f"{a.year}-southern-{part}.pdf"),
        }
        for kind, part in KINDS.items()
    }
    t = (ROOT / "src" / "template.html").read_text(encoding="utf-8")
    t = t.replace("__YEAR__", str(a.year))
    t = t.replace("__DATA__", json.dumps(data, separators=(",", ":")))
    t = t.replace("__PLACES__", json.dumps(build_places(), separators=(",", ":")))
    (ROOT / "dist").mkdir(exist_ok=True)
    (ROOT / "dist" / "index.html").write_text(t, encoding="utf-8")
    for f in STATIC:  # service worker, web app manifest, icons: copied as-is
        (ROOT / "dist" / f).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / "src" / f, ROOT / "dist" / f)
    print("wrote dist/index.html +", ", ".join(STATIC))


if __name__ == "__main__":
    main()
