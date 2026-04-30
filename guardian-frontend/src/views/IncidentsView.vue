<template>
  <div class="incidents-view">
    <div class="page-header">
      <div>
        <h1 class="page-title">Incidents</h1>
        <p class="page-subtitle">
          {{ store.total }} total &bull; {{ store.summary.pending }} pending
        </p>
      </div>
    </div>

    <div class="card filters-bar">
      <div class="filters-row">
        <div class="form-group">
          <label class="label">Status</label>
          <select v-model="filters.status" class="input" @change="applyFilters">
            <option value="">All statuses</option>
            <option value="PENDING">Pending</option>
            <option value="CONFIRMED">Confirmed</option>
            <option value="FALSE_POSITIVE">False Positive</option>
          </select>
        </div>

        <button class="btn btn-ghost btn-sm" @click="clearFilters" style="align-self:flex-end">
          <X :size="13" /> Clear
        </button>
      </div>
    </div>

    <div class="card" style="padding:0">
      <div v-if="store.loading" class="empty-state">
        <span class="spinner"></span>
      </div>

      <div v-else-if="!filteredIncidents.length" class="empty-state">
        <AlertTriangle :size="32" />
        <p>No incidents found</p>
      </div>

      <div v-else class="table-wrapper">
        <table class="table">
          <thead>
          <tr>
            <th>Incident</th>
            <th>Camera</th>
            <th>Status</th>
            <th>Confidence</th>
            <th>Timestamp</th>
            <th>Video</th>
            <th>Actions</th>
          </tr>
          </thead>

          <tbody>
          <tr
              v-for="incident in filteredIncidents"
              :key="incident.id"
              @click="$router.push(`/incidents/${incident.id}`)"
              style="cursor:pointer"
          >
            <td>
              <span class="badge badge-red">VIOLENCE</span>
              <div class="text-xs text-muted font-mono">{{ incident.sourceAlertId }}</div>
            </td>

            <td>
              <div>{{ incident.camera?.name || '—' }}</div>
              <div class="text-xs text-muted">
                {{ incident.camera?.facility?.name || '—' }}
              </div>
            </td>

            <td>
                <span class="badge" :class="statusBadge(incident.status)">
                  {{ formatStatus(incident.status) }}
                </span>
            </td>

            <td>
              <ConfidenceBar :value="incident.confidenceScore" />
            </td>

            <td>
              <div class="text-sm">{{ formatDate(incident.timestamp) }}</div>
              <div class="text-xs text-muted">{{ formatRelative(incident.timestamp) }}</div>
            </td>

            <td>
              <a
                  v-if="incident.minioBucket && incident.minioObjectKey"
                  class="text-xs"
                  :href="mediaUrl(incident)"
                  target="_blank"
                  @click.stop
              >
                Open video
              </a>
              <span v-else>—</span>
            </td>

            <td @click.stop>
              <div class="action-btns">
                <button
                    class="btn btn-sm btn-ghost"
                    v-if="incident.status === 'PENDING'"
                    @click="confirmIncident(incident)"
                >
                  <CheckCircle :size="13" /> Confirm
                </button>

                <button
                    class="btn btn-sm btn-ghost"
                    v-if="incident.status === 'PENDING'"
                    @click="markFalsePositive(incident)"
                >
                  <X :size="13" /> False
                </button>
              </div>
            </td>
          </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useIncidentsStore } from '@/stores/incidents'
import { AlertTriangle, X, CheckCircle } from 'lucide-vue-next'
import { format, formatDistanceToNow } from 'date-fns'
import ConfidenceBar from '@/components/common/ConfidenceBar.vue'
import { useToast } from 'vue-toastification'

const store = useIncidentsStore()
const toast = useToast()

const filters = ref({ status: '' })

onMounted(() => store.fetchIncidents())

const filteredIncidents = computed(() => {
  if (!filters.value.status) return store.incidents
  return store.incidents.filter(i => i.status === filters.value.status)
})

function applyFilters() {
  store.filters = {
    status: filters.value.status || null
  }
}

function clearFilters() {
  filters.value = { status: '' }
  store.filters = { status: null }
}

async function confirmIncident(incident) {
  await store.updateIncident(incident.id, true)
  toast.success('Incident confirmed')
}

async function markFalsePositive(incident) {
  await store.updateIncident(incident.id, false)
  toast.success('Marked as false positive')
}

function mediaUrl(incident) {
  const base = incident.minioUrl || 'http://localhost:9000'
  return `${base}/${incident.minioBucket}/${incident.minioObjectKey}`
}

function formatDate(ts) {
  try { return format(new Date(ts), 'MMM d, HH:mm:ss') } catch { return '—' }
}

function formatRelative(ts) {
  try { return formatDistanceToNow(new Date(ts), { addSuffix: true }) } catch { return '' }
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
.filters-bar { margin-bottom: 16px; padding: 16px 20px; }
.filters-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  flex-wrap: wrap;
}
.filters-row .form-group { min-width: 140px; }
.action-btns { display: flex; gap: 4px; }
.text-sm { font-size: 12px; }
.text-xs { font-size: 11px; }
.text-muted { color: var(--text-muted); }
.font-mono { font-family: monospace; }
</style>
