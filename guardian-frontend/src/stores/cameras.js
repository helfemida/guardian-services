import { defineStore } from 'pinia'
import { ref } from 'vue'
import { camerasApi } from '@/services/endpoints'

export const useCamerasStore = defineStore('cameras', () => {
  const cameras = ref([])
  const stats   = ref({ total: 0, online: 0, offline: 0, error: 0 })
  const loading = ref(false)

  async function fetchCameras(params = {}) {
    loading.value = true
    try {
      const { data } = await camerasApi.list(params)
      cameras.value = data
    } finally {
      loading.value = false
    }
  }

  async function fetchStats() {
    const { data } = await camerasApi.stats()
    stats.value = data
  }

  async function createCamera(payload) {
    const { data } = await camerasApi.create(payload)
    cameras.value.push(data)
    return data
  }

  async function updateCamera(id, payload) {
    const { data } = await camerasApi.update(id, payload)
    const idx = cameras.value.findIndex(c => c.id === id)
    if (idx !== -1) cameras.value[idx] = data
    return data
  }

  async function deleteCamera(id) {
    await camerasApi.delete(id)
    cameras.value = cameras.value.filter(c => c.id !== id)
  }

  async function updateStatus(id, status) {
    const { data } = await camerasApi.updateStatus(id, status)
    const idx = cameras.value.findIndex(c => c.id === id)
    if (idx !== -1) cameras.value[idx] = data
    return data
  }

  return {
    cameras, stats, loading,
    fetchCameras, fetchStats, createCamera, updateCamera, deleteCamera, updateStatus
  }
})
