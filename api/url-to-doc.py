#!/usr/bin/python3
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
                params = parse_qs(parsed.query) # Returns { 'key': ['val1', 'val2'] }

                if path not in data_map:
                    data_map[path] = {"keys": set(), "values": {}}

                for k, vals in params.items():
                    data_map[path]["keys"].add(k)
                    if k not in data_map[path]["values"]:
                        data_map[path]["values"][k] = set()
                    for v in vals:
                        data_map[path]["values"][k].add(v)

        # Print the Report
        print(f"{'PATH':<40} | {'ARG NAMES':<20} | {'SAMPLE VALUES'}")
        print("-" * 100)

        for path, info in sorted(data_map.items()):
            arg_names = ", ".join(sorted(info["keys"])) if info["keys"] else "None"
            
            # Format the first line for this path
            print(f"{path:<40} | {arg_names:<20} |")
            
            # Print the specific values found for each argument
            for arg in sorted(info["values"]):
                vals = ", ".join(list(info["values"][arg])[:5]) # Show first 5 values
                if len(info["values"][arg]) > 5:
                    vals += "..."
                print(f"{'':<40} | {'  -> ' + arg:<20} | {vals}")
            print("-" * 100)

    except FileNotFoundError:
        print("File not found. Please check the filename.")

if __name__ == "__main__":
    # Change 'urls.txt' to your filename
    analyze_urls('gets-extract.txt')
