<template>
  <div class="history-view">
    <div class="page-header">
      <div>
        <h1 class="page-title">Video History</h1>
        <p class="page-subtitle">Browse and playback recorded video segments</p>
      </div>
    </div>

    <!-- Search bar -->
    <div class="card search-bar">
      <div class="search-row">
        <div class="form-group">
          <label class="label">Camera</label>
          <select v-model="selectedCamera" class="input">
            <option value="">Select camera…</option>
            <option v-for="cam in cameras" :key="cam.id" :value="cam.id">{{ cam.name }}</option>
          </select>
        </div>
        <div class="form-group">
          <label class="label">From</label>
          <input v-model="fromDate" type="datetime-local" class="input" />
        </div>
        <div class="form-group">
          <label class="label">To</label>
          <input v-model="toDate" type="datetime-local" class="input" />
        </div>
        <button
          class="btn btn-primary"
          style="align-self:flex-end"
          @click="searchChunks"
          :disabled="!selectedCamera || searching"
        >
          <Search :size="14" />
          {{ searching ? 'Searching…' : 'Search' }}
        </button>
      </div>
    </div>

    <div class="history-body">
      <!-- Timeline / chunks list -->
      <div class="card chunks-panel">
        <div class="panel-header">
          <span class="panel-title">Video Segments</span>
          <span class="chunk-count" v-if="chunks.length">{{ chunks.length }} segments</span>
        </div>

        <div v-if="searching" class="empty-state"><span class="spinner"></span></div>
        <div v-else-if="!chunks.length && hasSearched" class="empty-state">
          <Film :size="28" />
          <p>No video segments found</p>
        </div>
        <div v-else-if="!hasSearched" class="empty-state">
          <Film :size="28" />
          <p>Select a camera and time range</p>
        </div>
        <div v-else class="chunk-list">
          <div
            v-for="chunk in chunks"
            :key="chunk.id"
            class="chunk-item"
            :class="{ active: selectedChunk?.id === chunk.id }"
            @click="selectChunk(chunk)"
          >
            <div class="chunk-thumb">
              <Video :size="16" />
            </div>
            <div class="chunk-info">
              <div class="chunk-time">{{ formatTime(chunk.startTime) }}</div>
              <div class="chunk-duration">
                {{ chunk.durationSec ? chunk.durationSec + 's' : '—' }}
                <span v-if="chunk.sizeBytes" class="text-muted">
                  · {{ formatSize(chunk.sizeBytes) }}
                </span>
              </div>
            </div>
            <a
              v-if="chunk.streamUrl"
              :href="chunk.streamUrl"
              target="_blank"
              class="btn btn-icon btn-ghost btn-sm"
              @click.stop
              title="Download"
            >
              <Download :size="12" />
            </a>
          </div>
        </div>
      </div>

      <!-- Video player -->
      <div class="card player-panel">
        <div class="panel-header">
          <span class="panel-title">Playback</span>
          <span v-if="selectedChunk" class="text-xs text-muted">
            {{ formatDate(selectedChunk.startTime) }} — {{ formatDate(selectedChunk.endTime) }}
          </span>
        </div>

        <div v-if="!selectedChunk" class="empty-state player-empty">
          <PlayCircle :size="48" />
          <p>Select a segment to play</p>
        </div>
        <div v-else class="player-wrapper">
          <video
            ref="videoRef"
            controls
            class="video-player"
            :src="selectedChunk.streamUrl"
            @loadstart="videoLoading = true"
            @canplay="videoLoading = false"
          >
            Your browser does not support the video tag.
          </video>
          <div v-if="videoLoading" class="video-loading">
            <span class="spinner"></span>
          </div>
          <div class="player-meta">
            <div class="meta-row">
              <span class="meta-label">Camera</span>
              <span>{{ currentCamera?.name || '—' }}</span>
            </div>
            <div class="meta-row">
              <span class="meta-label">Start</span>
              <span class="font-mono">{{ formatDate(selectedChunk.startTime) }}</span>
            </div>
            <div class="meta-row">
              <span class="meta-label">Duration</span>
              <span class="font-mono">{{ selectedChunk.durationSec }}s</span>
            </div>
            <div class="meta-row">
              <span class="meta-label">Size</span>
              <span class="font-mono">{{ formatSize(selectedChunk.sizeBytes) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Search, Film, Video, Download, PlayCircle } from 'lucide-vue-next'
import { useCamerasStore } from '@/stores/cameras'
import { format, subHours } from 'date-fns'

const cameraStore   = useCamerasStore()
const cameras       = computed(() => cameraStore.cameras)

const selectedCamera = ref('')
const fromDate       = ref(format(subHours(new Date(), 4), "yyyy-MM-dd'T'HH:mm"))
const toDate         = ref(format(new Date(), "yyyy-MM-dd'T'HH:mm"))
const chunks         = ref([])
const selectedChunk  = ref(null)
const searching      = ref(false)
const hasSearched    = ref(false)
const videoLoading   = ref(false)
const videoRef       = ref(null)

const currentCamera = computed(() =>
  cameras.value.find(c => c.id === selectedCamera.value)
)

onMounted(() => cameraStore.fetchCameras())

async function searchChunks() {
  if (!selectedCamera.value) return
  searching.value = true
  hasSearched.value = true
  try {
    const from = new Date(fromDate.value).toISOString()
    const to   = new Date(toDate.value).toISOString()
    const { data } = await historyApi.chunks(selectedCamera.value, from, to)
    chunks.value = data
    selectedChunk.value = null
  } finally {
    searching.value = false
  }
}

function selectChunk(chunk) {
  selectedChunk.value = chunk
  videoLoading.value  = true
  if (videoRef.value) {
    videoRef.value.load()
  }
}

function formatTime(ts) {
  try { return format(new Date(ts), 'HH:mm:ss') } catch { return '—' }
}
function formatDate(ts) {
  try { return format(new Date(ts), 'MMM d, HH:mm:ss') } catch { return '—' }
}
function formatSize(bytes) {
  if (!bytes) return '—'
  if (bytes > 1024 * 1024) return (bytes / 1024 / 1024).toFixed(1) + ' MB'
  return (bytes / 1024).toFixed(0) + ' KB'
}
</script>

<style scoped>
.search-bar { margin-bottom: 16px; }
.search-row {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  flex-wrap: wrap;
}
.search-row .form-group { min-width: 160px; flex: 1; }

.history-body {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 16px;
}

.panel-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 12px;
}
.panel-title {
  font-size: 12px; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.5px;
  color: var(--text-secondary);
}
.chunk-count {
  font-size: 11px;
  color: var(--text-muted);
  font-family: var(--font-mono);
}

