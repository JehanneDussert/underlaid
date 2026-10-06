#!/usr/bin/env bash
# Lighthouse report (performance, accessibility, best practices, SEO) on the
# main pages of the built site, phone and desktop (block 5). Run from
# frontend/ after `npm run build`:
#
#   bash scripts/lighthouse-report.sh
#
# Serves dist/ with the Vite preview server, runs Lighthouse with
# Playwright's Chromium, writes ../docs/lighthouse.md (scores; the JSON
# reports go to dist-lighthouse/, not versioned).
#
# LIGHTHOUSE_BASE_URL=https://underlaid.fr runs against that site instead
# of a local build (weekly workflow); LIGHTHOUSE_OUT changes the report path.
set -u
PORT=4372
BASE="${LIGHTHOUSE_BASE_URL:-}"
REPORT="${LIGHTHOUSE_OUT:-../docs/lighthouse.md}"
PAGES=(/ /quartier/930290101 /carte /methode /a-propos /lieux-du-quotidien /quartiers-les-plus-exposes /en)
OUT=dist-lighthouse
mkdir -p "$OUT"
if [ -z "$BASE" ]; then
BASE="http://localhost:$PORT"
node -e "import('vite').then(v=>v.preview({root:process.cwd(),preview:{port:$PORT}})).then(()=>setInterval(()=>{},1e9))" >/dev/null 2>&1 &
SERVER=$!
trap 'kill $SERVER 2>/dev/null' EXIT
for i in $(seq 1 30); do curl -s -o /dev/null "$BASE/" && break; sleep 1; done
SOURCE="Site construit localement (\`npm run build\`), servi par le serveur de prévisualisation de Vite, sans compression ; Lighthouse avec le Chromium de Playwright. En ligne (Vercel : compression, CDN), la performance est en principe meilleure."
else
SOURCE="Site en ligne ($BASE) ; Lighthouse avec le Chromium de Playwright, depuis un serveur de GitHub Actions."
fi
export CHROME_PATH="$(node -e "console.log(require('playwright').chromium.executablePath())")"
ROWS=""
for form in mobile desktop; do
  for path in "${PAGES[@]}"; do
    file="$OUT/${form}$(echo "$path" | tr '/' '_').json"
    extra=""
    [ "$form" = desktop ] && extra="--preset=desktop"
    npx -y lighthouse "$BASE$path" --quiet --output=json --output-path="$file" \
      --only-categories=performance,accessibility,best-practices,seo --chrome-flags="--headless=new --no-sandbox" $extra >/dev/null 2>&1
    row=$(python -c "
import json,sys
try:
    c=json.load(open('$file'))['categories']
    s=lambda k: '' if c[k]['score'] is None else str(round(c[k]['score']*100))
    print('| $form | $path | '+' | '.join(s(k) for k in ['performance','accessibility','best-practices','seo'])+' |')
except Exception:
    print('| $form | $path | erreur | | | |')
")
    echo "$row"
    ROWS="$ROWS$row"$'\n'
  done
done
cat > "$REPORT" <<EOF
# Lighthouse — rapport du $(date +%Y-%m-%d)

$SOURCE

| Format | Page | Performance | Accessibilité | Bonnes pratiques | Référencement |
|---|---|---|---|---|---|
$ROWS
EOF
echo "wrote $REPORT"
