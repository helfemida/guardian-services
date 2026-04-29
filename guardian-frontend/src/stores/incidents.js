import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { incidentsApi } from '@/services/endpoints'

export const useIncidentsStore = defineStore('incidents', () => {
  const incidents = ref([])
  const summary   = ref({ total: 0, newCount: 0, last24h: 0, resolved: 0 })
  const loading   = ref(false)
  const total     = ref(0)
  const page      = ref(0)
  const pageSize  = ref(20)
  const filters   = ref({ status: null, type: null, cameraId: null })

  // Live feed buffer (SSE pushed incidents)
  const liveFeed  = ref([])

  const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

  async function fetchIncidents(params = {}) {
    loading.value = true
    try {
      const { data } = await incidentsApi.list({
        page: page.value,
        size: pageSize.value,
        ...filters.value,
        ...params
      })
      incidents.value = data.content
      total.value     = data.total
    } finally {
      loading.value = false
    }
  }

  async function fetchSummary() {
    const { data } = await incidentsApi.list()
    summary.value = data
  }

  async function updateIncident(id, payload) {
    const { data } = await incidentsApi.resolve(id, null)
    const idx = incidents.value.findIndex(i => i.id === id)
    if (idx !== -1) incidents.value[idx] = data
    return data
  }

  function pushLiveIncident(incident) {
    liveFeed.value.unshift(incident)
    if (liveFeed.value.length > 50) liveFeed.value.pop()
    // Also bump summary counter
    summary.value.newCount++
    summary.value.total++
    summary.value.last24h++
  }

  return {
    incidents, summary, loading, total, page, pageSize, filters, liveFeed,
    totalPages,
    fetchIncidents, fetchSummary, updateIncident, pushLiveIncident
  }
})
