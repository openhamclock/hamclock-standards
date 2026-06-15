#!/usr/bin/env python3
# Copyright 2026 Open HamClock Standards
# SPDX-License-Identifier: Apache-2.0

"""
Generate hamclock-openapi.yaml from api-doc.md

Supports:
  - HTML comment enum definitions:
      <!-- ENUM DEFINITIONS
           enum:ModeEnum=3|13|17|19|38  # description
      -->
  - valid_values column (10th column) in the table:
      $EnumName   -> $ref to components/parameters/<EnumName>_<ArgName>
      a|b|c       -> inline enum in schema
      (empty)     -> type inferred from samples, no enum constraint
"""

import re
import sys
import yaml


def parse_md(md_file):
    """Parse api-doc.md returning (enum_defs, entries)."""
    enum_defs = {}   # name -> {'values': [str,...], 'description': str}
    entries   = []

    with open(md_file) as f:
        content = f.read()
        lines   = content.splitlines()

    # Parse enum definitions from HTML comment block
    enum_block = re.search(
        r'<!--\s*ENUM DEFINITIONS.*?-->', content, re.DOTALL)
    if enum_block:
        for line in enum_block.group().splitlines():
            m = re.match(r'\s*enum:(\w+)=([^#]+?)(?:\s+required=(\w*))?\s*(?:#\s*(.*))?$', line)
            if m:
                name   = m.group(1).strip()
                values = [v.strip() for v in m.group(2).strip().split('|')]
                req    = (m.group(3) or 'no').strip().lower() == 'yes'
                desc   = (m.group(4) or '').strip()
                enum_defs[name] = {'values': values, 'description': desc, 'required': req}

    # Parse table rows
    table_start    = False
    header_skipped = False
    for line in lines:
        line_s = line.strip()
        if line_s == '---':
            table_start = True
            continue
        if table_start and line_s.startswith('|'):
            if not header_skipped:
                header_skipped = True
                continue
            if ':---' in line_s:
                continue
            parts = [p.strip() for p in line_s.split('|')[1:-1]]
            # Support both 9-column (original) and 10-column (with valid_values)
            if len(parts) == 9:
                parts.append('')
            if len(parts) == 10:
                path, arg, units, min_, max_, default, required, samples, proposal, valid_values = parts
                entries.append({
                    'path': path, 'arg': arg, 'units': units,
                    'min': min_, 'max': max_, 'default': default,
                    'required': required, 'samples': samples,
                    'proposal': proposal, 'valid_values': valid_values,
                })

    return enum_defs, entries


def is_numeric_str(s):
    """Return True if s looks like a number."""
    return bool(s) and s.replace('.','',1).replace('-','',1).isdigit()


def infer_type(entry):
    """Infer 'number' or 'string' from samples, default, min, and max fields."""
    # Check samples first
    samples = entry.get('samples','')
    if samples:
        vals = [v.strip() for v in samples.split(',')][:3]
        if all(is_numeric_str(v) for v in vals if v):
            return 'number'
    # Fall back to checking default/min/max
    for field in ('default', 'min', 'max'):
        v = entry.get(field, '').strip()
        if v and is_numeric_str(v):
            return 'number'
    return 'string'


def cast_numeric(s):
    """Cast string to int or float; return original string if not numeric."""
    try:
        return float(s) if '.' in s else int(s)
    except (ValueError, TypeError):
        return s


