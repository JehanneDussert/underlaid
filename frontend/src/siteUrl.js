// The site's public address, single source (decided 2026-10-04: the
// project's own domain, underlaid.fr). Read by vite.config.js (canonical,
// hreflang, sharing images, JSON-LD, sitemap, robots) and by
// scripts/sync-redirects.mjs (permanent redirect from the old Vercel
// address). A fork deployed elsewhere overrides it with SITE_URL=... at
// build time. No trailing slash.
export const DEFAULT_SITE_URL = 'https://underlaid.fr'
// Former address, redirected to DEFAULT_SITE_URL (same path).
export const LEGACY_HOST = 'underlaid.vercel.app'
