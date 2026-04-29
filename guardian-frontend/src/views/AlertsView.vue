<!--<template>-->
<!--  <div class="alerts-view">-->
<!--    <div class="page-header">-->
<!--      <div>-->
<!--        <h1 class="page-title">Alerts</h1>-->
<!--        <p class="page-subtitle">Harassment alert dispatch log</p>-->
<!--      </div>-->
<!--      <div class="live-badge" :class="sseConnected ? 'live' : 'offline'">-->
<!--        <span class="pulse-dot" :class="sseConnected ? 'online' : 'offline'"></span>-->
<!--        {{ sseConnected ? 'Live' : 'Offline' }}-->
<!--      </div>-->
<!--    </div>-->

<!--    &lt;!&ndash; Live alerts ticker &ndash;&gt;-->
<!--    <div class="alert-ticker" v-if="liveAlerts.length">-->
<!--      <div class="ticker-label">-->
<!--        <Zap :size="13" /> RECENT-->
<!--      </div>-->
<!--      <TransitionGroup name="slide-up" tag="div" class="ticker-items">-->
<!--        <div v-for="alert in liveAlerts.slice(0, 5)" :key="alert.id" class="ticker-item">-->
<!--          <span class="ticker-type badge badge-red">ALERT</span>-->
<!--          <span class="ticker-msg">{{ alert.message }}</span>-->
<!--          <span class="ticker-time">{{ formatRelative(alert.sentAt) }}</span>-->
<!--        </div>-->
<!--      </TransitionGroup>-->
<!--    </div>-->

<!--    <div class="alerts-grid">-->
<!--      &lt;!&ndash; Alert log &ndash;&gt;-->
<!--      <div class="card">-->
<!--        <div class="card-title-row">-->
<!--          <span class="card-title">Alert Log</span>-->
<!--          <button class="btn btn-ghost btn-sm" @click="loadAlerts">-->
<!--            <RefreshCw :size="13" />-->
<!--          </button>-->
<!--        </div>-->

<!--        <div v-if="loading" class="empty-state"><span class="spinner"></span></div>-->
<!--        <div v-else-if="!alerts.length" class="empty-state">-->
<!--          <Bell :size="32" />-->
<!--          <p>No alerts dispatched</p>-->
<!--        </div>-->
<!--        <div v-else class="alert-list">-->
<!--          <div v-for="alert in alerts" :key="alert.id" class="alert-item">-->
<!--            <div class="alert-left">-->
<!--              <div class="alert-icon" :class="alert.alertStatus === 'SENT' ? 'icon-red' : 'icon-gray'">-->
<!--                <ShieldAlert :size="16" />-->
<!--              </div>-->
<!--            </div>-->
<!--            <div class="alert-body">-->
<!--              <div class="alert-message">{{ alert.message || 'Alert dispatched' }}</div>-->
<!--              <div class="alert-meta">-->
<!--                <span class="meta-chip">-->
<!--                  <Fingerprint :size="11" />-->
<!--                  {{ shortId(alert.incidentId) }}-->
<!--                </span>-->
<!--                <span v-if="alert.policeStationId" class="meta-chip">-->
<!--                  <Building2 :size="11" />-->
<!--                  {{ shortId(alert.policeStationId) }}-->
<!--                </span>-->
<!--                <span class="meta-chip">-->
<!--                  <Clock :size="11" />-->
<!--                  {{ formatDate(alert.sentAt) }}-->
<!--                </span>-->
<!--              </div>-->
<!--            </div>-->
<!--            <div class="alert-status">-->
<!--              <span class="badge" :class="alert.alertStatus === 'SENT' ? 'badge-green' : 'badge-red'">-->
<!--                {{ alert.alertStatus }}-->
<!--              </span>-->
<!--            </div>-->
<!--            <button-->
<!--              class="btn btn-sm btn-ghost"-->
<!--              @click="$router.push(`/incidents/${alert.incidentId}`)"-->
<!--            >-->
<!--              <ExternalLink :size="12" />-->
<!--            </button>-->
<!--          </div>-->
<!--        </div>-->
<!--      </div>-->

<!--      &lt;!&ndash; Police Stations panel &ndash;&gt;-->
<!--      <div class="card">-->
<!--        <div class="card-title-row">-->
<!--          <span class="card-title">Police Stations</span>-->
<!--          <button class="btn btn-sm btn-primary" @click="showAddStation = true">-->
<!--            <Plus :size="13" /> Add-->
<!--          </button>-->
<!--        </div>-->