def build_schema(entry, enum_defs):
    """Build a parameter schema dict from an entry."""
    valid = entry['valid_values']
    schema = {}
    param_type = infer_type(entry)

    if valid.startswith('$'):
        enum_name = valid[1:]
        if enum_name in enum_defs:
            raw_vals = enum_defs[enum_name]['values']
            typed = [cast_numeric(v) for v in raw_vals]
            schema['type'] = 'number' if all(isinstance(v,(int,float)) for v in typed) else 'string'
            schema['enum'] = typed
        else:
            schema['type'] = param_type
    elif '|' in valid:
        raw_vals = [v.strip() for v in valid.split('|')]
        typed = [cast_numeric(v) for v in raw_vals]
        schema['type'] = 'number' if all(isinstance(v,(int,float)) for v in typed) else 'string'
        schema['enum'] = typed
    else:
        schema['type'] = param_type

    # default must match the schema type
    if entry['default']:
        d = cast_numeric(entry['default'])
        if schema['type'] == 'number' and isinstance(d, str):
            pass   # non-numeric default for numeric param — skip
        else:
            schema['default'] = d

    if entry['min']:
        v = cast_numeric(entry['min'])
        if isinstance(v, (int, float)):
            schema['minimum'] = v

    if entry['max']:
        v = cast_numeric(entry['max'])
        if isinstance(v, (int, float)):
            schema['maximum'] = v

    return schema


def build_components(enum_defs, entries):
    """
    Build components/parameters for any (EnumName, ArgName) pair
    that appears in 2+ paths — these become $ref targets.
    Returns dict of component parameter defs.
    """
    # Count uses of each (enum_ref, arg_name) pair
    from collections import Counter
    usage = Counter()
    for e in entries:
        if e['arg'] and e['valid_values'].startswith('$'):
            usage[(e['valid_values'][1:], e['arg'])] += 1

    components = {}
    for (enum_name, arg_name), count in usage.items():
        if count >= 1 and enum_name in enum_defs:
            defn = enum_defs[enum_name]
            raw_vals = defn['values']
            typed = []
            for v in raw_vals:
                try:
                    typed.append(float(v) if '.' in v else int(v))
                except ValueError:
                    typed.append(v)
            comp_key = f'{enum_name}_{arg_name}'
            components[comp_key] = {
                'name': arg_name,
                'in': 'query',
                'description': defn['description'],
                'required': defn.get('required', False),
                'schema': {
                    'type': 'number' if all(isinstance(v,(int,float)) for v in typed) else 'string',
                    'enum': typed,
                }
            }
    return components


