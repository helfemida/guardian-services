<!-- CameraDetailsView.vue -->
<template>
  <div>
    <div class="page-header">
      <h1 class="page-title">Cameras</h1>
    </div>

    <div class="camera-grid">
      <div class="card camera-card" v-for="c in cams" :key="c.id">
        <div class="camera-title">{{ c.name }}</div>

        <video ref="videoPlayer" controls autoplay muted style="width:100%" class="video-js"></video>



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
import Hls from 'hls.js';


const cams = ref([])
const videoPlayer = ref(null);
const streamUrl = 'http://localhost:8888/camera1/index.m3u8';
let hls;

onMounted(() => {
  if (Hls.isSupported()) {
    hls = new Hls();
    hls.loadSource(streamUrl);
    hls.attachMedia(videoPlayer.value);
  } else if (videoPlayer.value.canPlayType('application/vnd.apple.mpegurl')) {
    videoPlayer.value.src = streamUrl;
  }
});

function getStreamUrl() {
  return "http://localhost:8888/camera1/index.m3u8?cookieCheck=1"
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