#!/usr/bin/python3
# Copyright 2026 Open HamClock Standards
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may find a copy of the License in the LICENSE file at the repo root.

"""
convert a list of get-method URLs to table with extended metadata columns
"""
import sys
from urllib.parse import urlparse, parse_qs

def analyze_urls(filename):
    # path -> { "keys": set(), "values": { "key": set() } }
    data_map = {}

    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # Parse the URL
                parsed = urlparse(line)
                path = parsed.path
                params = parse_qs(parsed.query) 

                if path not in data_map:
                    data_map[path] = {"keys": set(), "values": {}}

                for k, vals in params.items():
                    data_map[path]["keys"].add(k)
                    if k not in data_map[path]["values"]:
                        data_map[path]["values"][k] = set()
                    for v in vals:
                        data_map[path]["values"][k].add(v)

        # Print License Header
        print("# API Documentation")
        print("This work is licensed under a [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/).")
        print("\n---\n")

        # Print the Report Header
        # Column widths: Path(30), Argument(20), Units(8), Min(6), Max(6), Default(8), Required(9), Samples(rest)
        header = f"{'path':<30} | {'Argument':<20} | {'Units':<8} | {'Min':<6} | {'Max':<6} | {'Default':<8} | {'required':<9} | {'sample values'}"
        print(header)
        print("-" * len(header))

        for path, info in sorted(data_map.items()):
            # Print the path row first
            print(f"{path:<30} | {'':<20} | {'':<8} | {'':<6} | {'':<6} | {'':<8} | {'':<9} |")
            
            # Print the specific values and empty metadata columns for each argument
            for arg in sorted(info["values"]):
                vals = ", ".join(list(info["values"][arg])[:5]) 
                if len(info["values"][arg]) > 5:
                    vals += "..."
                
                # format: path(blank), argument, units(blank), min(blank), max(blank), default(blank), required(blank), samples
                print(f"{'':<30} | {arg:<20} | {'':<8} | {'':<6} | {'':<6} | {'':<8} | {'':<9} | {vals}")
            
            print("-" * len(header))

    except FileNotFoundError:
        print(f"Error: The file '{filename}' was not found.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 script_name.py <filename>")
        sys.exit(1)

    target_file = sys.argv[1]
    analyze_urls(target_file)
