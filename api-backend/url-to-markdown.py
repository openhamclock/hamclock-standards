#!/usr/bin/python3
# Copyright 2026 Open HamClock Standards
# SPDX-License-Identifier: Apache-2.0

"""
convert a list of get-method URLs to a GitHub Markdown table
"""
import sys
from urllib.parse import urlparse, parse_qs

def analyze_urls(filename):
    data_map = {}

    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
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

        # Print Markdown Header
        print("| path | Argument | Units | Min | Max | Default | required | sample values |")
        print("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")

        for path, info in sorted(data_map.items()):
            # If no arguments, just print the path row
            if not info["values"]:
                print(f"| {path} | | | | | | | |")
            else:
                for i, arg in enumerate(sorted(info["values"])):
                    vals = ", ".join(list(info["values"][arg])[:5])
                    if len(info["values"][arg]) > 5:
                        vals += "..."
                    
                    # For a clean look, only show the path on the first argument row for that path
                    display_path = path if i == 0 else ""
                    print(f"| {display_path} | {arg} | | | | | | {vals} |")

    except FileNotFoundError:
        print(f"Error: The file '{filename}' was not found.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 script_name.py <filename>")
        sys.exit(1)

    target_file = sys.argv[1]
    analyze_urls(target_file)