<!--        <div class="station-list">-->
<!--          <div v-for="station in stations" :key="station.id" class="station-item">-->
<!--            <div class="station-icon">-->
<!--              <Building2 :size="16" />-->
<!--            </div>-->
<!--            <div class="station-body">-->
<!--              <div class="station-name">{{ station.name }}</div>-->
<!--              <div class="station-meta">{{ station.address }}</div>-->
<!--              <div class="station-contacts">-->
<!--                <span v-if="station.phone" class="contact-chip">-->
<!--                  <Phone :size="10" /> {{ station.phone }}-->
<!--                </span>-->
<!--                <span v-if="station.email" class="contact-chip">-->
<!--                  <Mail :size="10" /> {{ station.email }}-->
<!--                </span>-->
<!--              </div>-->
<!--            </div>-->
<!--            <span class="badge" :class="station.active ? 'badge-green' : 'badge-gray'">-->
<!--              {{ station.active ? 'Active' : 'Inactive' }}-->
<!--            </span>-->
<!--          </div>-->
<!--          <div v-if="!stations.length" class="empty-state" style="padding:24px 0">-->
<!--            <p>No stations configured</p>-->
<!--          </div>-->
<!--        </div>-->
<!--      </div>-->
<!--    </div>-->

<!--    &lt;!&ndash; Add Station Modal &ndash;&gt;-->
<!--    <Teleport to="body">-->
<!--      <div v-if="showAddStation" class="modal-backdrop" @click.self="showAddStation = false">-->
<!--        <div class="modal">-->
<!--          <div class="modal-header">-->
<!--            <span>Add Police Station</span>-->
<!--            <button class="btn btn-icon btn-ghost btn-sm" @click="showAddStation = false">-->
<!--              <X :size="15" />-->
<!--            </button>-->
<!--          </div>-->
<!--          <div class="modal-body">-->
<!--            <div class="grid-2">-->
<!--              <div class="form-group" style="grid-column:1/-1">-->
<!--                <label class="label">Station Name *</label>-->
<!--                <input v-model="stationForm.name" class="input" />-->
<!--              </div>-->
<!--              <div class="form-group" style="grid-column:1/-1">-->
<!--                <label class="label">Address</label>-->
<!--                <input v-model="stationForm.address" class="input" />-->
<!--              </div>-->
<!--              <div class="form-group">-->
<!--                <label class="label">Phone</label>-->
<!--                <input v-model="stationForm.phone" class="input" />-->
<!--              </div>-->
<!--              <div class="form-group">-->
<!--                <label class="label">Email</label>-->
<!--                <input v-model="stationForm.email" class="input" type="email" />-->
<!--              </div>-->
<!--              <div class="form-group">-->
<!--                <label class="label">Latitude *</label>-->
<!--                <input v-model.number="stationForm.latitude" class="input" type="number" step="any" />-->
<!--              </div>-->
<!--              <div class="form-group">-->
<!--                <label class="label">Longitude *</label>-->
<!--                <input v-model.number="stationForm.longitude" class="input" type="number" step="any" />-->
<!--              </div>-->
<!--            </div>-->
<!--          </div>-->
<!--          <div class="modal-footer">-->
<!--            <button class="btn btn-ghost" @click="showAddStation = false">Cancel</button>-->
<!--            <button class="btn btn-primary" @click="addStation" :disabled="savingStation">-->
<!--              {{ savingStation ? 'Saving…' : 'Add Station' }}-->
<!--            </button>-->
<!--          </div>-->
<!--        </div>-->
<!--      </div>-->
<!--    </Teleport>-->
<!--  </div>-->
<!--</template>-->

<!--<script setup>-->
<!--import { ref, onMounted, onUnmounted } from 'vue'-->
<!--import {-->
<!--  Bell, ShieldAlert, Building2, Fingerprint, Clock,-->
<!--  RefreshCw, Plus, X, ExternalLink, Zap, Phone, Mail-->
<!--} from 'lucide-vue-next'-->
<!--import { alertsApi } from '@/services/endpoints'-->
<!--import { ReconnectingEventSource } from '@/services/sse'-->
<!--import { format, formatDistanceToNow } from 'date-fns'-->
<!--import { useToast } from 'vue-toastification'-->

<!--const toast         = useToast()-->
<!--const alerts        = ref([])-->
<!--const liveAlerts    = ref([])-->
<!--const stations      = ref([])-->
<!--const loading       = ref(false)-->
<!--const sseConnected  = ref(false)-->
<!--const showAddStation = ref(false)-->
<!--const savingStation  = ref(false)-->

