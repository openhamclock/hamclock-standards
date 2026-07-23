# Solar Proton Flux (GOES) for the Recent R-S-G Reports Pane

This proposal adds a **Solar Proton Flux** data feed to HamClock, sourced from the GOES >= 10 MeV integral proton flux published by NOAA SWPC through the OHB backend, completing the third of three scales shown in the **Recent R-S-G Reports** view. That view already draws NOAA-style R (radio blackout) and G (geomagnetic storm) history from HamClock's existing X-ray and Kp feeds; this proposal supplies the missing S (solar radiation storm) scale so all three NOAA scales are shown together, with a consistent severity legend, in one place.

## Description

HamClock's existing NOAA SpaceWx pane (`PLOT_CH_NOAASPW`) shows the current and forecast R/S/G levels as a small text table. Tapping the body of that pane (rather than its top strip, which still opens the normal pane-choice menu) opens **Recent R-S-G Reports**: a full-map, three-panel history view styled after NOAA SWPC's own "Recent R-S-G reports" product — Solar X-ray Flux (flare class A-X) on top, Solar Proton Flux (log10 pfu) in the middle, and Geomagnetic Activity (Kp) on the bottom, each with a six-block NOAA severity legend (green through dark red) down its right edge. Tapping inside any panel shows the nearest data point's value and age. A "Resume" button and a data-source credit line close out the view.

The X-ray and Kp panels already had live data behind them — HamClock's existing `retrieveXRay()` and `retrieveKp()` feeds, unchanged by this proposal. The proton panel did not: no proton flux feed exists anywhere in HamClock today, and the reference client's only historical source for HF-relevant solar data at this granularity is the X-ray feed. This proposal adds the missing feed so the S-scale panel is real data rather than a permanent "No data" placeholder.

This is a data-source addition to an existing view, not a new pane: it adds no new pane-selection menu entry, no new NVRAM setting, and no change to how the R-S-G Reports view is opened or closed.

## OHB Server Component

The server-side generator is `fetch_proton.py`. Like `xray_simple.py`, it produces a small plain-text time series rather than rendered imagery, and — because the proton panel shares the X-ray panel's 10-minute cadence and 25-hour window so the two line up on the same time axis — it follows the same binning approach.

### Data Source

**Source:** NOAA SWPC GOES primary satellite, >= 10 MeV integral proton flux — the same quantity the NOAA S-scale (solar radiation storm) is based on.
**URL:** `https://services.swpc.noaa.gov/json/goes/primary/integral-protons-3-day.json`
**Download size:** one small JSON document per poll (the 3-day file is used, not the 1-day one, for the same reason `xray_simple.py` prefers `xrays-3-day.json`: a safety margin against a slow-to-publish latest bin).

The feed carries several energy thresholds in one document (>= 1, >= 5, >= 10, >= 30 MeV, and so on); only the >= 10 MeV channel is kept. The energy label is matched numerically (the leading number is extracted and compared for an exact match against 10) rather than by substring, specifically so "10 MeV" is never confused with "100 MeV".

No permission or attribution agreement is required — this is public-domain U.S. government data — but SWPC is credited in the pane regardless (see Screen Layout).

### Data Transformation

The script fetches with a retry-with-backoff loop and an identifying User-Agent, then:

