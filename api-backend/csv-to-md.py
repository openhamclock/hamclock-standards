#!/usr/bin/env python3
# Copyright 2026 Open HamClock Standards
# SPDX-License-Identifier: Apache-2.0

"""
csv-to-md.py  —  Convert api-doc.csv back to api-doc.md

Supports the extended CSV format with a 10th column 'valid_values':
  - Enum definition rows start with ##enum:<Name> in the path column
  - ##enum:header is a column label row and is skipped
  - The valid_values column holds either:
      $EnumName   — reference to a named enum defined in a ##enum row
      a|b|c       — inline pipe-separated list of valid values
      (empty)     — no constraint

Enum definitions are written as an HTML comment AFTER the table (not between
the --- markers) so pandoc does not mistake them for YAML front matter.
The valid_values column is written as a 10th table column so md-to-openapi.py
and post-process.py can read it. md-to-doc.py ignores columns beyond 9 safely.

Usage:
    python3 csv-to-md.py [input.csv] [output.md]
"""

import csv
import sys

in_file  = sys.argv[1] if len(sys.argv) > 1 else 'api-doc.csv'
out_file = sys.argv[2] if len(sys.argv) > 2 else 'api-doc.md'

PREAMBLE = """\
---
# API Documentation
This work is licensed under a [Creative Commons Attribution-NoDerivatives 4.0 International License](https://creativecommons.org/licenses/by-nd/4.0/).

---
"""

MD_HEADER    = '| path | Argument | Units | Min | Max | Default | required | sample values | proposal | valid_values |'
MD_SEPARATOR = '| :--- | :--- | :--: | :--: | :--: | :--: | :--: | :--- | :--: | :--- |'


def row_to_md(cells):
    """Render up to 10 cells as a markdown table row."""
    while len(cells) < 10:
        cells.append('')
    parts = [f' {c} ' if c else ' ' for c in cells[:10]]
    return '|' + '|'.join(parts) + '|'


# ---------------------------------------------------------------------------
# Parse CSV
# ---------------------------------------------------------------------------
enum_defs = {}
data_rows = []

with open(in_file, newline='') as f:
    reader = csv.reader(f)
    for row in reader:
        if not row:
            continue
        first = row[0].strip()
        if first == '##enum:header':  # columns: ##enum:Name, values, description, required
            continue   # column label row — skip
        elif first.startswith('##enum:'):
            name   = first[len('##enum:'):]
            values = row[1].strip() if len(row) > 1 else ''
            desc   = row[2].strip() if len(row) > 2 else ''
            req    = row[3].strip().lower() if len(row) > 3 else 'no'
            enum_defs[name] = {'values': values, 'description': desc, 'required': req}
        elif first == 'path':
            continue
        else:
            while len(row) < 10:
                row.append('')
            data_rows.append(row)

# ---------------------------------------------------------------------------
# Write markdown
# ---------------------------------------------------------------------------
with open(out_file, 'w') as f:
    f.write(PREAMBLE)

    # Table first — enum comment goes AFTER the table so pandoc does not
    # mistake it for YAML front matter (which sits between the --- markers)
    f.write(MD_HEADER + '\n')
    f.write(MD_SEPARATOR + '\n')
    for row in data_rows:
        f.write(row_to_md(row) + '\n')

    # Enum definitions as HTML comment after the table
    if enum_defs:
        f.write('\n')
        f.write('<!-- ENUM DEFINITIONS — do not edit this block manually\n')
        for name, defn in enum_defs.items():
            req_str = ('  required=' + defn['required']) if defn['required'] else ''
            f.write('     enum:' + name + '=' + defn['values'] + req_str + '  # ' + defn['description'] + '\n')
        f.write('-->\n')

print(f"Written {len(data_rows)} rows, {len(enum_defs)} enum definitions to {out_file}")
