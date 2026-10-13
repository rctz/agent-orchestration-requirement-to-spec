#!/usr/bin/env python3
"""SR13 helper: dump the probes-row annotation segments for the rev13/rev14
probe cites + verify SR12-F-01 fold claims (58/59 annotated HISTORICAL since
the v14 rollover, 67 named as live re-proof, battery named)."""
import glob, os, re
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
spec = sorted(glob.glob('spec/*-spec-v*.md'))[-1]
text = open(spec).read()
header = text[:text.index('# 1. Overview')]
row = [l for l in header.split('\n') if l.startswith('| probes |')][0]

for needle in ['58-rev13', '59-rev13', '66-rev14', '67-rev14']:
    for m in re.finditer(re.escape(needle), row):
        s = max(0, m.start() - 40)
        print(f'--- {needle} @{m.start()}:')
        print(row[s:m.end() + 380].replace('\n', ' '))
        print()

print('68/69/70 in probes row:', [n for n in ('68-rev14','69-rev14','70-rev14') if n in row])
print('68/69/70 in header:', [n for n in ('68-rev14','69-rev14','70-rev14') if n in header])
print('battery sentence in header:', 'living battery' in header)

# Spot-verify the re-proof claims: 58 hardcodes spec/13? 59 hardcodes spec/13?
for f in ['appendix/58-rev13-sr11-folds-probes.py', 'appendix/59-rev13-gate-reaim.py']:
    src = open(f).read()
    pinned = re.findall(r'spec/1[0-9]-spec-v1[0-9]\.md', src)
    print(f, 'hardcodes:', sorted(set(pinned)))