<!--const stationForm = ref({ name: '', address: '', phone: '', email: '', latitude: null, longitude: null })-->

<!--let alertSse-->

<!--onMounted(async () => {-->
<!--  await Promise.all([loadAlerts(), loadStations()])-->

<!--  alertSse = new ReconnectingEventSource('/alerts/stream', {-->
<!--    onConnected:    () => { sseConnected.value = true },-->
<!--    onReconnecting: () => { sseConnected.value = false },-->
<!--    onAlert: (alert) => {-->
<!--      liveAlerts.value.unshift(alert)-->
<!--      if (liveAlerts.value.length > 20) liveAlerts.value.pop()-->
<!--      alerts.value.unshift(alert)-->
<!--    }-->
<!--  })-->
<!--})-->

<!--onUnmounted(() => alertSse?.destroy())-->

<!--async function loadAlerts() {-->
<!--  loading.value = true-->
<!--  try {-->
<!--    const { data } = await alertsApi.recent()-->
<!--    alerts.value = data-->
<!--  } finally {-->
<!--    loading.value = false-->
<!--  }-->
<!--}-->

<!--async function loadStations() {-->
<!--  const { data } = await alertsApi.stations()-->
<!--  stations.value = data-->
<!--}-->

<!--async function addStation() {-->
<!--  savingStation.value = true-->
<!--  try {-->
<!--    await alertsApi.createStation({ ...stationForm.value, active: true })-->
<!--    await loadStations()-->
<!--    showAddStation.value = false-->
<!--    stationForm.value = { name: '', address: '', phone: '', email: '', latitude: null, longitude: null }-->
<!--    toast.success('Station added')-->
<!--  } catch (e) {-->
<!--    toast.error('Failed to add station')-->
<!--  } finally {-->
<!--    savingStation.value = false-->
<!--  }-->
<!--}-->

<!--function shortId(id) { return id ? id.slice(0, 8) + '…' : '—' }-->
<!--function formatDate(ts) {-->
<!--  try { return format(new Date(ts), 'MMM d, HH:mm') } catch { return '—' }-->
<!--}-->
<!--function formatRelative(ts) {-->
<!--  try { return formatDistanceToNow(new Date(ts), { addSuffix: true }) } catch { return '' }-->
<!--}-->
<!--</script>-->

