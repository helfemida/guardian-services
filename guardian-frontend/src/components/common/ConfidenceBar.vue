<template>
  <div class="conf-bar-wrap" v-if="value !== null && value !== undefined">
    <div class="conf-bar" :style="{ width: pct + '%', background: color }"></div>
    <span class="conf-label">{{ pct }}%</span>
  </div>
  <span v-else class="text-muted">—</span>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ value: { type: Number, default: null } })
const pct   = computed(() => props.value != null ? Math.round(props.value * 100) : 0)
const color = computed(() => {
  if (pct.value >= 80) return 'var(--red)'
  if (pct.value >= 60) return 'var(--orange)'
  if (pct.value >= 40) return 'var(--accent)'
  return 'var(--green)'
})
</script>

<style scoped>
.conf-bar-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 80px;
}
.conf-bar {
  flex: 1;
  height: 5px;
  border-radius: 3px;
  transition: width 0.3s;
}
.conf-label {
  font-size: 11px;
  font-family: var(--font-mono);
  color: var(--text-muted);
  width: 28px;
  flex-shrink: 0;
}
.text-muted { color: var(--text-muted); font-size: 12px; }
</style>
