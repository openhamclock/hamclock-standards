# HF and VHF Band Conditions (HamQSL / N0NBH)

This proposal adds two new panes to HamClock — **HF Conditions** and **VHF Conditions** — sourced from Paul Herrman N0NBH's HamQSL solar feed through the OHB backend. HF Conditions presents N0NBH's calculated Good/Fair/Poor summary for four band groups by day and night; VHF Conditions presents his aurora and sporadic-E status. Both give operators the familiar at-a-glance "HamQSL banner" read of current propagation, path-independent and distinct from the existing VOACAP DE-DX matrix, with credit to HamQSL.com shown on each pane.

## Description

HamClock already plots the VOACAP DE-DX reliability matrix (`PLOT_CH_BC`) and the individual space-weather indices (SFI, Kp, solar wind, Bz, aurora, DRAP, X-ray). What it does not show is N0NBH's *calculated* conditions — the compact, location-agnostic Good/Fair/Poor band summary and VHF phenomena that many operators recognise from the HamQSL solar banner. This proposal supplies that layer as two panes.

Both are ordinary rotating panes, selected from the HamClock pane-selection menu alongside Contests, On-The-Air, and the space-weather panes, and may be assigned to any rotating pane slot or to the large PANE_0 slot. They support all standard build resolutions (800×480 through 3200×1920); every position and glyph size is derived from live pane and font metrics rather than fixed pixels.

**HF Conditions** is a four-row by two-column grid: the band groups 80–40, 30–20, 17–15, and 12–10 metres down the left, Day and Night across the top, each cell filled green/yellow/red for Good/Fair/Poor. The header carries no words — a sun glyph is centred over the Day column and a crescent moon over the Night column, both drawn from primitives. **VHF Conditions** is a six-row list — Aurora, 6 m, 4 m, 2 m EU, 2 m NA, and a geomagnetic Field line — with each right-justified value colour-coded to the N0NBH legend (magenta 144 MHz Es, yellow-green 70 MHz Es, green 50 MHz Es, amber high-MUF, red mid-latitude aurora, grey closed).

The underlying data is sourced from the public HamQSL solar XML feed. The OHB server polls HamQSL once every ten minutes — a single central poll serving every client, far lighter on the source than per-client requests — reduces the XML to the fields HamClock needs, and writes a single small CSV file that HamClock retrieves through the standard backend cached-file pipeline. Until that first backend call returns, both panes render a neutral **TBD** placeholder rather than a blank box.

## OHB Server Component

The server-side generator is `fetch_hamqsl.py`. Like the TLE and net tooling and unlike the map overlays, it produces a small text file rather than rendered imagery. It runs on its own schedule (it has no upstream chain to piggyback on), polling the HamQSL XML endpoint and writing one CSV that feeds both panes.

### Data Source

A single query returns the whole solar-terrestrial snapshot. The fields consumed from the XML:

| Field              | HamQSL XML tag                     | Used For                                          |
| ------------------ | ---------------------------------- | ------------------------------------------------- |
| Solar flux         | `solarflux`                        | HF display; HF model fallback driver              |
| Sunspot number     | `sunspots`                         | HF display                                        |
| A / K index        | `aindex` / `kindex`                | HF display; HF model fallback driver              |
| X-ray              | `xray`                             | Supporting solar detail                           |
| Solar wind / Bz    | `solarwind` / `magneticfield`      | Supporting solar detail                           |
| Aurora / lat       | `aurora` / `latdegree`             | Supporting solar detail                           |
| Geomag field       | `geomagfield`                      | VHF Field row                                     |
| Signal/noise       | `signalnoise`                      | VHF Field row                                     |
| MUF                | `muf`                              | Supporting solar detail                           |
| HF conditions      | `calculatedconditions/band`        | HF grid: 4 groups × {day,night} → Good/Fair/Poor  |
| VHF conditions     | `calculatedvhfconditions/phenomenon` | VHF rows: aurora + 6/4/2m E-skip                |

**Source:** HamQSL.com solar XML (Paul Herrman N0NBH)
**URL:** `https://www.hamqsl.com/solarxml.php`
**Download size:** one small XML document per poll.

N0NBH's `electonflux` tag is spelled without the second "r"; the generator maps it to `electronflux` on our side. Use is by permission of the author, whose only condition is that HamQSL.com be credited; that credit is emitted in the file header and rendered on both panes.

### Data Transformation

The script issues one HTTPS GET with an identifying User-Agent, parses the XML, and emits a self-describing CSV of `section,name,qualifier,value` rows under three sections — `SOLAR`, `HF`, and `VHF`. HF band ratings and VHF phenomena are passed through verbatim as N0NBH reports them (`Good`/`Fair`/`Poor`, `Band Closed`, `50MHz ES`, and so on); the client maps rows by section and name, so columns are order-independent and new fields may be appended without breaking older or newer clients.

