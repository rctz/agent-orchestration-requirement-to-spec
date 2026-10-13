#!/usr/bin/env python3
"""SR13: print the full probes row in numbered slices for exact reading."""
import glob, os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
spec = sorted(glob.glob('spec/*-spec-v*.md'))[-1]
text = open(spec).read()
header = text[:text.index('# 1. Overview')]
row = [l for l in header.split('\n') if l.startswith('| probes |')][0]
CH = 1900
for i in range(0, len(row), CH):
    print(f'===== slice {i//CH} [{i}:{i+CH}] =====')
    print(row[i:i+CH])
