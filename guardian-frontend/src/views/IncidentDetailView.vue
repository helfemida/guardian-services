<template>
  <div class="incident-detail" v-if="incident">
    <div class="page-header">
      <div style="display:flex;align-items:center;gap:12px">
        <button class="btn btn-ghost btn-sm" @click="$router.back()">Back</button>

        <div>
          <h1 class="page-title">Incident</h1>
          <p class="page-subtitle font-mono">{{ incident.id }}</p>
        </div>
      </div>
    </div>

    <div class="detail-layout">
      <div class="card video-card">
        <div class="card-title-sm">Evidence video</div>

        <video
            v-if="videoUrl"
            :src="videoUrl"
            controls
            autoplay
            muted
            class="video"
        />

        <div v-else class="empty-state">
          No video available
        </div>
      </div>

      <div class="side-panel">
        <div class="card">
          <div class="card-title-sm">Incident Info</div>

          <div class="info-rows">
            <div class="info-row">
              <span class="info-label">Status</span>
              <span class="badge" :class="statusBadge(incident.status)">
                {{ formatStatus(incident.status) }}
              </span>
            </div>

            <div class="info-row">
              <span class="info-label">Confidence</span>
              <span>{{ Math.round((incident.confidenceScore || 0) * 100) }}%</span>
            </div>

            <div class="info-row">
              <span class="info-label">Timestamp</span>
              <span>{{ formatDate(incident.timestamp) }}</span>
            </div>

            <div class="info-row">
              <span class="info-label">Created</span>
              <span>{{ formatDate(incident.createdAt) }}</span>
            </div>

            <div class="info-row">
              <span class="info-label">Alert ID</span>
              <span class="font-mono text-xs">{{ incident.sourceAlertId || '—' }}</span>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-title-sm">Camera</div>

          <div class="info-rows">
            <div class="info-row">
              <span class="info-label">Name</span>
              <span>{{ incident.camera?.name || '—' }}</span>
            </div>

            <div class="info-row">
              <span class="info-label">Facility</span>
              <span>{{ incident.camera?.facility?.name || '—' }}</span>
            </div>

            <div class="info-row">
              <span class="info-label">Address</span>
              <span>{{ incident.camera?.facility?.address || '—' }}</span>
            </div>

            <div class="info-row">
              <span class="info-label">Active</span>
              <span>{{ incident.camera?.isActive ? 'Yes' : 'No' }}</span>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-title-sm">Actions</div>

          <div class="action-btns">
            <button
                class="btn btn-sm btn-ghost"
                v-if="incident.status === 'PENDING'"
                @click="confirmIncident"
            >
              Confirm
            </button>

            <button
                class="btn btn-sm btn-ghost"
                v-if="incident.status === 'PENDING'"
                @click="markFalsePositive"
            >
              False Positive
            </button>
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
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useIncidentsStore } from '@/stores/incidents'
import { format } from 'date-fns'
import { useToast } from 'vue-toastification'

const route = useRoute()
const store = useIncidentsStore()
const toast = useToast()

const incident = ref(null)

onMounted(async () => {
  incident.value = await store.fetchIncident(route.params.id)
})

const videoUrl = computed(() => {
  if (!incident.value?.minioBucket || !incident.value?.minioObjectKey) return null
  const base = incident.value.
      minioUrl || 'http://localhost:9000'
  return `${base}/${incident.value.minioBucket}/${incident.value.minioObjectKey}`
})

async function confirmIncident() {
  incident.value = await store.updateIncident(incident.value.id, 'CONFIRMED')
  toast.success('Incident confirmed')
}

async function markFalsePositive() {
  incident.value = await store.updateIncident(incident.value.id, 'FALSE_POSITIVE')
  toast.success('Marked as false positive')
}

function formatDate(ts) {
  try { return format(new Date(ts), 'MMM d, yyyy HH:mm:ss') } catch { return '—' }
}

function formatStatus(status) {
  return status?.replace(/_/g, ' ') || '—'
}

function statusBadge(status) {
  const map = {
    PENDING: 'badge-orange',
    CONFIRMED: 'badge-green',
    FALSE_POSITIVE: 'badge-gray'
  }
  return map[status] || 'badge-gray'
}
</script>

<style scoped>
.detail-layout {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 16px;
}

.side-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.video-card {
  padding: 16px;
}

.video {
  width: 100%;
  height: 520px;
  background: #000;
  object-fit: contain;
  border-radius: 12px;
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

.action-btns {
  display: flex;
  gap: 8px;
}

.text-xs {
  font-size: 11px;
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
