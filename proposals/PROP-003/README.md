# Support light strike information on maps

This proposal adds lightning strike counts to the HamClock UI. 

An endpoint on the backend can be queried with a lat/lon and radius. The return is a list of lightning strikes with precise latitude and longitude, and time in seconds since the last strike.

To limit the list of strikes not to be too long the history is 900 seconds.

The endpoint and GET method arguments are:
```
/ham/HamClock/lightning/strikes.pl?lat=28.54&lon=-81.38&radius=10000
```
where radius is in kilometers.

The depth of history is up to the backend to choose and 900 is a typical default. The client can request a smaller list if it wants with the ```maxage`` argument in seconds:

```
/ham/HamClock/lightning/strikes.pl?lat=28.54&lon=-81.38&radius=10000&maxage=300
```

