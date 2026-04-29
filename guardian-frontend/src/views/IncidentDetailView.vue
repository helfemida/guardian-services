<template>
  <div class="incident-detail" v-if="incident">
    <!-- Header -->
    <div class="page-header">
      <div style="display:flex;align-items:center;gap:12px">
        <button class="btn btn-ghost btn-sm" @click="$router.back()">
          <ArrowLeft :size="14" /> Back
        </button>
        <div>
          <h1 class="page-title">Incident Detail</h1>
          <p class="page-subtitle font-mono">{{ incident.id }}</p>
        </div>
      </div>
      <div style="display:flex;gap:8px;align-items:center">
        <span class="badge" :class="statusBadge(incident.status)">{{ incident.status }}</span>
        <span class="badge" :class="typeBadge(incident.incidentType)">
          {{ formatType(incident.incidentType) }}
        </span>
      </div>
    </div>

    <div class="detail-grid">
      <!-- Left column -->
      <div class="detail-left">
        <!-- Thumbnail / video preview -->
        <div class="card media-card">
          <div class="media-placeholder" v-if="!incident.thumbnailUrl">
            <VideoOff :size="40" />
            <p>No preview available</p>
          </div>
          <img v-else :src="incident.thumbnailUrl" class="thumbnail" alt="Incident thumbnail" />
          <div class="media-footer">
            <span class="meta-item">
              <Camera :size="13" />
              {{ incident.cameraName || 'Unknown Camera' }}
            </span>
            <span class="meta-item">
              <MapPin :size="13" />
              {{ incident.cameraBuilding || '—' }}
            </span>
          </div>
        </div>

        <!-- Detection info -->
        <div class="card">
          <div class="card-title" style="margin-bottom:14px">Detection Details</div>
          <div class="detail-rows">
            <div class="detail-row">
              <span class="detail-label">Confidence</span>
              <div style="flex:1">
                <ConfidenceBar :value="incident.confidence" />
              </div>
            </div>
            <div class="detail-row">
              <span class="detail-label">Frame Time</span>
              <span class="detail-val font-mono">{{ formatDate(incident.frameTimestamp) }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">Detected At</span>
              <span class="detail-val font-mono">{{ formatDate(incident.createdAt) }}</span>
            </div>
            <div class="detail-row" v-if="incident.videoChunkPath">
              <span class="detail-label">Video Chunk</span>
              <a :href="incident.videoChunkPath" target="_blank" class="detail-link">
                <Download :size="12" /> Download
              </a>
            </div>
            <div class="detail-row" v-if="incident.personId">
              <span class="detail-label">Person ID</span>
              <span class="detail-val font-mono">{{ incident.personId }}</span>
            </div>
          </div>
        </div>

        <!-- Bounding box raw data -->
        <div class="card" v-if="incident.boundingBox">
          <div class="card-title" style="margin-bottom:10px">Bounding Box</div>
          <pre class="json-pre">{{ formatJson(incident.boundingBox) }}</pre>
        </div>
      </div>

      <!-- Right column -->
      <div class="detail-right">
        <!-- Status management -->
        <div class="card">
          <div class="card-title" style="margin-bottom:14px">Status Management</div>
          <div class="status-flow">
            <div
              v-for="(s, i) in statusFlow"
              :key="s.value"
              class="status-step"
              :class="{
                active: incident.status === s.value,
                done: statusIndex > i,
                clickable: canTransitionTo(s.value)
              }"
              @click="canTransitionTo(s.value) && transitionStatus(s.value)"
            >
              <div class="step-dot">
                <Check v-if="statusIndex > i" :size="10" />
                <span v-else>{{ i + 1 }}</span>
              </div>
              <span class="step-label">{{ s.label }}</span>
            </div>
          </div>
        </div>

        <!-- Notes -->
        <div class="card">
          <div class="card-title" style="margin-bottom:12px">Notes</div>
          <textarea
            v-model="notes"
            class="input notes-input"
            placeholder="Add investigation notes…"
            rows="5"
          ></textarea>
          <button
            class="btn btn-secondary btn-sm"
            style="margin-top:8px"
            @click="saveNotes"
            :disabled="savingNotes || notes === incident.notes"
          >
            <Save :size="13" />
            {{ savingNotes ? 'Saving…' : 'Save Notes' }}
          </button>
        </div>

        <!-- Alert history -->
        <div class="card" v-if="alertLogs.length">
          <div class="card-title" style="margin-bottom:12px">Alert History</div>
          <div class="alert-log-list">
            <div v-for="log in alertLogs" :key="log.id" class="alert-log-item">
              <Bell :size="13" class="text-orange" />
              <div>
                <div class="text-sm">{{ log.message }}</div>
                <div class="text-xs text-muted">{{ formatDate(log.sentAt) }}</div>
              </div>
              <span class="badge" :class="log.alertStatus === 'SENT' ? 'badge-green' : 'badge-red'">
                {{ log.alertStatus }}
              </span>
            </div>
          </div>
        </div>

        <!-- Metadata -->
        <div class="card" v-if="incident.metadata">
          <div class="card-title" style="margin-bottom:10px">Raw Metadata</div>
          <pre class="json-pre">{{ formatJson(incident.metadata) }}</pre>
        </div>
      </div>
    </div>
  </div>

  <div v-else class="empty-state">
    <span class="spinner"></span>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowLeft, Camera, MapPin, VideoOff, Download,
  Check, Save, Bell
} from 'lucide-vue-next'
import { incidentsApi } from '@/services/endpoints'
import ConfidenceBar from '@/components/common/ConfidenceBar.vue'
import { format } from 'date-fns'
import { useToast } from 'vue-toastification'

