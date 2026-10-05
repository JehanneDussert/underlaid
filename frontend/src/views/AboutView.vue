<script setup>
// About page, redesign D4 (docs/design/refonte-d4/: 06, AProposD4): the
// project, how to cite it, reuse (licences decided on 3 October 2026: code
// MIT, data ODbL, maps and visuals CC BY 4.0), collaborate, press, and
// "Vos données" (wording validated on 3 October 2026). The contact address
// is composed on click, never written in the page.
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useSeoMeta } from '../composables/useSeoMeta'
import { localizedRouteName } from '../router'

const { t, locale } = useI18n()

useSeoMeta({
  image: 'apropos',
  title: { en: 'About', fr: 'À propos' },
  description: {
    en: 'Who runs Underlaid, how to cite it, reuse its data and code, contribute, and what happens to your data.',
    fr: 'Qui porte Underlaid, comment le citer, réutiliser ses données et son code, y contribuer, et ce que deviennent vos données.',
  },
})

const REPO_URL = 'https://github.com/JehanneDussert/underlaid'
const PERSONAL_SITE = 'https://jehannedussert.com'
const GITHUB_PROFILE = 'https://github.com/JehanneDussert'
const LINKEDIN_URL = 'https://www.linkedin.com/in/jehanne-dussert'
const VERSION = '0.2.0'
const VERSION_DOI = '10.5281/zenodo.23101510'
const CONCEPT_DOI_URL = 'https://doi.org/10.5281/zenodo.23083312'
const TITLE = 'Underlaid: cumulative environmental exposure in Paris and its inner suburbs'
const PARTS = ['projet', 'citer', 'reutiliser', 'collaborer', 'presse', 'confidentialite']

// Citation, text or BibTeX (tabs).
const format = ref('text')
const citation = computed(() =>
  format.value === 'text'
    ? `Dussert, J. (2026). ${TITLE} (version ${VERSION}) [${t('about.cite.kind')}]. Zenodo. https://doi.org/${VERSION_DOI}`
    : `@software{dussert_underlaid_2026,
  author    = {Dussert, Jehanne},
  title     = {{${TITLE}}},
  year      = {2026},
  version   = {${VERSION}},
  publisher = {Zenodo},
  doi       = {${VERSION_DOI}},
  url       = {https://doi.org/${VERSION_DOI}}
}`
)
const copied = ref('')
async function copy() {
  try {
    await navigator.clipboard.writeText(citation.value)
    copied.value = t('about.cite.copied')
  } catch {
    copied.value = t('about.cite.copyFailed')
  }
}
function onTabKey(e) {
  if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
    format.value = format.value === 'text' ? 'bibtex' : 'text'
    e.currentTarget.parentElement.querySelector(`[data-tab="${format.value}"]`)?.focus()
  }
}

// Contact: the address is composed on click only (decision of 3 October 2026).
const CONTACT_PARTS = ['research.jehannedussert', 'gmail.com']
function writeTo(e) {
  e.preventDefault()
  window.location.href = `mailto:${CONTACT_PARTS.join('@')}`
}
</script>

