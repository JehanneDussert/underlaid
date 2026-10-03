<script setup>
// Where a neighbourhood stands among the 2,752 (docs/design/refonte-d4/,
// VotreQuartierD4): a bar whose last quarter is pale pink, a marker at the
// neighbourhood's rank — pink and filled in the most affected quarter,
// white with a black ring elsewhere — and a sentence that carries the
// same information in words. The bar itself is decorative (aria-hidden):
// the sentence is what a screen reader reads, so the colour never carries
// the information alone.
import { computed } from 'vue'

const props = defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  // Share of neighbourhoods less affected than this one, 0-1 (rank / n).
  share: { type: Number, default: null },
  inWorstQuarter: { type: Boolean, default: false },
  leftLabel: { type: String, required: true },
  rightLabel: { type: String, required: true },
  // The sentence, e.g. "Sur 10 quartiers, 8 sont moins exposés que le vôtre".
  sentence: { type: String, default: '' },
  // Shown instead of the bar when there is no value (e.g. not enough data).
  missing: { type: String, default: '' },
  // A line under the sentence (e.g. the better-placed neighbourhoods of the
  // same commune).
  note: { type: String, default: '' },
})

const left = computed(() => `${Math.min(100, Math.max(0, 100 * props.share))}%`)
</script>

<template>
  <div class="rank-card">
    <div class="rank-head">
      <h3 class="rank-title">{{ title }}</h3>
      <p v-if="subtitle" class="rank-subtitle">{{ subtitle }}</p>
    </div>
    <template v-if="share !== null && share !== undefined">
      <div class="rank-bar" aria-hidden="true">
        <span class="rank-marker" :class="{ worst: inWorstQuarter }" :style="{ left }"></span>
      </div>
      <div class="rank-scale" aria-hidden="true">
        <span>{{ leftLabel }}</span><span>{{ rightLabel }}</span>
      </div>
      <p class="rank-sentence">{{ sentence }}</p>
      <p v-if="note" class="rank-note">{{ note }}</p>
    </template>
    <p v-else class="rank-missing">{{ missing }}</p>
  </div>
</template>

<style scoped>
.rank-card {
  border: 1.5px solid var(--line);
  border-radius: var(--radius);
  padding: 26px 26px 24px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  background: var(--surface);
}
.rank-head {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.rank-title {
  margin: 0;
  font-size: 20px;
}
.rank-subtitle {
  margin: 0;
  font-size: 14px;
  color: var(--text-secondary);
}
.rank-bar {
  position: relative;
  height: 14px;
  border-radius: 999px;
  background: linear-gradient(90deg, #f1f1f1 0%, #f1f1f1 75%, #fbd3e7 75%, #fbd3e7 100%);
}
.rank-marker {
  position: absolute;
  top: -4px;
  width: 18px;
  height: 18px;
  margin-left: -9px;
  border-radius: 50%;
  background: var(--surface);
  border: 3px solid var(--text-primary);
}
.rank-marker.worst {
  background: var(--accent);
  border-color: var(--accent);
}
.rank-scale {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 12px;
  color: var(--text-muted);
}
.rank-sentence {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
}
.rank-note {
  margin: 0;
  font-size: 14px;
  line-height: 1.5;
  color: var(--text-secondary);
}
.rank-missing {
  margin: 0;
  color: var(--text-secondary);
}
</style>