const route  = useRoute()
const router = useRouter()
const toast  = useToast()

const incident   = ref(null)
const notes      = ref('')
const savingNotes = ref(false)
const alertLogs  = ref([])

const statusFlow = [
  { value: 'NEW', label: 'New' },
  { value: 'ACKNOWLEDGED', label: 'Acknowledged' },
  { value: 'INVESTIGATING', label: 'Investigating' },
  { value: 'RESOLVED', label: 'Resolved' }
]

const statusIndex = computed(() => statusFlow.findIndex(s => s.value === incident.value?.status))

onMounted(async () => {
  const { data } = await incidentsApi.get(route.params.id)
  incident.value = data
  notes.value    = data.notes || ''
})

function canTransitionTo(status) {
  const order = ['NEW', 'ACKNOWLEDGED', 'INVESTIGATING', 'RESOLVED', 'FALSE_POSITIVE']
  const cur   = order.indexOf(incident.value?.status)
  const next  = order.indexOf(status)
  return next > cur
}

async function transitionStatus(status) {
  const { data } = await incidentsApi.update(route.params.id, { status })
  incident.value = data
  toast.success(`Status updated to ${status}`)
}

async function saveNotes() {
  savingNotes.value = true
  try {
    const { data } = await incidentsApi.update(route.params.id, { notes: notes.value })
    incident.value = data
    toast.success('Notes saved')
  } finally {
    savingNotes.value = false
  }
}

function formatDate(ts) {
  try { return format(new Date(ts), 'MMM d yyyy, HH:mm:ss') } catch { return '—' }
}
function formatType(type) { return type?.replace(/_/g, ' ') || '—' }
function formatJson(val) {
  try { return JSON.stringify(typeof val === 'string' ? JSON.parse(val) : val, null, 2) }
  catch { return val }
}
function typeBadge(type) {
  const m = { HARASSMENT:'badge-red', PHYSICAL_ASSAULT:'badge-red', VERBAL_ABUSE:'badge-orange',
    SUSPICIOUS_BEHAVIOR:'badge-amber', INTRUSION:'badge-purple', LOITERING:'badge-blue', OTHER:'badge-gray' }
  return m[type] || 'badge-gray'
}
function statusBadge(status) {
  const m = { NEW:'badge-red', ACKNOWLEDGED:'badge-orange', INVESTIGATING:'badge-blue',
    RESOLVED:'badge-green', FALSE_POSITIVE:'badge-gray' }
  return m[status] || 'badge-gray'
}
</script>

<style scoped>
.detail-grid {
  display: grid;
  grid-template-columns: 1fr 360px;
  gap: 16px;
}
.detail-left, .detail-right { display: flex; flex-direction: column; gap: 16px; }

.media-card { padding: 0; overflow: hidden; }
.media-placeholder {
  height: 220px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  background: var(--bg-elevated);
  color: var(--text-muted);
}
.thumbnail { width: 100%; height: 220px; object-fit: cover; display: block; }
.media-footer {
  display: flex;
  gap: 16px;
  padding: 10px 14px;
  border-top: 1px solid var(--border);
}
.meta-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: var(--text-secondary);
}

.detail-rows { display: flex; flex-direction: column; gap: 10px; }
.detail-row {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
}
.detail-label {
  width: 110px;
  flex-shrink: 0;
  font-size: 11px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.4px;
}
.detail-val { color: var(--text-primary); }
.detail-link {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--accent);
}

.json-pre {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-secondary);
  background: var(--bg-elevated);
  padding: 10px;
  border-radius: var(--radius);
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 150px;
}

/* Status flow */
.status-flow {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.status-step {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: var(--radius);
  transition: background 0.12s;
}
.status-step.clickable { cursor: pointer; }
.status-step.clickable:hover { background: var(--bg-overlay); }
.status-step.active { background: var(--accent-dim); }

.step-dot {
  width: 22px; height: 22px;
  border-radius: 50%;
  border: 2px solid var(--border-mid);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  color: var(--text-muted);
  flex-shrink: 0;
}
.status-step.active .step-dot  { border-color: var(--accent); color: var(--accent); }
.status-step.done   .step-dot  { background: var(--green); border-color: var(--green); color: white; }
.step-label { font-size: 13px; color: var(--text-secondary); }
.status-step.active .step-label { color: var(--accent); font-weight: 600; }

.notes-input { resize: vertical; }

.alert-log-list { display: flex; flex-direction: column; gap: 8px; }
.alert-log-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 10px;
  background: var(--bg-elevated);
  border-radius: var(--radius);
}

.card-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.font-mono { font-family: var(--font-mono); font-size: 11px; }
.text-sm   { font-size: 12px; color: var(--text-primary); }
.text-xs   { font-size: 11px; }
.text-muted { color: var(--text-muted); }
.text-orange { color: var(--orange); }

@media (max-width: 1000px) {
  .detail-grid { grid-template-columns: 1fr; }
}
</style>