Comment lines beginning with `#` carry the attribution, the HamQSL update time, and the OHB fetch time, so freshness can be judged and the required credit travels with the data. On any fetch or parse error the previous good file is left intact — never overwritten with empty or partial data — so the panes degrade to *stale* rather than *blank*. Writing is atomic (temporary file in the same directory, then rename).

### Output File

A single file is written, following the OHB htdocs convention so it is served under the standard `/ham/HamClock/` path:

```
/opt/hamclock-backend/htdocs/ham/HamClock/hamqsl/hamqsl-cond.csv
```

Served to HamClock at:

```
<backend>/ham/HamClock/hamqsl/hamqsl-cond.csv
```

CSV format:

```
# OHB HamQSL conditions  source=HamQSL.com/N0NBH (https://www.hamqsl.com/solar.html)
# hamqsl_updated=<HamQSL time>  ohb_fetched=<UTC timestamp>  poll=<secs>s
# Data courtesy Paul Herrman N0NBH - used with permission. Credit: HamQSL.com
# format: section,name,qualifier,value   (lines beginning with # are comments, skip them)
SOLAR,sfi,,188
SOLAR,k,,1
...
HF,80m-40m,day,Poor
HF,80m-40m,night,Good
...
VHF,vhf-aurora,northern_hemi,Band Closed
VHF,E-Skip,europe_6m,50MHz ES
...
```

The leading comment lines carry the required credit, the update time, and the poll interval. HamClock skips every line beginning with `#`.

### Update Schedule

N0NBH advises that, unlike the 15-minute banner images, the XML feed is near real-time — some fields refresh as often as every five minutes. The file is therefore regenerated on a modest fixed cadence of ten minutes, which stays fresh while remaining a good bandwidth citizen, and is wired in with a single cron entry:

```
*/10 * * * *  /opt/hamclock-backend/scripts/fetch_hamqsl.py
```

A single backend file serves any number of HamClock instances through the client's cached-file age check; one central poll replaces what would otherwise be one request per client.

### Server Dependencies

| Dependency   | Type   | Purpose                                                       |
| ------------ | ------ | ------------------------------------------------------------ |
| `python3`    | System | Fetch + parse (stdlib `urllib` and `xml.etree` only)         |
| `cron`       | System | Scheduling                                                   |
| `lighttpd`   | OHB    | Serves the static CSV under `/ham/HamClock/`                 |

No external Python packages, `curl`, or `jq` are required.

## HamClock Client Component

The client side adds **two new rotating panes**, a shared parser and cache, and no change to any existing pane.

| Aspect             | Value                                                                                     |
| ------------------ | ----------------------------------------------------------------------------------------- |
| Entry points       | Pane-selection menu items "HF Cond" and "VHF Cond"                                         |
| Fetch path         | `/hamqsl/hamqsl-cond.csv` (relative to the `/ham/HamClock` root the fetch prepends)        |
| Parser             | `retrieveHamQSL()` — reads `section,name,qualifier,value`, skips `#` comment lines         |
| Data structure     | `HamQSLData` (SFI/SN/Kp, `hf[4][2]` ratings, VHF phenomenon strings, geomag/S-N, validity) |
| HF pane            | `plotHFConditions()` — 4×2 grid, sun/moon header glyphs                                    |
| VHF pane           | `plotVHFConditions()` — six right-justified, colour-coded rows                             |
| Update entry points| `updateHFConditions()` / `updateVHFConditions()` — one shared fetch feeds both panes       |
| Retrieval          | Standard backend cached-file path from the configured backend host                        |
| Refresh interval   | `HQ_INTERVAL` = 660 s                                                                      |
| Touched files      | `HamClock.h`, `wifi.cpp`, `plotmgmnt.cpp`, `Makefile`, new `hamqsl.cpp`                    |

The parser is section-driven and tolerant of missing fields: absent HF cells or VHF rows default rather than corrupting the display, so a backend serving an older or newer column layout continues to work. A single retrieval populates a shared cache, so selecting both panes at once still results in one backend request per refresh.

Frequency/condition retrieval reuses the backend cached-file path, so the panes require HamClock to be pointed at the OHB backend (for example with `-b host:port`) that serves the file.

**Pane-count note.** These two panes bring the reference client to 32 panes — exactly the width of the `uint32_t` `plot_rotset` rotation bitmask, which is persisted with `NVReadUInt32`. Reaching 32 requires two mechanical corrections in the pane manager: the "reset bits too high" mask must be valid at `PLOT_CH_N == 32` (where `1 << 32` is undefined), and every pane-bit shift must be unsigned (`1u << i`) so bit 31 is well-defined. A hypothetical 33rd pane would require widening `plot_rotset` to `uint64_t` and a NVRAM migration; the migration-safe form keeps each existing 32-bit rotset field (the low half, preserving saved values) and appends a new HI field, rather than resizing in place.

