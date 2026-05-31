# Support backend admin messages to HamClocks

This proposal enables the backend to send system messages to HamClocks

## Description

At times a backend system administrator may need to send messages to HamClocks. A method of notifying the HamClock will enable simple text-based messages to be sent.

The endpoint is:
```
/ham/HamClock/sysmsg.pl
```
The choice of the typical perl CGI enables programmatic response to message requests.

The response is a simple text string. Line wraps are handled by the HamClock client.

## Endpoint
```
/ham/HamClock/sysmsg.pl
```

## GET Method Arguments

| Argument | Units | Min | Max | Default | required |
| -------- | :---: | :-: | :-: | :-----: | :------: |

