# Antenna Index

## Introduction

The Backend / HamClock api provides methods for fetching voacap propagation information in the following URLs:

> /ham/HamClock/fetchBandConditions.pl
> /ham/HamClock/fetchVOACAPArea.pl
> /ham/HamClock/fetchVOACAP-TOA.pl

Those functions take three optional arguments described herein

> &ANTTX=
> &ANtRX=
> &ANTTXRX=


### ANTTXRX

This argument controls what Antennas will be using for voacap propagation analysis. If missing, the value 0 isused

Values are specified as ANTTXRX=anttxrx where antxrx is processed as in the following table

| anttxrx | Description              |
|---------|--------------------------|
|    0    | process as default       |
|    1    | Use ANTTX                |
|    2    | Use ANTRX                |
|    3    | Use both ANTTX and ANTRX |

### ANTTX, ANTRX
These parameters control what antenna profile is used for Transmission and Reception for the De and DX station respectively.

The value used is defined in the voacap.ant.csv file which is the specification of the interface. voacap antenna path is given; however,
the method used by the backend in implementation independent.
Instead of just showing the raw numeric value index, they are shown as msb and lsb values where the index is calculated as:
> index=msb*256+lsb

## Files

Files are described below

### voacap.ant.csv

The specificaiton of the antenna values used. The CSV has the following columns

| column | Description                                |
|--------|--------------------------------------------|
|   msb  | used in antenna index calculation          |
|   lsb  | used in antenna index calculation          |
| path   | path to antenna file under voacap antennas |
| description | description of antenna extracted from header of antenna file |

## README.md

This file

### gen_antenna_data.py

python program to generate antenna_data.py from voacap.ant.csv 
Intended for use on the backend server side.

usage:
```bash
python3 gen_antenna_data.py voacap.ant.csv antenna_data.py
```

### gen_antenna_data.showing

bash script to generate antenna_data.h from voacap.ant.csv
Intended for use on the HamClock client side.

usage:
```bash
./gen_antnna_data.sh voacap.ant.csv antenna_data.h 
```

### antenna_lookup.py

example code that provides lookup functions for antenna_data.py

### antenna_test.py

example code that shows usage of antenna_lookup.py

### antenna_test.cpp

example code that shows usage of antenna_lookup.py

### Makefile

Madefile that creates sample programs and generates header files
It can create programs antenna_dump to display antenna data, antenna_test to show usage similar to antenna_test.py

usage:
```bash
echo clean files
make clean
echo make all targets
make
echo run exmaple programs
./antenna_test
./antenna_dump
