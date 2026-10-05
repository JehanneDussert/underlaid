import { useHead } from '@unhead/vue'
import { computed, unref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { baseRouteName } from '../router'

// Defined once in vite.config.js (shared with the sitemap/robots
// generator so the two can't disagree).
const SITE_URL = __SITE_URL__
const SITE_NAME = 'Underlaid'
// Preview and development builds must never be indexed (vite.config.js).
const NOINDEX = __NOINDEX__
// 1200x630 PNG sharing images in the site's identity (validated on
// 5 October 2026), one per main page and language, made by
// scripts/make-share-images.mjs into public/share/. Other pages use the home
// page's; a neighbourhood page passes its own (made on request, api/og.js).
const SHARE_ALT = {
  accueil: { fr: 'Underlaid : une même ville, des conditions de vie inégales', en: 'Underlaid: one city, unequal living conditions' },
  carte: { fr: 'Underlaid : explorer la carte des 2 752 quartiers de Paris et de la petite couronne', en: 'Underlaid: explore the map of the 2,752 neighbourhoods of Paris and its inner suburbs' },
  methode: { fr: 'Underlaid : sources et méthode', en: 'Underlaid: sources and method' },
  apropos: { fr: 'Underlaid : à propos du projet', en: 'Underlaid: about the project' },
}
const shareImage = (key, lang) => ({ url: `${SITE_URL}/share/${key}-${lang}.png`, alt: SHARE_ALT[key][lang] })
const OG_IMAGE_WIDTH = '1200'
const OG_IMAGE_HEIGHT = '630'

/**
 * Per-route <head> metadata: title, description, OG/Twitter tags,
 * canonical link, and reciprocal hreflang alternates (fr/en; x-default = French).
 *
 * @param {{en: string, fr: string} | (() => {en: string, fr: string})} title
 * @param {{en: string, fr: string} | (() => {en: string, fr: string})} description
 * @param {string | (() => {url: string, alt: string} | null)} [image] key of a page image
 *   ('accueil', 'carte', 'methode', 'apropos'), or a function giving a specific image
 * @param {(locale: string) => object} [jsonLd] schema.org object per locale, if this page has one
 */
export function useSeoMeta({ title, description, image, jsonLd }) {
  const { locale } = useI18n()
  const route = useRoute()
  const router = useRouter()

  const base = computed(() => baseRouteName(route.name))
  // Params kept (a neighbourhood page has the same code in both languages).
  const frPath = computed(() => router.resolve({ name: base.value, params: route.params }).fullPath)
  const enPath = computed(() => router.resolve({ name: `${base.value}-en`, params: route.params }).fullPath)
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
  const resolvedShare = computed(() => {
    const own = typeof image === 'function' ? image() : null
    if (own) return own
    return shareImage(typeof image === 'string' && SHARE_ALT[image] ? image : 'accueil', locale.value === 'en' ? 'en' : 'fr')
  })
  const resolvedImage = computed(() => resolvedShare.value.url)
  const resolvedImageAlt = computed(() => resolvedShare.value.alt)
  const selfUrl = computed(() => `${SITE_URL}${selfPath.value}`)

  useHead({
    title: resolvedTitle,
    htmlAttrs: { lang: locale },
    meta: [
      ...(NOINDEX ? [{ name: 'robots', content: 'noindex, nofollow' }] : []),
      { name: 'description', content: resolvedDescription },
      { property: 'og:site_name', content: SITE_NAME },
      { property: 'og:title', content: resolvedTitle },
      { property: 'og:description', content: resolvedDescription },
      { property: 'og:type', content: 'website' },
      { property: 'og:url', content: selfUrl },
      { property: 'og:image', content: resolvedImage },
      { property: 'og:image:type', content: 'image/png' },
      { property: 'og:image:width', content: OG_IMAGE_WIDTH },
      { property: 'og:image:height', content: OG_IMAGE_HEIGHT },
      { property: 'og:image:alt', content: resolvedImageAlt },
      { property: 'og:locale', content: computed(() => (locale.value === 'fr' ? 'fr_FR' : 'en_US')) },
      { property: 'og:locale:alternate', content: computed(() => (locale.value === 'fr' ? 'en_US' : 'fr_FR')) },
      { name: 'twitter:card', content: 'summary_large_image' },
      { name: 'twitter:title', content: resolvedTitle },
      { name: 'twitter:description', content: resolvedDescription },
      { name: 'twitter:image', content: resolvedImage },
      { name: 'twitter:image:alt', content: resolvedImageAlt },
    ],
    link: [
      { rel: 'canonical', href: selfUrl },
      { rel: 'alternate', hreflang: 'en', href: computed(() => `${SITE_URL}${enPath.value}`) },
      { rel: 'alternate', hreflang: 'fr', href: computed(() => `${SITE_URL}${frPath.value}`) },
      { rel: 'alternate', hreflang: 'x-default', href: computed(() => `${SITE_URL}${frPath.value}`) },
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
