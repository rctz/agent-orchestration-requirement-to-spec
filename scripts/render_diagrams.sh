#!/usr/bin/env bash
# Render every ```mermaid block of a markdown doc to PNG (plan §6).
#
# Usage: scripts/render_diagrams.sh <doc.md> [outdir]
#   <doc.md>  markdown file containing ```mermaid fenced blocks
#   [outdir]  output dir (default: <docdir>/req3-diagrams)
#
# Behaviour:
# - Blocks are extracted in document order by an inline python3 script.
# - PNG names are NN-<slug>.png; slugs come from the ordered list below so
#   the existing files in ~/kaizen/design/req3-diagrams keep their names.
#   If the block count no longer matches the list, the script warns on
#   stderr and extra blocks fall back to plain NN.png — update the list
#   when diagrams are added or removed.
# - Renderer: npx -y -p @mermaid-js/mermaid-cli mmdc, system chromium
#   (--no-sandbox), scale 2. PUPPETEER_SKIP_DOWNLOAD=1 — we never use the
#   bundled chromium.
# - Rendering goes to a temp dir first; the old PNGs are replaced only when
#   ALL blocks rendered. Any error exits non-zero (fails the milestone).
set -euo pipefail

DOC="${1:?usage: render_diagrams.sh <doc.md> [outdir]}"
[ -f "$DOC" ] || { echo "error: doc not found: $DOC" >&2; exit 1; }
OUT="${2:-$(dirname "$DOC")/req3-diagrams}"
CHROMIUM="${CHROMIUM:-/usr/bin/chromium}"
[ -x "$CHROMIUM" ] || { echo "error: chromium not executable: $CHROMIUM" >&2; exit 1; }
command -v npx >/dev/null || { echo "error: npx not found" >&2; exit 1; }
mkdir -p "$OUT"
TMP="$(mktemp -d "$OUT/.render.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

# Ordered slugs for req3-design.md §2A (block index -> file name part).
SLUGS="component state-top state-requirement state-spec seq-happy seq-expiry flow-repo flow-review deployment module-deps"

export PUPPETEER_SKIP_DOWNLOAD=1

python3 - "$DOC" "$TMP" $SLUGS <<'PYEOF'
import sys
from pathlib import Path

doc, tmp = Path(sys.argv[1]), Path(sys.argv[2])
slugs = sys.argv[3:]
blocks, cur = [], None
for ln in doc.read_text(encoding="utf-8").splitlines():
    if cur is None:
        if ln.strip().startswith("```mermaid"):
            cur = []
    elif ln.strip() == "```":
        blocks.append(cur)
        cur = None
    else:
        cur.append(ln)
if cur is not None:
    sys.exit("error: unterminated mermaid block")
if not blocks:
    sys.exit("error: no mermaid blocks found")
for i, b in enumerate(blocks):
    n = f"{i:02d}"
    slug = slugs[i] if i < len(slugs) else ""
    (tmp / f"{n}{('-' + slug) if slug else ''}.mmd").write_text(
        "\n".join(b) + "\n", encoding="utf-8")
print(f"extracted {len(blocks)} mermaid block(s)")
if len(blocks) != len(slugs):
    print(f"warning: block count {len(blocks)} != slug list {len(slugs)}; "
          "extras fall back to plain NN names — update SLUGS", file=sys.stderr)
PYEOF

cat > "$TMP/puppeteer.json" <<JEOF
{"executablePath": "$CHROMIUM", "args": ["--no-sandbox"]}
JEOF

cd "$TMP"
for mmd in *.mmd; do
  png="${mmd%.mmd}.png"
  echo "render $mmd -> $OUT/$png"
  npx -y -p @mermaid-js/mermaid-cli mmdc -p puppeteer.json -i "$mmd" -o "$png" -s 2
done

for png in *.png; do mv -f "$png" "$OUT/$png"; done
echo "OK: $(find "$OUT" -maxdepth 1 -name '*.png' | wc -l) png file(s) in $OUT"
