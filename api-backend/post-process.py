#!/usr/bin/env python3
# Copyright 2026 Open HamClock Standards
# SPDX-License-Identifier: Apache-2.0

"""
post-process.py  —  Inject enum definitions and valid-values column into pandoc HTML

Reads:
  - <raw.html>   pandoc-generated HTML (10-column table with valid_values as last col)
  - <source.md>  api-doc.md with ENUM DEFINITIONS comment block

Writes:
  - <output.html> with:
      - Enum Definitions section before the table
      - The raw valid_values column (containing $EnumName or empty) replaced with
        a styled "valid values" column showing the enum name as a clickable pill link

Usage:
    python3 post-process.py <raw.html> <source.md> <output.html>
"""

import html as html_mod
import re
import sys

# ---------------------------------------------------------------------------
# Args
# ---------------------------------------------------------------------------
if len(sys.argv) < 4:
    print('Usage: post-process.py <raw.html> <source.md> <output.html>')
    sys.exit(1)

raw_html_path = sys.argv[1]
md_path       = sys.argv[2]
out_path      = sys.argv[3]

# ---------------------------------------------------------------------------
# Read inputs
# ---------------------------------------------------------------------------
if raw_html_path == '-':
    raw_html = sys.stdin.read()
else:
    with open(raw_html_path, encoding='utf-8') as f:
        raw_html = f.read()

with open(md_path, encoding='utf-8') as f:
    md_content = f.read()

# ---------------------------------------------------------------------------
# Parse enum definitions from md HTML comment block
# ---------------------------------------------------------------------------
enum_defs = {}

enum_block = re.search(r'<!--\s*ENUM DEFINITIONS.*?-->', md_content, re.DOTALL)
if enum_block:
    for line in enum_block.group().splitlines():
        m = re.match(r'\s*enum:(\w+)=([^#]+)(?:#\s*(.*))?', line)
        if m:
            name   = m.group(1).strip()
            values = [v.strip() for v in m.group(2).strip().split('|')]
            desc   = (m.group(3) or '').strip()
            enum_defs[name] = {'values': values, 'description': desc}

# ---------------------------------------------------------------------------
# CSS to inject
# ---------------------------------------------------------------------------
INJECTED_CSS = """\
<style>
/* ── Enum definitions section ── */
.enum-section {
  margin: 1.5em 0 2em 0;
  padding: 1em 1.2em;
  background: #f8f9fa;
  border-left: 4px solid #1a5276;
  border-radius: 3px;
}
.enum-section h2 {
  margin-top: 0;
  font-size: 1.1rem;
  color: #1a5276;
  letter-spacing: 0.04em;
}
.enum-block { margin: 0.8em 0 0 0; }
.enum-block + .enum-block {
  margin-top: 1.2em;
  padding-top: 1em;
  border-top: 1px solid #dde;
}
.enum-name {
  font-family: monospace;
  font-size: 0.95rem;
  font-weight: bold;
  color: #1a5276;
}
.enum-desc { font-size: 0.85rem; color: #555; margin: 0.15em 0 0.4em 0; }
.enum-values { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 0.3em; }
.enum-value {
  display: inline-block;
  font-family: monospace;
  font-size: 0.82rem;
  background: #e8f0fe;
  border: 1px solid #b3c6e7;
  border-radius: 3px;
  padding: 2px 8px;
  color: #1a3a6b;
}
/* ── valid values column ── */
th.valid-values-col {
  text-align: center;
  white-space: nowrap;
}
td.valid-values-col {
  text-align: center;
  white-space: nowrap;
}
td.valid-values-col a.enum-link {
  font-family: monospace;
  font-size: 0.78rem;
  color: #1a5276;
  background: #e8f0fe;
  border: 1px solid #b3c6e7;
  border-radius: 3px;
  padding: 2px 7px;
  text-decoration: none;
}
td.valid-values-col a.enum-link:hover {
  background: #cddcf7;
  border-color: #1a5276;
}
</style>
"""

# ---------------------------------------------------------------------------
# Build enum section HTML
# ---------------------------------------------------------------------------
def esc(s):
    return html_mod.escape(s or '')

def build_enum_section():
    if not enum_defs:
        return ''
    parts = ['<div class="enum-section">', '<h2>Enum Definitions</h2>']
    for name, defn in enum_defs.items():
        anchor = f'enum-{name}'
        pills  = ''.join(
            f'<span class="enum-value">{esc(v)}</span>'
            for v in defn['values']
        )
        parts.append(
            f'<div class="enum-block" id="{anchor}">\n'
            f'  <div class="enum-name">{esc(name)}</div>\n'
            f'  <div class="enum-desc">{esc(defn["description"])}</div>\n'
            f'  <div class="enum-values">{pills}</div>\n'
            f'</div>'
        )
    parts.append('</div>')
    return '\n'.join(parts)

