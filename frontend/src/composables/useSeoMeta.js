import { useHead } from '@unhead/vue'
import { computed, unref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { baseRouteName } from '../router'

// Defined once in vite.config.js (shared with the sitemap generator so
// the two can't disagree) — still a placeholder until deployment
// happens for real (see README/CLAUDE.md); canonical/OG/hreflang URLs
// are meaningless against a placeholder domain, so this must be updated
// before relying on any of this for actual search-engine indexing.
const SITE_URL = __SITE_URL__
const SITE_NAME = 'Underlaid'
// No dedicated static OG image exists yet (only frontend/public/favicon.svg) —
// falls back to the favicon so the tag isn't simply missing, but a real
// 1200x630 social-preview image should replace this before launch.
const DEFAULT_OG_IMAGE = `${SITE_URL}/favicon.svg`

/**
 * Per-route <head> metadata: title, description, OG/Twitter tags,
 * canonical link, and reciprocal hreflang alternates (en/fr/x-default).
 *
 * @param {{en: string, fr: string} | (() => {en: string, fr: string})} title
 * @param {{en: string, fr: string} | (() => {en: string, fr: string})} description
 * @param {string} [image] absolute or root-relative image URL
 * @param {(locale: string) => object} [jsonLd] schema.org object per locale, if this page has one
 */
export function useSeoMeta({ title, description, image, jsonLd }) {
  const { locale } = useI18n()
  const route = useRoute()
  const router = useRouter()

  const base = computed(() => baseRouteName(route.name))
  const enPath = computed(() => router.resolve({ name: base.value }).fullPath)
  const frPath = computed(() => router.resolve({ name: `${base.value}-fr` }).fullPath)
  const selfPath = computed(() => (locale.value === 'fr' ? frPath.value : enPath.value))

  const resolvedTitle = computed(() => {
    const value = typeof title === 'function' ? title() : title
    const localized = unref(value)
    return `${localized[locale.value]} | ${SITE_NAME}`
  })
  const resolvedDescription = computed(() => {
    const value = typeof description === 'function' ? description() : description
    const localized = unref(value)
    return localized[locale.value]
  })
  const resolvedImage = computed(() => image || DEFAULT_OG_IMAGE)
  const selfUrl = computed(() => `${SITE_URL}${selfPath.value}`)

  useHead({
    title: resolvedTitle,
    htmlAttrs: { lang: locale },
    meta: [
      { name: 'description', content: resolvedDescription },
      { property: 'og:site_name', content: SITE_NAME },
      { property: 'og:title', content: resolvedTitle },
      { property: 'og:description', content: resolvedDescription },
      { property: 'og:type', content: 'website' },
      { property: 'og:url', content: selfUrl },
      { property: 'og:image', content: resolvedImage },
      { property: 'og:locale', content: computed(() => (locale.value === 'fr' ? 'fr_FR' : 'en_US')) },
      { property: 'og:locale:alternate', content: computed(() => (locale.value === 'fr' ? 'en_US' : 'fr_FR')) },
      { name: 'twitter:card', content: 'summary_large_image' },
      { name: 'twitter:title', content: resolvedTitle },
      { name: 'twitter:description', content: resolvedDescription },
      { name: 'twitter:image', content: resolvedImage },
    ],
    link: [
      { rel: 'canonical', href: selfUrl },
      { rel: 'alternate', hreflang: 'en', href: computed(() => `${SITE_URL}${enPath.value}`) },
      { rel: 'alternate', hreflang: 'fr', href: computed(() => `${SITE_URL}${frPath.value}`) },
      { rel: 'alternate', hreflang: 'x-default', href: computed(() => `${SITE_URL}${enPath.value}`) },
    ],
    script: jsonLd
      ? [
          {
            type: 'application/ld+json',
            innerHTML: computed(() => JSON.stringify(jsonLd(locale.value))),
          },
        ]
      : [],
  })
}

export { SITE_URL, SITE_NAME }
