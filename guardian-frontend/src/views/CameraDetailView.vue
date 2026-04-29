<!-- CameraDetailView.vue -->
<template>
  <div class="camera-detail" v-if="camera">
    <div class="page-header">
      <div style="display:flex;align-items:center;gap:12px">
        <button class="btn btn-ghost btn-sm" @click="$router.back()">
          Back
        </button>

        <div>
          <h1 class="page-title">{{ camera.name }}</h1>
          <p class="page-subtitle font-mono">{{ camera.id }}</p>
        </div>
      </div>
    </div>

    <div class="detail-layout">
      <!-- Stream -->
      <div class="card stream-card">
        <div class="stream-header">
          <span class="stream-label">Live Feed</span>
        </div>

        <div class="stream-viewport">
          <video
              v-if="rtspUrl"
              :src="rtspUrl"
              autoplay
              muted
              controls
              playsinline
              style="width:100%;height:100%;object-fit:cover"
          ></video>

          <div v-else class="stream-placeholder">
            <p>No stream available</p>
          </div>
        </div>

        <div class="stream-footer">
          <p class="text-xs text-muted">
            Stream URL: {{ rtspUrl || '—' }}
          </p>
        </div>
      </div>

      <!-- Info -->
      <div class="side-panel">
        <div class="card">
          <div class="card-title-sm">Camera Info</div>

          <div class="info-rows">
            <div class="info-row">
              <span class="info-label">Facility</span>
              <span>{{ camera.facility?.name || '—' }}</span>
            </div>

            <div class="info-row">
              <span class="info-label">Address</span>
              <span>{{ camera.facility?.address || '—' }}</span>
            </div>

            <div class="info-row">
              <span class="info-label">Active</span>
              <span>{{ camera.isActive ? 'Yes' : 'No' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div v-else class="empty-state">
    Loading...
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { camerasApi } from '@/services/endpoints'

const route = useRoute()

const camera = ref(null)

const streamUrl = computed(() => {
  if (!camera.value) return null
  return (
      camera.value.streamUrl ||
      camera.value.rtspUrl ||
      camera.value.url ||
      null
  )
})

onMounted(async () => {
  const { data } = await camerasApi.get(route.params.id)
  camera.value = data
})
</script>

<style scoped>
.detail-layout {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 16px;
}

.side-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stream-card {
  padding: 0;
  overflow: hidden;
}

.stream-header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
}

.stream-label {
  font-size: 11px;
  font-weight: 700;
}

.stream-viewport {
  height: 420px;
  background: #000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stream-placeholder {
  color: #777;
}

.stream-footer {
  padding: 10px 16px;
}

.card-title-sm {
  margin-bottom: 12px;
  font-size: 11px;
  font-weight: 700;
}

.info-rows {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.info-label {
  color: var(--text-muted);
}

.text-xs {
  font-size: 12px;
}

.text-muted {
  color: var(--text-muted);
}

.font-mono {
  font-family: monospace;
}

@media (max-width: 900px) {
  .detail-layout {
    grid-template-columns: 1fr;
  }
}
</style>