def generate_openapi(md_file, output_file):
    enum_defs, entries = parse_md(md_file)
    components         = build_components(enum_defs, entries)

    # Group entries by path
    paths         = {}
    current_path  = None
    params        = []
    path_proposals= {}

    for entry in entries:
        if entry['path']:
            if current_path:
                paths[current_path] = {
                    'parameters': params,
                    'proposal':   path_proposals.get(current_path, ''),
                }
                params = []
            current_path = entry['path']
            if entry['proposal']:
                path_proposals[current_path] = entry['proposal']

        if entry['arg']:
            valid    = entry['valid_values']
            # Data row required overrides enum default: yes=required, no/empty=not required
            row_required_str = entry['required'].strip().lower()
            if row_required_str == 'yes':
                required = True
            elif row_required_str == 'no':
                required = False
            else:
                required = False   # empty = not required

            if valid.startswith('$'):
                enum_name = valid[1:]
                comp_key  = f'{enum_name}_{entry["arg"]}'
                if comp_key in components:
                    if not required:
                        # Not required — use $ref (keeps yaml small)
                        params.append({'$ref': f'#/components/parameters/{comp_key}'})
                        continue
                    else:
                        # Required — must inline since $ref siblings ignored in OAS 3.0
                        comp_defn = components[comp_key]
                        param = {
                            'name':        comp_defn['name'],
                            'in':          'query',
                            'required':    True,
                            'description': comp_defn.get('description', ''),
                            'schema':      comp_defn['schema'],
                        }
                        params.append(param)
                        continue
            # Inline parameter (no enum ref)
            param = {
                'name':     entry['arg'],
                'in':       'query',
                'required': required,
                'schema':   build_schema(entry, enum_defs),
            }
            if entry['units']:
                param['description'] = f'Units: {entry["units"]}'
            params.append(param)

    if current_path:
        paths[current_path] = {
            'parameters': params,
            'proposal':   path_proposals.get(current_path, ''),
        }

    # ── Tag assignment ────────────────────────────────────────────────────
    def get_tag(path):
        if '/SDO/' in path:              return 'SDO Images'
        if '/maps/' in path:             return 'Maps'
        if any(x in path for x in ['/solar-','/Bz/','/NOAASpaceWX/','/ssn/','/xray/','/solar-wind/']):
            return 'Solar Weather'
        if '/geomag/' in path or '/dst/' in path: return 'Geomagnetic'
        if any(x in path for x in ['fetchVOACAP','fetchBandConditions']):
            return 'Propagation'
        if any(x in path for x in ['Reporter','RBN','WSPR']):
            return 'Reporters'
        if '/wx' in path or '/worldwx/' in path:  return 'Weather'
        if '/esats/' in path:            return 'Satellites'
        return 'Miscellaneous'

    # ── Build OpenAPI spec ─────────────────────────────────────────────────
    openapi_spec = {
        'openapi': '3.0.3',
        'info': {
            'title':       'HamClock API',
            'description': 'API endpoints for HamClock — a real-time amateur radio clock and propagation display application.',
            'version':     '1.0.0',
            'license':  {'name': 'CC BY-ND 4.0', 'url': 'https://creativecommons.org/licenses/by-nd/4.0/'},
            'contact':  {'name': 'HamClock', 'url': 'https://www.clearskyinstitute.com/ham/HamClock/'},
        },
        'servers': [
            {'url': 'http://clearskyinstitute.com', 'description': 'Clear Sky Institute (primary)'},
            {'url': 'http://ohb.hamclock.app',      'description': 'OHB HamClock instance'},
            {'url': 'http://hamclock.com',           'description': 'HamClock.com'},
        ],
        'tags': [
            {'name': 'Solar Weather',  'description': 'Solar flux, X-ray, Bz, solar wind, and space weather data'},
            {'name': 'Geomagnetic',    'description': 'Geomagnetic indices including K-index and DST'},
            {'name': 'Propagation',    'description': 'HF band condition and MUF prediction scripts'},
            {'name': 'Reporters',      'description': 'PSK Reporter, RBN, and WSPR spot data'},
            {'name': 'Maps',           'description': 'Day and night map overlays at various resolutions'},
            {'name': 'SDO Images',     'description': 'Solar Dynamics Observatory solar imagery'},
            {'name': 'Satellites',     'description': 'Satellite tracking data'},
            {'name': 'Weather',        'description': 'World weather and local weather data'},
            {'name': 'Miscellaneous',  'description': 'Contests, DXpeditions, city data, version info, and more'},
        ],
        'paths': {},
    }

    for path, data in paths.items():
        desc = 'Standard HamClock API endpoint.'
        if data['proposal']:
            desc = f"Proposal implementation: {data['proposal']}."

        openapi_spec['paths'][path] = {
            'get': {
                'tags':        [get_tag(path)],
                'summary':     path.split('/')[-1],
                'description': desc,
                'parameters':  data['parameters'],
                'responses': {
                    '200': {
                        'description': 'Success',
                        'content': {'text/plain': {'schema': {'type': 'string'}}},
                    }
                },
            }
        }

    # components/parameters block
    if components:
        openapi_spec['components'] = {
            'parameters': components
        }

    # Use a custom dumper that ignores anchors/aliases so PyYAML doesn't
    # emit &id001/*id001 — Swagger Editor handles expanded yaml better.
    class NoAliasDumper(yaml.Dumper):
        def ignore_aliases(self, data):
            return True

    with open(output_file, 'w') as f:
        yaml.dump(openapi_spec, f, Dumper=NoAliasDumper,
                  default_flow_style=False, sort_keys=False, allow_unicode=True)

    print(f"Written {output_file}")
    print(f"  {len(paths)} paths, {len(components)} reusable component parameters")
    if enum_defs:
        print(f"  Enum definitions: {', '.join(enum_defs.keys())}")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: python3 md-to-openapi.py <api-doc.md> <hamclock-openapi.yaml>')
        sys.exit(1)
    generate_openapi(sys.argv[1], sys.argv[2])
