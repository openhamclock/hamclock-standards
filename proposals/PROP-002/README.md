# Handle SDO and moon movies servers going down at NASA

We've had outages from hours to weeks of SDO and Moon movies. HamClock handles movies with the direct URL to NASA. It seems like it would be a better idea for HC to go to the server and let the server decide what the best URL is.

There are backups for each of these so the backend could easily offer backups.

Currently PR 27 (<https://github.com/openhamclock/hamclock/pull/27>) is a change to HamClock that would direct these requests to the backend. The backend would need to handle them.

The backend could handle them any way it wishes. One possible approach is generating 307's dynamically based on what host is available:

<https://github.com/komacke/open-hamclock-backend/blob/main/ham/HamClock/moon/movies/moon-movies.pl>
and
<https://github.com/komacke/open-hamclock-backend/blob/main/ham/HamClock/SDO/movies/sdo-movies.pl>

How the backend handles these requests is not the subject of this proposal. The proposal is simply to change where HamClock goes for movies. The backend implementation would need to handle these URLs
