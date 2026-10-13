import sys
t = open('spec/12-spec-v12.md', encoding='utf-8').read()
out = []
for name, pat in [('T-C8', 'T-C8 | write-phase failures'), ('T-C16', 'T-C16 | E-MEM fault form')]:
    i = t.find(pat)
    if i < 0:
        out.append(name + ' NOT FOUND')
        continue
    j = t.find('\n', i)
    out.append('===== ' + name + ' (chars %d..%d) =====' % (i, j))
    row = t[i:j]
    # wrap at 200 chars for readability
    for k in range(0, len(row), 200):
        out.append(row[k:k+200])
open('appendix/55b-extract-tc8-tc16.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('written', sum(len(x) for x in out))