# ---------------------------------------------------------------------------
# Build a styled valid-values <td> from a raw valid_values value
# ($EnumName -> linked pill, empty -> empty cell)
# ---------------------------------------------------------------------------
def make_valid_td(raw_value):
    raw = raw_value.strip()
    if raw.startswith('$'):
        enum_name = raw[1:]
        anchor    = f'enum-{enum_name}'
        return (f'<td class="valid-values-col">'
                f'<a class="enum-link" href="#{anchor}" '
                f'title="See enum definition">{esc(enum_name)}</a>'
                f'</td>')
    elif raw and '|' in raw:
        # inline pipe-separated enum — show values directly
        anchor = f'enum-inline-{re.sub(r"[^a-zA-Z0-9]", "-", raw)}'
        return (f'<td class="valid-values-col">'
                f'<a class="enum-link" href="#{anchor}" '
                f'title="See valid values">{esc(raw)}</a>'
                f'</td>')
    return '<td class="valid-values-col"></td>'

# ---------------------------------------------------------------------------
# Process HTML line by line
#
# Strategy: buffer each <tr>...</tr>. In each row find the last <td> (the
# raw valid_values column) and replace it with a styled cell derived from
# its content. Replace the <th>valid_values</th> header with our styled one.
#
# Handles pandoc's <tr class="odd">, <tr class="even">, <tr class="header">
# ---------------------------------------------------------------------------
def process_html(html_text):
    out_lines   = []
    in_thead    = False
    in_tbody    = False
    in_tr       = False
    tr_lines    = []

    def flush_tr(buffered):
        """Replace the last <td> in a buffered row with a styled valid-values cell."""
        # Find the last line that is a <td>
        last_td_idx = None
        for i in range(len(buffered) - 1, -1, -1):
            if buffered[i].strip().startswith('<td'):
                last_td_idx = i
                break

        if last_td_idx is None:
            return buffered

        # Extract raw value from the last td
        m = re.match(r'(\s*<td[^>]*>)(.*?)(</td>)', buffered[last_td_idx], re.DOTALL)
        raw_value = m.group(2).strip() if m else ''

        result = []
        for i, bl in enumerate(buffered):
            if i == last_td_idx:
                result.append(make_valid_td(raw_value))
            else:
                result.append(bl)
        return result

    for line in html_text.splitlines():
        stripped = line.strip()

        # Section markers
        if stripped == '<thead>':
            in_thead = True
            out_lines.append(line)
            continue
        if stripped == '</thead>':
            in_thead = False
            out_lines.append(line)
            continue
        if stripped == '<tbody>':
            in_tbody = True
            out_lines.append(line)
            continue
        if stripped == '</tbody>':
            in_tbody = False
            out_lines.append(line)
            continue

        # thead: replace the valid_values <th> with our styled header
        if in_thead:
            if re.search(r'<th[^>]*>\s*valid_values\s*</th>', stripped, re.IGNORECASE):
                out_lines.append('<th class="valid-values-col">valid values</th>')
            else:
                out_lines.append(line)
            continue

        # tbody: buffer rows and flush with replaced last td
        if in_tbody:
            # Match any <tr ...> opening — pandoc adds class="odd"/"even"
            if re.match(r'<tr\b', stripped):
                in_tr    = True
                tr_lines = [line]
                continue

            if in_tr:
                tr_lines.append(line)
                if stripped == '</tr>':
                    in_tr = False
                    for fl in flush_tr(tr_lines):
                        out_lines.append(fl)
                    tr_lines = []
                continue

        out_lines.append(line)

    return '\n'.join(out_lines)


# ---------------------------------------------------------------------------
# Apply transformations
# ---------------------------------------------------------------------------
result = raw_html

# 1. Inject CSS before </head>
result = result.replace('</head>', INJECTED_CSS + '</head>', 1)

# 2. Insert enum section before the first <table — no <hr /> in newer pandoc
enum_html = build_enum_section()
if enum_html:
    result = result.replace('<table', enum_html + '\n<table', 1)

# 3. Replace valid_values column with styled valid values column
result = process_html(result)

with open(out_path, 'w', encoding='utf-8') as f:
    f.write(result)

n_links = result.count('class="enum-link"')
print(f"Written {out_path}")
print(f"  {len(enum_defs)} enum definitions, {n_links} valid-values cells linked")
