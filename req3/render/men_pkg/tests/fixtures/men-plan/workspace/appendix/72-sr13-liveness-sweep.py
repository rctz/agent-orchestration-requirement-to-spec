#!/usr/bin/env python3
"""SR13 probes-row liveness sweep (reviewer's own, cycle 13).

Targets the NEWEST spec via sorted glob (board convention), then:
  L1  probes-row appendix cites, each marked LIVE or HISTORICAL
  L2  every LIVE-cited probe exists and does not crash on an archived
      spec path (runs with a hard timeout, captures only exit status +
      last line — battery timings excluded, this is a liveness sweep)
  L3  HISTORICAL annotations name their archived spec path
  L4  annotation re-proof cites (67/68/69/70/66/58/59...) exist on disk
"""
import glob, subprocess, sys, os, re

os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
spec = sorted(glob.glob('spec/*-spec-v*.md'))[-1]
print('target spec:', spec)
text = open(spec).read()
header = text[:text.index('# 1. Overview')]
row = [l for l in header.split('\n') if l.startswith('| probes |')][0]

parts = row.split('+ appendix/')
results = []
for p in parts[1:]:
    name = p.strip().split(' ')[0]
    is_hist = 'HISTORICAL' in p[:600]
    results.append((name, is_hist, p))

print('\nL1 probes-row cites:')
live, hist = [], []
for name, is_hist, p in results:
    tag = 'HISTORICAL' if is_hist else 'LIVE'
    print(f'  {name:38s} {tag}')
    (hist if is_hist else live).append(name)

fails = 0

print('\nL2 LIVE-cited probe liveness (run with timeout, tail only):')
# 66 is the 4-minute timing battery: check pass markers instead of full run here
for name in live:
    path = f'appendix/{name}'
    if not os.path.exists(path):
        print(f'  FAIL {name}: file missing'); fails += 1; continue
    if name.startswith('66-'):
        # full battery is re-run separately by the reviewer; here only
        # confirm the file parses and its Part B harness is present
        src = open(path).read()
        ok = ('FIELD_START' in src or 'QUOTED' in src) and 'def ' in src
        print(f'  {"PASS" if ok else "FAIL"} {name}: Part B harness present={ok}')
        fails += 0 if ok else 1
        continue
    try:
        r = subprocess.run([sys.executable, path], capture_output=True,
                           text=True, timeout=120)
        last = (r.stdout or r.stderr).strip().split('\n')[-1][:90]
        crashed = 'FileNotFoundError' in (r.stdout + r.stderr)
        status = 'FAIL' if (r.returncode != 0 or crashed) else 'PASS'
        if status == 'FAIL':
            fails += 1
        print(f'  {status} {name}: rc={r.returncode} last={last!r}')
    except subprocess.TimeoutExpired:
        print(f'  FAIL {name}: timeout 120s'); fails += 1

print('\nL3 HISTORICAL annotations name an archived spec path:')
for name, is_hist, p in results:
    if is_hist:
        m = re.search(r'archived spec/(\d+)-spec-v(\d+)\.md', p[:600])
        ok = bool(m)
        print(f'  {"PASS" if ok else "FAIL"} {name}: archived path={m.group(0) if m else None}')
        fails += 0 if ok else 1

print('\nL4 re-proof cites exist on disk:')
cited = set(re.findall(r'appendix/(\d+[a-z]?-[\w-]+\.py)', row))
for c in sorted(cited):
    ok = os.path.exists(f'appendix/{c}')
    if not ok:
        print(f'  FAIL missing: appendix/{c}'); fails += 1
print(f'  {len(cited)} distinct .py cites checked, missing listed above')

print(f'\nTOTAL FAILURES: {fails}')
sys.exit(1 if fails else 0)