<template>
  <article class="about">
    <header class="container about-head">
      <h1>{{ t('about.title') }}</h1>
      <p class="lead">{{ t('about.lead') }}</p>
    </header>
    <div class="container about-grid">
      <nav class="toc" :aria-label="t('method.tocLabel')">
        <span class="toc-title">{{ t('method.tocLabel') }}</span>
        <ol>
          <li v-for="(id, i) in PARTS" :key="id">
            <a :href="`#${id}`"><span class="toc-num">{{ i + 1 }}</span>{{ t(`about.part.${id}`) }}</a>
          </li>
        </ol>
      </nav>

      <div class="parts">
        <section id="projet" class="part" aria-labelledby="a-projet">
          <h2 id="a-projet"><span class="num">1.</span>{{ t('about.part.projet') }}</h2>
          <p>{{ t('about.projet.p1') }}</p>
          <p v-html="t('about.projet.p2')"></p>
          <p>
            {{ t('about.projet.p3a') }}
            <a href="https://eig.numerique.gouv.fr/defis/twincity/" rel="noopener">TwinCity</a>{{ t('about.projet.p3b') }}
          </p>
          <p>{{ t('about.projet.p4') }}</p>
          <ul class="person-links">
            <li><a :href="PERSONAL_SITE" rel="noopener">{{ t('about.projet.personalSite') }}</a></li>
            <li><a :href="GITHUB_PROFILE" rel="noopener">GitHub</a></li>
            <li><a :href="LINKEDIN_URL" rel="noopener">LinkedIn</a></li>
          </ul>
        </section>

        <section id="citer" class="part" aria-labelledby="a-citer">
          <h2 id="a-citer"><span class="num">2.</span>{{ t('about.part.citer') }}</h2>
          <p>{{ t('about.cite.intro') }}</p>
          <div class="cite-box">
            <div role="tablist" :aria-label="t('about.cite.formats')" class="tabs">
              <button
                v-for="f in ['text', 'bibtex']"
                :id="`tab-${f}`"
                :key="f"
                type="button"
                role="tab"
                :data-tab="f"
                :aria-selected="format === f ? 'true' : 'false'"
                :tabindex="format === f ? 0 : -1"
                aria-controls="cite-panel"
                @click="format = f"
                @keydown="onTabKey"
              >{{ t(`about.cite.${f}`) }}</button>
            </div>
            <div id="cite-panel" role="tabpanel" :aria-labelledby="`tab-${format}`">
              <pre class="citation">{{ citation }}</pre>
            </div>
            <div class="cite-actions">
              <button type="button" class="pill-button" @click="copy">{{ t('about.cite.copy') }}</button>
              <span class="small">{{ t('about.cite.note') }}</span>
              <span class="sr-only" aria-live="polite">{{ copied }}</span>
              <span v-if="copied" class="small" aria-hidden="true">{{ copied }}</span>
            </div>
          </div>
          <p class="small">
            {{ t('about.cite.concept') }}
            <a :href="CONCEPT_DOI_URL" rel="noopener">{{ CONCEPT_DOI_URL }}</a>
          </p>
        </section>

        <section id="reutiliser" class="part" aria-labelledby="a-reutiliser">
          <h2 id="a-reutiliser"><span class="num">3.</span>{{ t('about.part.reutiliser') }}</h2>
          <p>{{ t('about.reuse.intro') }}</p>
          <!-- Focusable: a scrollable region must be reachable with the keyboard. -->
      <div class="table-wrap" tabindex="0" role="region" :aria-label="t('site.tableRegion')">
            <table>
              <caption class="sr-only">{{ t('about.part.reutiliser') }}</caption>
              <thead>
                <tr>
                  <th scope="col">{{ t('about.reuse.what') }}</th>
                  <th scope="col">{{ t('about.reuse.licence') }}</th>
                  <th scope="col">{{ t('about.reuse.allows') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in ['code', 'data', 'osm', 'visuals']" :key="row">
                  <th scope="row">{{ t(`about.reuse.rows.${row}.what`) }}</th>
                  <td>{{ t(`about.reuse.rows.${row}.licence`) }}</td>
                  <td>{{ t(`about.reuse.rows.${row}.allows`) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="links">
            <a class="pill-link" :href="CONCEPT_DOI_URL" rel="noopener">{{ t('about.reuse.zenodo') }}</a>
            <a class="pill-link" :href="REPO_URL" rel="noopener">{{ t('about.reuse.github') }}</a>
            <router-link class="pill-link" :to="{ name: localizedRouteName('methodology-details', locale), hash: '#data-licences' }">{{ t('about.reuse.sources') }}</router-link>
          </div>
        </section>

        <section id="collaborer" class="part" aria-labelledby="a-collaborer">
          <h2 id="a-collaborer"><span class="num">4.</span>{{ t('about.part.collaborer') }}</h2>
          <p>{{ t('about.collab.intro') }}</p>
          <ul class="bullets">
            <li v-for="i in 4" :key="i">{{ t(`about.collab.items.${i - 1}`) }}</li>
          </ul>
          <div class="links">
            <a class="pill-link" :href="`${REPO_URL}/issues/new`" rel="noopener">{{ t('about.collab.report') }}</a>
            <a class="pill-link" :href="`${REPO_URL}/discussions`" rel="noopener">{{ t('about.collab.discuss') }}</a>
            <a class="pill-link" :href="`${REPO_URL}/discussions`" rel="noopener" @click="writeTo">{{ t('about.collab.write') }}</a>
          </div>
        </section>

        <section id="presse" class="part" aria-labelledby="a-presse">
          <h2 id="a-presse"><span class="num">5.</span>{{ t('about.part.presse') }}</h2>
          <p>{{ t('about.press.intro') }}</p>
          <div class="press-cards">
            <router-link class="press-card" :to="{ name: localizedRouteName('press', locale) }">
              <span class="press-title"><span class="ring" style="border-color: #e4007c" aria-hidden="true"></span>{{ t('about.press.figures') }}</span>
              <span class="small">{{ t('about.press.figuresDesc') }}</span>
            </router-link>
            <div class="press-card">
              <span class="press-title"><span class="ring" style="border-color: #ff7a00" aria-hidden="true"></span>{{ t('about.press.visuals') }}</span>
              <span class="small">{{ t('about.press.visualsDesc') }}</span>
            </div>
            <a class="press-card" :href="`${REPO_URL}/discussions`" rel="noopener" @click="writeTo">
              <span class="press-title"><span class="ring" style="border-color: #00a06b" aria-hidden="true"></span>{{ t('about.press.contact') }}</span>
              <span class="small">{{ t('about.press.contactDesc') }}</span>
            </a>
          </div>
        </section>

        <section id="confidentialite" class="part" aria-labelledby="a-confidentialite">
          <h2 id="a-confidentialite"><span class="num">6.</span>{{ t('about.part.confidentialite') }}</h2>
          <p>{{ t('about.privacy') }}</p>
        </section>
      </div>
    </div>
  </article>
</template>

<style scoped>
.about-head {
  padding-top: 40px;
  padding-bottom: 8px;
}
.about-head h1 {
  margin: 0 0 12px;
  font-size: 46px;
  letter-spacing: -0.02em;
}
.lead {
  margin: 0;
  font-size: 19px;
  line-height: 1.55;
  color: var(--text-secondary);
  max-width: 820px;
}
.about-grid {
  display: grid;
  grid-template-columns: 260px minmax(0, 1fr);
  gap: 56px;
  padding-top: 32px;
}
.toc {
  align-self: start;
  position: sticky;
  top: 24px;
  border-left: 3px solid var(--primary);
  padding-left: 18px;
}
.toc-title {
  font-size: 13px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
.toc ol {
  list-style: none;
  margin: 10px 0 0;
  padding: 0;
}
.toc a {
  display: flex;
  gap: 10px;
  align-items: center;
  min-height: 36px;
  padding: 7px 0;
  font-size: 15px;
  text-decoration: none;
}
.toc a:hover {
  text-decoration: underline;
}
.toc-num {
  color: var(--text-muted);
  min-width: 16px;
}
.parts {
  min-width: 0;
}
.part {
  padding-bottom: 64px;
  scroll-margin-top: 24px;
}
.part h2 {
  margin: 0 0 18px;
  font-size: 30px;
}
.num {
  color: var(--primary);
  margin-right: 10px;
}
.part p {
  font-size: 17px;
  line-height: 1.65;
  margin: 0 0 14px;
  max-width: 820px;
}
.small,
.part p.small {
  font-size: 14px;
  color: var(--text-secondary);
}
.cite-box {
  border: 1.5px solid var(--line);
  border-radius: var(--radius);
  padding: 18px 22px;
  margin-bottom: 14px;
  max-width: 900px;
}
.tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 12px;
}
.tabs button {
  min-height: 40px;
  padding: 0 16px;
  border-radius: 999px;
  border: 1.5px solid var(--control-border);
  background: var(--surface);
  font: inherit;
  cursor: pointer;
}
.tabs button[aria-selected='true'] {
  background: var(--text-primary);
  color: #fff;
  border-color: var(--text-primary);
  font-weight: 700;
}
.citation {
  margin: 0 0 14px;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: var(--mono);
  font-size: 14px;
  line-height: 1.6;
  background: var(--surface-muted);
  padding: 14px 16px;
  border-radius: 12px;
}
.cite-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}
.pill-button,
.pill-link {
  display: inline-flex;
  align-items: center;
  min-height: 44px;
  padding: 0 18px;
  border-radius: 999px;
  border: 2px solid var(--control-border);
  background: var(--surface);
  font: inherit;
  font-weight: 700;
  text-decoration: none;
  cursor: pointer;
}
.pill-button:hover,
.pill-link:hover {
  border-color: var(--text-primary);
}
.links {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin: 8px 0;
}
table {
  border-collapse: collapse;
  width: 100%;
  font-size: 15px;
}
th,
td {
  text-align: left;
  vertical-align: top;
  padding: 10px 12px 10px 0;
  border-bottom: 1px solid var(--line);
  line-height: 1.5;
}
.table-wrap {
  overflow-x: auto;
  margin: 8px 0 14px;
  max-width: 900px;
}
.bullets {
  margin: 0 0 14px;
  padding-left: 22px;
  line-height: 1.7;
  font-size: 17px;
}
.press-cards {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  max-width: 900px;
}
.press-card {
  border: 1.5px solid var(--line);
  border-radius: 18px;
  padding: 18px 20px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  text-decoration: none;
}
a.press-card:hover {
  border-color: var(--text-primary);
}
.press-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
}
.ring {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 3px solid;
}
@media (max-width: 900px) {
  .about-grid {
    grid-template-columns: minmax(0, 1fr);
    gap: 24px;
  }
  .toc {
    position: static;
  }
  .press-cards {
    grid-template-columns: minmax(0, 1fr);
  }
  .about-head h1 {
    font-size: 34px;
  }
  .part h2 {
    font-size: 24px;
  }
}
.person-links {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 24px;
  list-style: none;
  padding: 0;
  margin: 0 0 16px;
  font-size: 17px;
}
.person-links a {
  display: inline-flex;
  align-items: center;
  min-height: 44px;
}
</style>
