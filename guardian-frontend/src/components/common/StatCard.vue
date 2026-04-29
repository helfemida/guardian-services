<template>
  <div class="stat-card" :class="`color-${color}`">
    <div class="stat-icon">
      <component :is="icon" :size="18" />
    </div>
    <div class="stat-body">
      <div class="stat-value">{{ value }}</div>
      <div class="stat-label">{{ label }}</div>
    </div>
    <span v-if="pulse" class="pulse-ring"></span>
  </div>
</template>

<script setup>
defineProps({
  label:  { type: String, required: true },
  value:  { type: [String, Number], required: true },
  icon:   { required: true },
  color:  { type: String, default: 'blue' },
  pulse:  { type: Boolean, default: false }
})
</script>

<style scoped>
.stat-card {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 18px 20px;
  display: flex;
  align-items: center;
  gap: 14px;
  position: relative;
  overflow: hidden;
  transition: border-color 0.2s;
}
.stat-card::before {
  content: '';
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 3px;
}

.color-red    { border-color: rgba(239,68,68,0.2); }
.color-red    .stat-icon { background: var(--red-dim); color: var(--red); }
.color-red::before { background: var(--red); }

.color-green  { border-color: rgba(34,197,94,0.2); }
.color-green  .stat-icon { background: var(--green-dim); color: var(--green); }
.color-green::before { background: var(--green); }

.color-blue   { border-color: rgba(59,130,246,0.2); }
.color-blue   .stat-icon { background: var(--blue-dim); color: var(--blue); }
.color-blue::before { background: var(--blue); }

.color-orange { border-color: rgba(249,115,22,0.2); }
.color-orange .stat-icon { background: var(--orange-dim); color: var(--orange); }
.color-orange::before { background: var(--orange); }

.color-amber  { border-color: rgba(245,158,11,0.2); }
.color-amber  .stat-icon { background: var(--accent-dim); color: var(--accent); }
.color-amber::before { background: var(--accent); }

.stat-icon {
  width: 40px; height: 40px;
  border-radius: var(--radius);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-body { flex: 1; }

.stat-value {
  font-family: var(--font-mono);
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.1;
}

.stat-label {
  font-size: 11px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-top: 2px;
}

.pulse-ring {
  position: absolute;
  top: 12px; right: 12px;
  width: 8px; height: 8px;
  border-radius: 50%;
  background: var(--red);
  animation: blink 1s ease-in-out infinite;
}
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.2; }
}
</style>