<!--<style scoped>-->
<!--.live-badge {-->
<!--  display: flex; align-items: center; gap: 6px;-->
<!--  padding: 5px 12px; border-radius: 20px;-->
<!--  font-size: 11px; font-weight: 700; letter-spacing: 0.5px;-->
<!--}-->
<!--.live-badge.live    { background: var(&#45;&#45;red-dim); color: var(&#45;&#45;red); }-->
<!--.live-badge.offline { background: var(&#45;&#45;bg-overlay); color: var(&#45;&#45;text-muted); }-->

<!--.alert-ticker {-->
<!--  display: flex;-->
<!--  align-items: flex-start;-->
<!--  gap: 12px;-->
<!--  background: var(&#45;&#45;bg-surface);-->
<!--  border: 1px solid rgba(239,68,68,0.2);-->
<!--  border-radius: var(&#45;&#45;radius-lg);-->
<!--  padding: 10px 14px;-->
<!--  margin-bottom: 20px;-->
<!--}-->
<!--.ticker-label {-->
<!--  display: flex; align-items: center; gap: 4px;-->
<!--  font-size: 10px; font-weight: 700; letter-spacing: 1px;-->
<!--  color: var(&#45;&#45;red); white-space: nowrap; padding-top: 2px;-->
<!--}-->
<!--.ticker-items { flex: 1; display: flex; flex-direction: column; gap: 4px; }-->
<!--.ticker-item {-->
<!--  display: flex; align-items: center; gap: 8px;-->
<!--  font-size: 12px;-->
<!--}-->
<!--.ticker-msg  { flex: 1; color: var(&#45;&#45;text-secondary); }-->
<!--.ticker-time { color: var(&#45;&#45;text-muted); font-size: 11px; white-space: nowrap; }-->

<!--.alerts-grid {-->
<!--  display: grid;-->
<!--  grid-template-columns: 1fr 340px;-->
<!--  gap: 16px;-->
<!--}-->

<!--.card-title-row {-->
<!--  display: flex; align-items: center;-->
<!--  justify-content: space-between;-->
<!--  margin-bottom: 14px;-->
<!--}-->
<!--.card-title {-->
<!--  font-size: 12px; font-weight: 600;-->
<!--  color: var(&#45;&#45;text-secondary);-->
<!--  text-transform: uppercase; letter-spacing: 0.5px;-->
<!--}-->

<!--.alert-list { display: flex; flex-direction: column; }-->
<!--.alert-item {-->
<!--  display: flex;-->
<!--  align-items: flex-start;-->
<!--  gap: 10px;-->
<!--  padding: 12px 0;-->
<!--  border-bottom: 1px solid var(&#45;&#45;border);-->
<!--}-->
<!--.alert-item:last-child { border-bottom: none; }-->

<!--.alert-icon {-->
<!--  width: 32px; height: 32px;-->
<!--  border-radius: var(&#45;&#45;radius);-->
<!--  display: flex; align-items: center; justify-content: center;-->
<!--  flex-shrink: 0;-->
<!--}-->
<!--.icon-red  { background: var(&#45;&#45;red-dim); color: var(&#45;&#45;red); }-->
<!--.icon-gray { background: var(&#45;&#45;bg-overlay); color: var(&#45;&#45;text-muted); }-->

<!--.alert-body { flex: 1; min-width: 0; }-->
<!--.alert-message { font-size: 13px; color: var(&#45;&#45;text-primary); margin-bottom: 4px; }-->
<!--.alert-meta { display: flex; flex-wrap: wrap; gap: 6px; }-->
<!--.meta-chip {-->
<!--  display: flex; align-items: center; gap: 3px;-->
<!--  font-size: 10px; color: var(&#45;&#45;text-muted);-->
<!--  background: var(&#45;&#45;bg-elevated);-->
<!--  padding: 2px 6px; border-radius: 3px;-->
<!--}-->

<!--.station-list { display: flex; flex-direction: column; gap: 1px; }-->
<!--.station-item {-->
<!--  display: flex; align-items: flex-start; gap: 10px;-->
<!--  padding: 10px;-->
<!--  border-radius: var(&#45;&#45;radius);-->
<!--  transition: background 0.12s;-->
<!--}-->
<!--.station-item:hover { background: var(&#45;&#45;bg-elevated); }-->
<!--.station-icon {-->
<!--  width: 34px; height: 34px;-->
<!--  background: var(&#45;&#45;blue-dim); color: var(&#45;&#45;blue);-->
<!--  border-radius: var(&#45;&#45;radius);-->
<!--  display: flex; align-items: center; justify-content: center;-->
<!--  flex-shrink: 0;-->
<!--}-->
<!--.station-body { flex: 1; min-width: 0; }-->
<!--.station-name { font-size: 13px; font-weight: 600; color: var(&#45;&#45;text-primary); }-->
<!--.station-meta { font-size: 11px; color: var(&#45;&#45;text-muted); margin-top: 2px; }-->
<!--.station-contacts { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 4px; }-->
<!--.contact-chip {-->
<!--  display: flex; align-items: center; gap: 3px;-->
<!--  font-size: 10px; color: var(&#45;&#45;text-secondary);-->
<!--  background: var(&#45;&#45;bg-elevated); padding: 2px 6px; border-radius: 3px;-->
<!--}-->

<!--/* Modal (reuse) */-->
<!--.modal-backdrop {-->
<!--  position: fixed; inset: 0; background: rgba(0,0,0,0.6);-->
<!--  display: flex; align-items: center; justify-content: center;-->
<!--  z-index: 200; backdrop-filter: blur(4px);-->
<!--}-->
<!--.modal {-->
<!--  background: var(&#45;&#45;bg-elevated); border: 1px solid var(&#45;&#45;border-mid);-->
<!--  border-radius: var(&#45;&#45;radius-lg); width: 100%; max-width: 520px;-->
<!--  box-shadow: var(&#45;&#45;shadow-md);-->
<!--}-->
<!--.modal-header {-->
<!--  display: flex; align-items: center; justify-content: space-between;-->
<!--  padding: 16px 20px; border-bottom: 1px solid var(&#45;&#45;border);-->
<!--  font-size: 14px; font-weight: 600;-->
<!--}-->
<!--.modal-body { padding: 20px; }-->
<!--.modal-footer {-->
<!--  display: flex; justify-content: flex-end; gap: 8px;-->
<!--  padding: 16px 20px; border-top: 1px solid var(&#45;&#45;border);-->
<!--}-->

<!--@media (max-width: 900px) {-->
<!--  .alerts-grid { grid-template-columns: 1fr; }-->
<!--}-->
<!--</style>-->
