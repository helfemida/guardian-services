import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { incidentsApi } from '@/services/endpoints'

export const useIncidentsStore = defineStore('incidents', () => {
  const incidents = ref([])
  const loading = ref(false)
  const total = ref(0)
  const page = ref(0)
  const pageSize = ref(20)
  const filters = ref({ status: null })
  const liveFeed = ref([])

  const summary = computed(() => {
    const pending = incidents.value.filter(i => i.status === 'PENDING').length
    const confirmed = incidents.value.filter(i => i.status === 'CONFIRMED').length
    const falsePositive = incidents.value.filter(i => i.status === 'FALSE_POSITIVE').length

    return {
      total: incidents.value.length,
      newCount: pending,
      pending,
      confirmed,
      falsePositive
    }
  })

  const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

  async function fetchIncidents(params = {}) {
    loading.value = true
    try {
      const { data } = await incidentsApi.list({
        ...filters.value,
        ...params
      })

      const list = Array.isArray(data) ? data : data.content || []

      incidents.value = list
      total.value = Array.isArray(data) ? list.length : data.totalElements || data.total || list.length
    } finally {
      loading.value = false
    }
  }

  async function fetchIncident(id) {
    const { data } = await incidentsApi.get(id)
    return data
  }

  async function updateIncident(id, confirmed) {
    const { data } = await incidentsApi.resolve(id, {
     confirmed
    })

    const idx = incidents.value.findIndex(i => i.id === id)
    if (idx !== -1) incidents.value[idx] = data

    return data
  }

  function pushLiveIncident(incident) {
    liveFeed.value.unshift(incident)
    incidents.value.unshift(incident)
    total.value++

    if (liveFeed.value.length > 50) liveFeed.value.pop()
  }

  return {
    incidents,
    loading,
    total,
    page,
    pageSize,
    filters,
    liveFeed,
    summary,
    totalPages,
    fetchIncidents,
    fetchIncident,
    updateIncident,
    pushLiveIncident
  }
})