1. Filters to the >= 10 MeV channel as above.
2. Drops negative/sentinel "no data" readings rather than let a bogus value distort the output (real flux is always >= 0).
3. Bins to fixed 10-minute intervals (UTC-aligned), taking the max per bin — the same convention `xray_simple.py` uses, appropriate for a severity feed where the peak within a bin matters more than its average.
4. Drops the newest bins SWPC may not have finished publishing yet (a 15-minute lag margin, the same idea as `xray_simple.py`'s `CSI_LAG_MINUTES`).
5. Keeps the most recent 150 bins — the file is refused and left unwritten if fewer than 150 usable bins are available, the same strict all-or-nothing behaviour `kindex_simple.py` uses for Kp, so a partial or malformed upstream response degrades the client to a graceful "No data" rather than showing a distorted partial series.

Writing is atomic (temporary file in the same directory, `fsync`, then rename) — the same pattern used throughout OHB.

### Output File

```
/opt/hamclock-backend/htdocs/ham/HamClock/proton/protons.txt
```

Served to HamClock at:

```
<backend>/ham/HamClock/proton/protons.txt
```

Format is deliberately the simplest possible: 150 lines, oldest first, one decimal pfu value per line, no header or comment lines:

```
1.230e+00
1.180e+00
1.340e+00
...
```

Unlike the HamQSL CSV (PROP-009), which is a multi-field, multi-consumer file with a section/name/qualifier/value shape, this feed has exactly one consumer and one field, so it follows `kindex.txt`'s minimal convention rather than inventing a header format. Values are written in scientific notation to comfortably span the range from quiet-sun flux (~10⁻² pfu) to a major SEP event (~10⁵ pfu) without fixed-decimal precision loss at either end.

### Update Schedule

```
1-57/4 * * * *  $SCRIPTS/cron-wrapper.sh $VENV/bin/python3 $SCRIPTS/fetch_proton.py
```

Same cadence as `xray_simple.py`, since the two feeds are meant to stay time-aligned on the client.

### Server Dependencies

| Dependency   | Type   | Purpose                                      |
| ------------ | ------ | --------------------------------------------- |
| `python3`    | System | Fetch + transform                             |
| `pandas`     | Python | JSON parsing, UTC-aligned binning             |
| `requests`   | Python | HTTPS fetch with retry                        |
| `cron`       | System | Scheduling                                    |
| `lighttpd`   | OHB    | Serves the static file under `/ham/HamClock/` |

Unlike `poll_activenets.py` or the stdlib-only `fetch_hamqsl.py`, this generator uses `pandas`, matching `xray_simple.py`'s existing dependency footprint rather than adding a new one.

## HamClock Client Component

No new pane, menu entry, or NVRAM setting. This proposal adds one new data feed and wires it into the existing R-S-G Reports view (itself unconditional — it renders regardless of whether the proton feed is present, showing "No data" for that panel alone if not).

| Aspect              | Value                                                                                      |
| ------------------- | ------------------------------------------------------------------------------------------- |
| Entry point          | Existing: tap the body of the NOAA SpaceWx pane                                            |
| Fetch path          | `/proton/protons.txt` (relative to the `/ham/HamClock` root the fetch prepends)             |
| Parser              | `retrieveProtonFlux()` — one `strtof` value per line, same shape as `retrieveXRay()`        |
| Data structure      | `ProtonData` — `x[PROTON_NV]` (age, hours), `p[PROTON_NV]` (log10 pfu); `PROTON_NV == XRAY_NV` |
| Rendering           | `plotRSGHistory()` / `rsgDrawPanel()` in `plotmap.cpp` (existing, unchanged in shape)        |
| Refresh interval    | `PROTON_INTERVAL` = `XRAY_INTERVAL` = 610 s                                                 |
| Touched files       | `HamClock.h`, `spacewx.cpp`, `plotmap.cpp`                                                  |

`retrieveProtonFlux()` deliberately rejects, rather than tolerates, malformed input: it parses each line with `strtof()` and stops populating the array the instant a line fails to parse as a leading number, rather than defaulting a bad line to some placeholder value. This matters in practice — a backend that does not yet serve `/proton/protons.txt` returns an HTML 404 page, and an earlier, laxer implementation that used `atof()` (which silently returns `0.0` for non-numeric input) allowed a handful of HTML body lines to be read as valid low readings, producing a spurious rising line instead of the correct "No data" state. The strict parser makes "backend does not implement this proposal" and "backend implements it but has no data right now" both render identically and correctly as "No data", with no partial/bogus series in between.

**Related robustness note.** While integrating this feed, `rsgDrawPanel()`'s y-axis auto-scaling was found to trust the full range of whatever data it was given, with no bound on how far a single extreme sample could push the axis. This was hit in practice by an unrelated pre-existing gap in `retrieveKp()` (no guard against a missing-data sentinel in unpublished future Kp predictions), not by this proposal's feed, but the fix is general and applies to all three panels: the auto-scaled range is now clamped to a bounded multiple of the nominal display range, and tick-label text is hard-clipped to never render outside its own panel regardless of how wide an extreme value's formatted text would be. Backends implementing this proposal do not need to validate proton values beyond the non-negative check in Data Transformation above — the client-side floor is defense in depth, not a requirement placed on the server.

## Screen Layout

No change to the existing R-S-G Reports layout (three stacked panels, six-block NOAA severity legend per panel, tap-to-inspect popups, Resume button). This proposal fills in what was previously the middle panel's permanent placeholder state:

| Row               | Behaviour with this proposal implemented                                             | Behaviour without it                |
| ----------------- | -------------------------------------------------------------------------------------- | ------------------------------------ |
| Solar X-ray Flux  | Unchanged — real data, as today                                                        | Unchanged — real data, as today      |
| Solar Proton Flux | Real GOES >= 10 MeV data, log10(pfu) scale, tap-to-inspect shows eg `3.2 pfu`           | "No data" placeholder, as today      |
| Geomagnetic Activity | Unchanged — real data, as today                                                     | Unchanged — real data, as today      |

A small `Data: NOAA SWPC` credit is drawn bottom-right of the pane, covering the X-ray and proton panels (both GOES-derived); it is present regardless of whether this proposal's feed is available, since the X-ray panel is already GOES data.

## Operational Notes

**Most useful for:** operators who want NOAA's own R/S/G correlation view — is a given event a radio blackout, a radiation storm, a geomagnetic storm, or some combination — without leaving HamClock or cross-referencing swpc.noaa.gov by hand.

**Units:** the wire format is raw pfu (particle flux units); the client converts to log10 internally to match the panel's log-scale axis and NOAA's own S-scale thresholds (S1 = 10 pfu, S2 = 100 pfu, and so on).

**Refresh behaviour:** the server polls SWPC roughly every 4 minutes and serves a single cached file; the client refreshes on the same 610 s cadence as the X-ray panel it's time-aligned with.

**Failure behaviour:** if the backend does not serve this file, or the fetch or parse fails for any reason, the proton panel shows "No data" while the X-ray and Kp panels continue to render normally — the feed's absence never blocks or degrades the rest of the view. The server-side "refuse to write a short file" rule and the client-side strict-parse rule are both deliberately conservative in the same direction: prefer an honest "No data" over a plausible-looking but wrong series.

**Attribution:** NOAA SWPC data is public domain and requires no permission, but is credited in the pane for consistency with the X-ray panel it sits beside.

**Backend requirement:** the file is fetched from the configured HamClock backend, not from NOAA directly — HamClock has no TLS client and cannot reach `services.swpc.noaa.gov` on its own. The client must be pointed at an OHB instance running `fetch_proton.py`; a backend that does not implement this proposal simply returns 404, which the client already treats as "No data".

**Display limitations:** the panel shows a single log-scale trend line colour-coded by S-scale severity, matching the X-ray panel's presentation; it is a history view, not a forecast, and carries no per-event particle-energy spectrum detail beyond the single >= 10 MeV threshold NOAA's own S-scale uses.
