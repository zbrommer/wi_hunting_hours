# WI Shooting Hours

A single-page, mobile-first lookup of legal shooting hours for Wisconsin deer, bear, small game and fall turkey, plus waterfowl and spring turkey.
The DNR publishes these as tiny PDF charts that are hard to read; this page makes them easy to read. Goal: host it publicly for other hunters.

## Layout
- `data/` — the official DNR 2026 Northern and Southern Area PDFs (source of truth): `{year}-{northern|southern}-shooting-hours.pdf` (deer, bear, small game, fall turkey) and `{year}-{northern|southern}-waterfowl-shooting-hours.pdf` (waterfowl, spring turkey).
- `src/template.html` — the page. Has `__DATA__`, `__PLACES__` and `__YEAR__` placeholders; everything else (CSS/JS) is inline.
- `build.py` — parses the PDFs (via `pypdf`) and a Wisconsin town list (from the `zipcodes` pip package) into the template → `dist/index.html`. Needs `pip install pypdf zipcodes`. Page data is `D[kind][region][month][day] = [open_min, close_min]`, where kind is `big` or `bird` (see `KINDS` in build.py and the template).
- `dist/` — the built site: `index.html` plus the static files in `STATIC` in build.py (copied from `src/`). Deploy the whole folder. No backend, no external requests except Google Fonts.
- `src/sw.js` — minimal service worker. Only there so Android can show notifications; no fetch handler, so no caching yet.
- `src/manifest.webmanifest` + `src/icons/` — web app manifest (standalone, name "WI Hours") so iPhone Home Screen installs run as an app; iOS only allows web notifications there (16.4+). Icons are drawn by `tools/make_icons.py` (stdlib only); rerun it if the icon design changes.
- `.github/workflows/pages.yml` — publishes `dist/` to GitHub Pages on every push to main. Live at https://wishootinghours.com (custom domain set in repo Settings → Pages, not a CNAME file; DNS at Dynadot: 4 GitHub A records + `www` CNAME → zbrommer.github.io). Rebuild and commit `dist/` before pushing.

## Rules the page implements
- Charts are Zone A times, local clock time, already including DST (Mar 8 and Nov 1, 2026).
  - Deer, bear, small game, fall turkey: 30 min before sunrise to 20 min after sunset.
  - Waterfowl, spring turkey: 30 min before sunrise to sunset (same opens; closes exactly 20 min earlier every day in 2026).
- Zone offsets are by longitude, added to both open and close, same for both charts: A east of 88°W +0, B 88–89 +4, C 89–90 +8, D 90–91 +12, E 91–92 +16, F west of 92 +20.
- Northern Area = Pierce, Dunn, Eau Claire, Clark, Marathon, Shawano, Oconto, Door and every county north of them (30 counties, listed in `NORTH` in the template). Southern = everything else.
- Town search: county → area, ZIP-centroid longitude → zone. It warns within ~0.06° of a zone line. It also accepts "lat, lon".
- Does NOT cover season dates or special opening-day hours.

## Data quirks
- The deer charts show a junk Feb 29 cell (`#### 12:20`) even though 2026 isn't a leap year; the waterfowl charts leave it blank. The parser handles both and exits if a row has an unexpected cell count. `build.py` sets Feb to 29 automatically when `--year` is a leap year.
- The parser sanity-checks that only the two DST days jump more than 3 minutes (it prints those two expected jumps per chart).

## Page features
A sticky top bar with a live per-second countdown for today (opens in / legal · closes in / closed · opens tomorrow in; blaze orange while legal; DST-aware overnight), so hunters don't have to scroll with gloves on. It has an optional "Notify me" switch (off by default, saved in localStorage `wiAlert`): when the countdown hits zero (legal light / end of hours) it vibrates and shows a notification. No sound on purpose. Static site, so it only works while the page is open; it skips alerts more than 10 min late and won't fire when the user changes zone/area/type. iPhone needs the page added to the Home Screen for notifications. When alerts can't be turned on, the switch opens a help card (`HELP` in the template) with steps: add to Home Screen (iPhone Safari), turn on in Settings (iPhone app, denied), update iOS (no API), or allow from the address bar (other browsers, denied). Web pages can't open Settings directly. Below the title, a "Your spot" summary (place · area · zone · hunt type) with a Change button; the settings panel is collapsed for returning visitors and open on a first visit. The times card has its own ‹ date › header (tap the date for a picker). Settings: hunt-type toggle (deer/bear/small game/fall turkey vs waterfowl/spring turkey), area toggle, zone buttons (with example towns per area), town/coordinate search, a "Use my location" button (browser geolocation: exact longitude → zone, nearest town's county → area, with a warning within ~0.28° of a town in the other area), big open/close times, a day bar with the legal window and a "now" marker, a live "legal now / opens in / closes in" status (uses America/Chicago time), and a 14-day table that marks DST changes. Hunt type, area and zone are remembered in localStorage. A dark "Put WI Hours on your Home Screen" banner under the title (✕ hides it for 30 days, localStorage `wiPromo`) and, below the 14-day table, an "Add to your Home Screen" button; both hidden once installed. They use Chrome's own install prompt when offered (`beforeinstallprompt`), otherwise opens iPhone / Android / other steps (`addIOS`, `addAndroid`, `addOther` in `HELP`). Footer: "Not an official Wisconsin DNR tool" plus a link to the DNR regs page.

## Status / next steps
- Live on GitHub Pages at https://wishootinghours.com.
- Each year: drop the four new DNR PDFs into `data/` with the names above, and run `python build.py --year {year}`. The year text in the template is a `__YEAR__` placeholder filled in by the build. Also update the DST dates noted above.
- Ideas: multi-year support, PWA/offline (useful at camp with no signal), a more precise town gazetteer than ZIP centroids.
