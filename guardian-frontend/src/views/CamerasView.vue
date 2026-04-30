<!-- CameraDetailsView.vue -->
<template>
  <div>
    <div class="page-header">
      <h1 class="page-title">Cameras</h1>
    </div>

    <div class="camera-grid">
      <div class="card camera-card" v-for="c in cams" :key="c.id">
        <div class="camera-title">{{ c.name }}</div>

        <iframe
            :src="getStreamUrl(c)"
            class="video"/>

        <div class="camera-meta">
          {{ c.facility?.name || 'No facility' }}
        </div>

        <router-link class="btn btn-sm btn-primary" :to="`/cameras/${c.id}`">
          Open
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { camerasApi } from '@/services/endpoints'

const cams = ref([])

onMounted(async () => {
  const { data } = await camerasApi.list()
  cams.value = data || []
})

function getStreamUrl(camera) {
  return "http://localhost:8889/camera1/"
}
</script>

<style scoped>
.camera-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.camera-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.camera-title {
  font-weight: 700;
}

.camera-meta {
  color: var(--text-muted);
  font-size: 13px;
}

.empty-video {
  height: 180px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #111;
  color: #777;
}

@media (max-width: 1200px) {
  .camera-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>