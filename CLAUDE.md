# WI Shooting Hours

A single-page, mobile-first lookup of legal shooting hours for Wisconsin deer, bear, small game and fall turkey.
The DNR publishes these as tiny PDF charts that are hard to read; this page makes them easy to read. Goal: host it publicly for other hunters.

## Layout
- `data/` — the official DNR 2026 Northern and Southern Area PDFs (source of truth).
- `src/template.html` — the page. Has `__DATA__`, `__PLACES__` and `__YEAR__` placeholders; everything else (CSS/JS) is inline.
- `build.py` — parses the PDFs (via `pdftotext -layout`) and a Wisconsin town list (from the `zipcodes` pip package) into the template → `dist/index.html`.
- `dist/index.html` — the built, self-contained page. Deploy just this file (as index.html). No backend, no external requests except Google Fonts.

## Rules the page implements
- Charts are Zone A times: 30 min before sunrise to 20 min after sunset. They're local clock time and already include DST (Mar 8 and Nov 1, 2026).
- Zone offsets are by longitude, added to both open and close: A east of 88°W +0, B 88–89 +4, C 89–90 +8, D 90–91 +12, E 91–92 +16, F west of 92 +20.
- Northern Area = Pierce, Dunn, Eau Claire, Clark, Marathon, Shawano, Oconto, Door and every county north of them (30 counties, listed in `NORTH` in the template). Southern = everything else.
- Town search: county → area, ZIP-centroid longitude → zone. It warns within ~0.06° of a zone line. It also accepts "lat, lon".
- Does NOT cover waterfowl/spring turkey (different hours) or season dates.

## Data quirks
- The PDFs show a junk Feb 29 cell (`#### 12:20`) even though 2026 isn't a leap year; the parser skips it. `build.py` sets Feb to 29 automatically when `--year` is a leap year.
- The parser sanity-checks that only the two DST days jump more than 3 minutes.

## Page features
Area toggle, zone buttons (with example towns per area), town/coordinate search, date picker with prev/next/today, big open/close times, a day bar with the legal window and a "now" marker, a live "legal now / opens in / closes in" status (uses America/Chicago time), and a 14-day table that marks DST changes. Area and zone are remembered in localStorage. Footer: "Not an official Wisconsin DNR tool" plus a link to the DNR regs page.

## Status / next steps
- Currently shared as a Claude artifact. Next: self-host (GitHub Pages / Cloudflare Pages / S3+CloudFront), maybe with a custom domain.
- Each year: drop the new DNR PDFs into `data/` as `{year}-northern-shooting-hours.pdf` / `{year}-southern-shooting-hours.pdf`, and run `python build.py --year {year}`. The year text in the template is a `__YEAR__` placeholder filled in by the build. Also update the DST dates noted above.
- Ideas: multi-year support, PWA/offline (useful at camp with no signal), use device geolocation when self-hosted (it's blocked inside the artifact sandbox), a more precise town gazetteer than ZIP centroids.
