# Hamclock RESTful web server 

## Introduction

Hamclock provides a RESTfull web server interface to allow the user change the operation of hamclock.

Hamclock command parameter -e sets the port where the restful server resides. The default is 8080.
To disable the RESTfull web server use '-e -1'.

## Operation

Going to the RESTfull web server's url with no arguments displays the port to access HamClock live and a summary of commands.


## Current commands 

get_capture.bmp       get live screen shot in bmp format
get_config.txt        get current display settings
get_contests.txt      get current list of contests
get_de.txt            get DE info
get_dx.txt            get DX info
get_dxpeds.txt        get current list of DXpeditions
get_dxspots.txt       get DX spots
get_gpio?             pin=MCP&latched=[true,false]
get_livespots.txt     get live spots list
get_livestats.txt     get live spots statistics
get_ontheair.txt      get POTA/SOTA activators
get_satellite.txt     get current sat info
get_satellites.txt    get list of all sats
get_sensors.txt       get sensor data
get_spacewx.txt       get space weather info
get_sys.txt           get system stats
get_time.txt          get current time
get_voacap.txt        get current band conditions matrix
set_adif?             pane=[0123] (POST)
set_alarm?            state=off|armed&time=HR:MN&utc=yes|no
set_auxtime?          format=[one_from_menu]
set_bmp?              pane=[1,2,3,map]&fit=[resize,crop,fill][&off] (POST)
set_cluster?          host=xxx&port=yyy
set_debug?            name=xxx&level=n
set_defmt?            fmt=[one_from_menu]&atin=RSAtAt|RSInAgo
set_displayOnOff?     on|off
set_displayTimes?     on=HR:MN&off=HR:MN&day=[Sun..Sat]&idle=mins
set_gpio?             pin=MCP&level=[hi,lo]&blink=hz
set_livespots?        (see error message)
set_mapcenter?        lng=X
set_mapcolor?         setup=name&color=R,G,B
set_mapview?          Style=S&Grid=G&Projection=P&RSS=on|off&Night=on|off
set_newde?            grid=AB12&lat=X&lng=Y&call=AA0XYZ
set_newdx?            grid=AB12&lat=X&lng=Y
set_once_alarm?       state=off|armed&time=YYYY-MM-DDTHR:MN&tz=DE|UTC
set_pane?             Pane[0123]=X,Y,Z... any from:
   VOACAP_DEDX DE_Wx DX_Wx Solar_Flux Planetary_K Moon NOAA_SpcWx Sunspot_N
   X-Ray SDO Solar_Wind DRAP Contests Live_Spots Bz_Bt On_The_Air Aurora
   DXPeditions Disturbance
set_panzoom?          pan_x=X&pan_y=Y&pan_dx=dX&pan_dy=dY&zoom=Z
set_rotator?          state=[un]stop|[un]auto&az=X&el=X
set_rss?              reset|add=X|network|interval=secs|on|off|file (POST)
set_satname?          abc|none
set_sattle?           name=abc&t1=line1&t2=line2
set_screenlock?       lock=on|off
set_senscorr?         sensor=76|77&dTemp=X&dPres=Y
set_stopwatch?        reset|run|stop|lap|countdown=mins
set_time?             change=delta_seconds
set_time?             ISO=YYYY-MM-DDTHH:MM:SS
set_time?             Now
set_time?             unix=secs_since_1970
set_title?            call|title|onair=[text]&fg=R,G,B&bg=R,G,B|rainbow
set_touch?            x=X&y=Y
set_voacap?           band=X&power=W&tz=DE|UTC&mode=X&map=X&TOA=X
exit                  exit HamClock
postDiags             post diagnostic logs and configuration settings
restart               restart HamClock
updateVersion         update to latest version

## Examples

Examples use localhost as the IP address of HamClock

### get_caputere.bmp

To get a screen snapshot, open this url in a browser with connectivity with hamclock. 

http://localhost:8080/get_capture.bmp

### set de grid to center of EM13

http://localhost:8080/set_newde?grid=EM13
