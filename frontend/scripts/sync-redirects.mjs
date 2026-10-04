// Writes the permanent redirects of the pre-redesign addresses into
// vercel.json, from src/routePaths.js (single source). Vercel reads
// vercel.json before the build, so the file is committed, not generated at
// build time: run `node scripts/sync-redirects.mjs` after changing a page
// address; the smoke test fails if the two disagree (`--check`).
import { readFileSync, writeFileSync } from 'fs'
import { paramRewrites, vercelRedirects } from '../src/routePaths.js'

const path = new URL('../vercel.json', import.meta.url)
const config = JSON.parse(readFileSync(path, 'utf-8'))
const expected = vercelRedirects()
const rewrites = paramRewrites()
if (process.argv.includes('--check')) {
  const same = JSON.stringify(config.redirects || []) === JSON.stringify(expected) && JSON.stringify(config.rewrites || []) === JSON.stringify(rewrites)
  console.log(same ? 'vercel.json redirects up to date' : 'vercel.json redirects out of date: run node scripts/sync-redirects.mjs')
  process.exit(same ? 0 : 1)
}
config.redirects = expected
config.rewrites = rewrites
writeFileSync(path, JSON.stringify(config, null, 2) + '\n')
console.log(`${expected.length} redirects and ${rewrites.length} rewrites written`)
