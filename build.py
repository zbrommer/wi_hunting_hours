#!/usr/bin/env python3
"""Rebuild dist/index.html from the DNR shooting-hours PDFs.

Usage:  python build.py [--year 2026]
Needs:  pdftotext (poppler-utils) on PATH, and `pip install zipcodes`.
"""
import argparse, calendar, collections, json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).parent
MDAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]  # Feb is set from --year in main()


def parse_chart(pdf: Path):
    """Return [month][day] -> [open_min, close_min] (minutes after midnight, Zone A)."""
    text = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True, check=True).stdout
    rows = {}
    for line in text.splitlines():
        m = re.match(r"\s*(\d{1,2})\s+(.*)\s+(\d{1,2})\s*$", line)
        if m:
            rows[int(m.group(1))] = m.group(2).split()
    out = []
    for mi, n in enumerate(MDAYS):
        col = []
        for d in range(1, n + 1):
            # Row 29 carries a junk Feb 29 cell ("#### 12:20") in non-leap years, so all 12 months are present.
            present = list(range(12)) if d == 29 else [i for i in range(12) if d <= MDAYS[i]]
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
        "N": parse_chart(ROOT / "data" / f"{a.year}-northern-shooting-hours.pdf"),
        "S": parse_chart(ROOT / "data" / f"{a.year}-southern-shooting-hours.pdf"),
    }
    t = (ROOT / "src" / "template.html").read_text(encoding="utf-8")
    t = t.replace("__YEAR__", str(a.year))
    t = t.replace("__DATA__", json.dumps(data, separators=(",", ":")))
    t = t.replace("__PLACES__", json.dumps(build_places(), separators=(",", ":")))
    (ROOT / "dist").mkdir(exist_ok=True)
    (ROOT / "dist" / "index.html").write_text(t, encoding="utf-8")
    print("wrote dist/index.html")


if __name__ == "__main__":
    main()
