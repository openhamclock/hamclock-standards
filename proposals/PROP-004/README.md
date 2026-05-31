# Support tropical cyclone information on maps

This proposal adds tropical cyclone tracks to maps and a summary panel.
"Tropical cyclones" includes tropical/subtropical cyclones, hurricanes,
typhoons, and equivalent systems.

## Description

An endpoint on the backend can be queried for current tropical cyclones. The
return is a list of storms with location and intensity suitable for both a text
summary panel and a map overlay (current position + forecast track).

## Endpoint

```
/ham/HamClock/storms/storms.txt
```

The list contains all active named/numbered systems and their official
forecast points. There is no `age` argument and no query parameters.

## GET Method Arguments

None.

## Returned Results

UTF-8 text, Unix line endings (`\n`). One record per line. Lines beginning with
`#` are comments/metadata and MUST be ignored by parsers that do not understand
them. Blank lines MUST be ignored.

### Record format

Fields are comma-separated. The first nine fields are the stable v1 contract.
Fields after `ADVISORY` are optional v2 extensions; clients MUST tolerate their
presence or absence and MUST NOT fail if more fields appear later.

```
STORMNAME,BASIN,TYPE,CATEGORY,LAT,LON,WIND_KT,FCST_HOUR,ADVISORY[,STORM_ID,MSLP_MB]
```

| Field      | Required | Description |
|------------|----------|-------------|
| STORMNAME  | yes | Storm name, uppercase, e.g. `HELENE`. If unnamed, the ATCF wallet ID is used, e.g. `AL052026` (note: this is what the backend actually emits; `INVESTnnL` is **not** produced). Names never contain a comma. |
| BASIN      | yes | `AL` Atlantic, `EP` E.Pacific, `CP` C.Pacific, `WP` W.Pacific, `IO` Indian Ocean. **Only `AL`, `EP`, and `CP` are currently produced** (NHC/CPHC sources). `WP`/`IO` are reserved for a future JTWC ingest. |
| TYPE       | yes | Two-letter system status — see TYPE table below. Derived from the source classification when available, falling back to wind speed. |
| CATEGORY   | yes | `0`–`5`. `0` = anything below hurricane/typhoon force (TD, TS, SD, SS, etc.). `1`–`5` = Saffir–Simpson. For W.Pacific the same wind thresholds are applied as an approximation; Saffir–Simpson is not formally defined there. |
| LAT        | yes | Decimal degrees, `+`=N, `-`=S. One decimal place. |
| LON        | yes | Decimal degrees in range `-180.0`–`180.0`, `+`=E, `-`=W. One decimal place. |
| WIND_KT    | yes | Maximum sustained wind in knots (integer). `0` if unknown. |
| FCST_HOUR  | yes | `0` = current/analysis position. `> 0` = forecast valid time in hours from the analysis. Typical official values: `12,24,36,48,60,72,96,120`. Clients MUST accept any non-negative integer. |
| ADVISORY   | yes | The source advisory number string, e.g. `24` or `24A`. If the source does not provide one, the literal `-` is emitted. **This field is an advisory number, not a timestamp** (corrects v1, where the DTG was written here). |
| STORM_ID   | no (v2) | ATCF wallet ID, e.g. `AL052026`. Stable across an invest→named rename, suitable as a track key. |
| MSLP_MB    | no (v2) | Minimum sea-level pressure in millibars (integer), or `-` if unknown. Useful for the summary panel. |

### TYPE values

```
TD  Tropical Depression          (< 34 kt, tropical)
TS  Tropical Storm               (34–63 kt, tropical)
HU  Hurricane                    (>= 64 kt, AL/EP/CP)
TY  Typhoon                      (>= 64 kt, WP)
TC  Tropical Cyclone             (generic, IO / unclassified basin)
SD  Subtropical Depression       (< 34 kt, subtropical)
SS  Subtropical Storm            (>= 34 kt, subtropical)
PT  Post-Tropical Cyclone        (was tropical, now post-tropical/remnant)
EX  Extratropical Cyclone
DB  Disturbance / low / invest
LO  Remnant Low
```

**Mapping rule.** When the source provides a status code, map it directly
(ATCF `TY` field: `TD/TS/HU/TY/TC/SD/SS/EX/PT/LO/DB`). Only when status is
absent or `XX` may the backend fall back to deriving `TD/TS/HU/TY` from
`WIND_KT`. Clients MUST treat any unrecognized two-letter code as a generic
tropical system and still plot it.

### Ordering

- Records are grouped by storm; all rows for one storm are contiguous.
- Within a storm, the `FCST_HOUR=0` (current) row comes first, followed by
  forecast rows in ascending `FCST_HOUR`.
- This lets a client draw the current position as a bullseye and the remaining
  rows, in order, as the forecast track (line + circles).

### Metadata / header lines



```
# TROPICAL CYCLONES N storms as of YYYY-MM-DD HH:MM UTC
```

`N` MUST equal the number of distinct storms actually present in the file
(storms dropped for missing data are NOT counted — corrects v1, which counted
intended storms).

Compliant backends SHOULD additionally emit these ignorable comment lines:

```
# STORMS-FORMAT 2.0
# PUBLISHED 2026-05-31T14:00:00Z
# SOURCES NHC,CPHC
```

`PUBLISHED` is an ISO 8601 UTC timestamp (use a timezone-aware clock, not the
deprecated naive `utcnow()`).

### Zero-storm case

When no storms are active, the file MUST still be written and MUST contain a
valid header with `N = 0` and no data rows. Clients treat this as "clear the
overlay," distinct from a fetch failure.

## Example output

```
# TROPICAL CYCLONES 2 storms as of 2026-09-28 12:00 UTC
# STORMS-FORMAT 2.0
# PUBLISHED 2026-09-28T12:03:11Z
# SOURCES NHC,CPHC
HELENE,AL,HU,4,25.3,-80.1,120,0,24,AL092026,938
HELENE,AL,HU,4,26.5,-81.5,115,12,24,AL092026,945
HELENE,AL,HU,3,27.8,-82.4,110,24,24,AL092026,952
HELENE,AL,TS,0,30.8,-83.1,70,48,24,AL092026,985
HELENE,AL,PT,0,34.8,-82.9,35,96,24,AL092026,1002
KIRK,AL,HU,2,18.4,-45.2,90,0,12,AL122026,968
KIRK,AL,HU,2,19.8,-47.5,95,12,12,AL122026,964
```