## Screen Layout

### HF Conditions Pane

A 4×2 grid sized from pane and font metrics. Title "HF Bands" is centred at the top. The band-group labels (80-40, 30-20, 17-15, 12-10) run down the left in grey; a sun glyph is centred over the Day column and a crescent moon over the Night column, both drawn from primitives (the sun a filled disc with eight rays; the moon a disc with a crescent carved by a second, background-coloured disc), scaled from pane width so they render correctly at every build size. Each of the eight cells is filled green/yellow/red for Good/Fair/Poor with the word centred in black. Until the first successful backend call, every cell shows a neutral grey **TBD** placeholder. A credit footer reads `HamQSL.com  N0NBH`.

If the HF block is ever absent from the file but SFI and Kp are present, the pane computes the eight ratings locally from a validated SFI+K model (matched to N0NBH's own published examples across the solar cycle) and the footer changes to a yellow `OHB model (SFI/K)` so the source is never misrepresented.

### VHF Conditions Pane

A six-row list, labels left in grey and values right-justified. Title "VHF Cond" is centred at the top.

| Row     | Source field                       | Notes                                                       |
| ------- | ---------------------------------- | ----------------------------------------------------------- |
| Aurora  | `vhf-aurora` / `northern_hemi`     | Colour-coded: mid-lat red, hi-lat amber, closed grey        |
| 6 m     | `E-Skip` / `europe_6m`             | `50 ES` green when open                                      |
| 4 m     | `E-Skip` / `europe_4m`             | `70 ES` yellow-green when open                               |
| 2 m EU  | `E-Skip` / `europe`                | `144 ES` magenta / `High MUF` amber                         |
| 2 m NA  | `E-Skip` / `north_america`         | as above, North-American region                             |
| Field   | `geomagfield` + `signalnoise`      | plain grey; e.g. `VR QUIET S0-S1`                            |

Values are compacted for the narrow pane (`Band Closed` → `Closed`, `50MHz ES` → `50 ES`). Until the first successful backend call, every value shows `TBD`. A credit footer reads `HamQSL.com  N0NBH`.

### Web Endpoint (optional)

A `get_hamqsl.txt` handler may be added to expose the parsed values as key/value lines, so headless and scripted clients get the same HF/VHF summary as the on-screen panes. It is not required for the panes to function.

## Operational Notes

**Most useful for:** operators who want the quick, path-independent "are the bands good right now" read that the HamQSL banner provides — N0NBH's calculated HF summary and VHF aurora/Es status — without invoking the DE-DX-specific VOACAP matrix or consulting an external site.

**Units:** HF ratings and VHF phenomena are categorical (Good/Fair/Poor, open/closed) and carry no unit configuration; VHF sporadic-E rows name the band in MHz as N0NBH reports it.

**Refresh behaviour:** the OHB server polls HamQSL every ten minutes and serves a single cached file; the client refreshes every `HQ_INTERVAL` (660 s), serving its own cache between fetches. On a cold start the panes show `TBD` until the first successful retrieval, after which the last good data remains on screen during each (blocking) refetch — `TBD` does not flash on subsequent refreshes.

**Failure behaviour:** on a fetch or parse error the server leaves the last good CSV in place, so the panes go stale rather than blank. The client shows `TBD` only until the first data arrives. The HF pane additionally falls back to the local SFI+K model if the HF block is missing but SFI is present; the VHF pane has no model fallback, because aurora and sporadic-E are measured phenomena rather than functions of the solar indices.

**Attribution:** the HamQSL data is used with the author's permission on the single condition that HamQSL.com be credited. That credit is emitted in the CSV header and drawn in both pane footers, and HamQSL should be listed in the OHB `ATTRIBUTION.md`.

**Backend requirement:** the file is fetched from the configured HamClock backend, not from HamQSL directly. The client must be pointed at an OHB instance that runs `fetch_hamqsl.py`; otherwise the path returns 404 from a backend that does not host it.

**Display limitations:** HamClock's embedded fonts are ASCII-only, so the Day/Night columns are marked by drawn sun and moon glyphs rather than symbols or emoji, and condition text is plain words. The HF ratings are N0NBH's own heuristic, not a point-to-point prediction, and are intentionally complementary to — not a replacement for — the VOACAP DE-DX pane. The VHF sporadic-E and aurora rows are passed through from N0NBH's measured/derived values and are not recomputed by the client.