.chunk-list { display: flex; flex-direction: column; gap: 2px; max-height: 500px; overflow-y: auto; }
.chunk-item {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 10px;
  border-radius: var(--radius);
  cursor: pointer;
  transition: background 0.1s;
}
.chunk-item:hover  { background: var(--bg-elevated); }
.chunk-item.active { background: var(--accent-dim); border: 1px solid rgba(245,158,11,0.3); }

.chunk-thumb {
  width: 32px; height: 32px;
  background: var(--bg-elevated);
  border-radius: var(--radius);
  display: flex; align-items: center; justify-content: center;
  color: var(--text-muted); flex-shrink: 0;
}
.chunk-item.active .chunk-thumb { background: var(--accent-dim); color: var(--accent); }

.chunk-info { flex: 1; min-width: 0; }
.chunk-time { font-family: var(--font-mono); font-size: 12px; font-weight: 600; color: var(--text-primary); }
.chunk-duration { font-size: 11px; color: var(--text-muted); }

/* Player */
.player-empty { min-height: 300px; }
.player-wrapper { display: flex; flex-direction: column; gap: 12px; }
.video-player {
  width: 100%;
  max-height: 400px;
  background: #000;
  border-radius: var(--radius);
  display: block;
}
.video-loading {
  display: flex; align-items: center; justify-content: center;
  height: 200px;
}
.player-meta {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}
.meta-row {
  display: flex; flex-direction: column; gap: 2px;
  padding: 8px 10px;
  background: var(--bg-elevated);
  border-radius: var(--radius);
}
.meta-label { font-size: 10px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.4px; }
.font-mono  { font-family: var(--font-mono); font-size: 12px; }
.text-xs    { font-size: 11px; }
.text-muted { color: var(--text-muted); }

@media (max-width: 900px) {
  .history-body { grid-template-columns: 1fr; }
}
</style>
