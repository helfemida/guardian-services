<template>
  <div class="incidents-view">
    <div class="page-header">
      <div>
        <h1 class="page-title">Incidents</h1>
        <p class="page-subtitle">{{ store.total }} total &bull; {{ store.summary.newCount }} open</p>
      </div>
    </div>

    <!-- Filters -->
    <div class="card filters-bar">
      <div class="filters-row">
        <div class="form-group">
          <label class="label">Status</label>
          <select v-model="filters.status" class="input" @change="applyFilters">
            <option value="">All statuses</option>
            <option v-for="s in statuses" :key="s.value" :value="s.value">{{ s.label }}</option>
          </select>
        </div>
        <div class="form-group">
          <label class="label">Type</label>
          <select v-model="filters.type" class="input" @change="applyFilters">
            <option value="">All types</option>
            <option v-for="t in types" :key="t.value" :value="t.value">{{ t.label }}</option>
          </select>
        </div>
        <div class="form-group">
          <label class="label">From</label>
          <input v-model="filters.from" type="datetime-local" class="input" @change="applyFilters" />
        </div>
        <div class="form-group">
          <label class="label">To</label>
          <input v-model="filters.to" type="datetime-local" class="input" @change="applyFilters" />
        </div>
        <button class="btn btn-ghost btn-sm" @click="clearFilters" style="align-self:flex-end">
          <X :size="13" /> Clear
        </button>
      </div>
    </div>

    <!-- Table -->
    <div class="card" style="padding:0">
      <div v-if="store.loading" class="empty-state">
        <span class="spinner"></span>
      </div>
      <div v-else-if="!store.incidents.length" class="empty-state">
        <AlertTriangle :size="32" />
        <p>No incidents found</p>
      </div>
      <div v-else class="table-wrapper">
        <table class="table">
          <thead>
            <tr>
              <th>Type</th>
              <th>Camera</th>
              <th>Status</th>
              <th>Confidence</th>
              <th>Timestamp</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="incident in store.incidents"
              :key="incident.id"
              @click="$router.push(`/incidents/${incident.id}`)"
              style="cursor:pointer"
            >
              <td>
                <span class="badge" :class="typeBadge(incident.incidentType)">
                  {{ formatType(incident.incidentType) }}
                </span>
              </td>
              <td>
                <div>{{ incident.cameraName || '—' }}</div>
                <div class="text-xs text-muted">{{ incident.cameraBuilding }}</div>
              </td>
              <td>
                <span class="badge" :class="statusBadge(incident.status)">
                  {{ incident.status }}
                </span>
              </td>
              <td>
                <ConfidenceBar :value="incident.confidence" />
              </td>
              <td>
                <div class="text-sm">{{ formatDate(incident.frameTimestamp) }}</div>
                <div class="text-xs text-muted">{{ formatRelative(incident.frameTimestamp) }}</div>
              </td>
              <td @click.stop>
                <div class="action-btns">
                  <button
                    class="btn btn-sm btn-ghost"
                    v-if="incident.status === 'NEW'"
                    @click="acknowledge(incident)"
                  >
                    <CheckCircle :size="13" /> Ack
                  </button>
                  <button
                    class="btn btn-sm btn-ghost"
                    v-if="['NEW','ACKNOWLEDGED','INVESTIGATING'].includes(incident.status)"
                    @click="resolve(incident)"
                  >
                    <Check :size="13" /> Resolve
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div v-if="store.totalPages > 1" class="pagination">
        <button class="btn btn-sm btn-ghost" :disabled="store.page === 0" @click="changePage(-1)">
          <ChevronLeft :size="14" />
        </button>
        <span class="page-info">{{ store.page + 1 }} / {{ store.totalPages }}</span>
        <button class="btn btn-sm btn-ghost" :disabled="store.page >= store.totalPages - 1" @click="changePage(1)">
          <ChevronRight :size="14" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useIncidentsStore } from '@/stores/incidents'
import { AlertTriangle, X, CheckCircle, Check, ChevronLeft, ChevronRight } from 'lucide-vue-next'
import { format, formatDistanceToNow } from 'date-fns'
import ConfidenceBar from '@/components/common/ConfidenceBar.vue'
import { useToast } from 'vue-toastification'

const store = useIncidentsStore()
const toast = useToast()

const filters = ref({ status: '', type: '', from: '', to: '' })

const statuses = [
  { value: 'NEW', label: 'New' },
  { value: 'ACKNOWLEDGED', label: 'Acknowledged' },
  { value: 'INVESTIGATING', label: 'Investigating' },
  { value: 'RESOLVED', label: 'Resolved' },
  { value: 'FALSE_POSITIVE', label: 'False Positive' }
]
const types = [
  { value: 'HARASSMENT', label: 'Harassment' },
  { value: 'PHYSICAL_ASSAULT', label: 'Physical Assault' },
  { value: 'VERBAL_ABUSE', label: 'Verbal Abuse' },
  { value: 'SUSPICIOUS_BEHAVIOR', label: 'Suspicious Behavior' },
  { value: 'INTRUSION', label: 'Intrusion' },
  { value: 'LOITERING', label: 'Loitering' },
  { value: 'OTHER', label: 'Other' }
]

onMounted(() => store.fetchIncidents())

function applyFilters() {
  store.page = 0
  store.filters = {
    status: filters.value.status || null,
    type: filters.value.type || null,
    from: filters.value.from ? new Date(filters.value.from).toISOString() : null,
    to: filters.value.to ? new Date(filters.value.to).toISOString() : null
  }
  store.fetchIncidents()
}

function clearFilters() {
  filters.value = { status: '', type: '', from: '', to: '' }
  store.filters = { status: null, type: null, from: null, to: null }
  store.page = 0
  store.fetchIncidents()
}

function changePage(delta) {
  store.page += delta
  store.fetchIncidents()
}

async function acknowledge(incident) {
  await store.updateIncident(incident.id, { status: 'ACKNOWLEDGED' })
  toast.success('Incident acknowledged')
}
async function resolve(incident) {
  await store.updateIncident(incident.id, { status: 'RESOLVED' })
  toast.success('Incident resolved')
}

function formatDate(ts) {
  try { return format(new Date(ts), 'MMM d, HH:mm:ss') } catch { return '—' }
}
function formatRelative(ts) {
  try { return formatDistanceToNow(new Date(ts), { addSuffix: true }) } catch { return '' }
}
function formatType(type) { return type?.replace(/_/g, ' ') || '—' }

function typeBadge(type) {
  const map = {
    HARASSMENT: 'badge-red', PHYSICAL_ASSAULT: 'badge-red',
    VERBAL_ABUSE: 'badge-orange', SUSPICIOUS_BEHAVIOR: 'badge-amber',
    INTRUSION: 'badge-purple', LOITERING: 'badge-blue', OTHER: 'badge-gray'
  }
  return map[type] || 'badge-gray'
}
function statusBadge(status) {
  const map = {
    NEW: 'badge-red', ACKNOWLEDGED: 'badge-orange',
    INVESTIGATING: 'badge-blue', RESOLVED: 'badge-green', FALSE_POSITIVE: 'badge-gray'
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

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 14px;
  border-top: 1px solid var(--border);
}
.page-info { font-size: 12px; color: var(--text-muted); font-family: var(--font-mono); }

.text-sm { font-size: 12px; }
.text-xs { font-size: 11px; }
.text-muted { color: var(--text-muted); }
</style>
