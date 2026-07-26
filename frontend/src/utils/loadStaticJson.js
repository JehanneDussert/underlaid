// Loads a JSON file from public/ the same way in both environments this
// app runs in: a real fetch() in the browser (dev server or a deployed
// static host), and a direct filesystem read during vite-ssg's build-time
// prerendering (a Node process with no HTTP server to fetch from — the
// build hasn't been written to disk yet at that point, only public/ exists
// on disk). Without this split, a page whose content depends on this data
// (the /ranking list, the home page's screen-reader IRIS table) would
// prerender as an empty shell, defeating the whole point of prerendering.
export async function loadStaticJson(publicPath) {
  if (import.meta.env.SSR) {
    const { readFileSync } = await import('fs')
    const { fileURLToPath } = await import('url')
    const path = fileURLToPath(new URL(`../../public${publicPath}`, import.meta.url))
    return JSON.parse(readFileSync(path, 'utf-8'))
  }
  const response = await fetch(publicPath)
  return response.json()
}
