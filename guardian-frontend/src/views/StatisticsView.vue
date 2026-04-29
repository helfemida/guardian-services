<!--<template>-->
<!--  <div class="statistics-view">-->
<!--    <div class="page-header">-->
<!--      <div>-->
<!--        <h1 class="page-title">Statistics</h1>-->
<!--        <p class="page-subtitle">Analytics & incident trends</p>-->
<!--      </div>-->
<!--      <div style="display:flex;gap:8px;align-items:center">-->
<!--        <select v-model="dateRange" class="input" style="width:160px" @change="loadAll">-->
<!--          <option value="7">Last 7 days</option>-->
<!--          <option value="30">Last 30 days</option>-->
<!--          <option value="90">Last 90 days</option>-->
<!--        </select>-->
<!--      </div>-->
<!--    </div>-->

<!--    &lt;!&ndash; KPI row &ndash;&gt;-->
<!--    <div class="grid-4" style="margin-bottom:20px">-->
<!--      <StatCard label="Total Incidents"  :value="dash.totalIncidents"  :icon="AlertTriangle" color="orange" />-->
<!--      <StatCard label="Open Incidents"   :value="dash.openIncidents"   :icon="Bell"          color="red" />-->
<!--      <StatCard label="Last 24h"         :value="dash.incidentsLast24h" :icon="Clock"        color="blue" />-->
<!--      <StatCard label="Last 7 days"      :value="dash.incidentsLast7d" :icon="TrendingUp"    color="amber" />-->
<!--    </div>-->

<!--    &lt;!&ndash; Charts row &ndash;&gt;-->
<!--    <div class="grid-2" style="margin-bottom:20px">-->
<!--      &lt;!&ndash; Time series &ndash;&gt;-->
<!--      <div class="card">-->
<!--        <div class="chart-header">-->
<!--          <span class="chart-title">Incident Trend</span>-->
<!--          <div style="display:flex;gap:4px">-->
<!--            <button v-for="iv in ['hour','day','week']" :key="iv"-->
<!--              class="btn btn-sm btn-ghost" :class="{ 'btn-secondary': interval === iv }"-->
<!--              @click="setInterval(iv)">{{ iv }}-->
<!--            </button>-->
<!--          </div>-->
<!--        </div>-->
<!--        <div style="height:200px;position:relative">-->
<!--          <Line v-if="lineData.labels?.length" :data="lineData" :options="lineOptions" />-->
<!--          <div v-else class="empty-state"><span class="spinner"></span></div>-->
<!--        </div>-->
<!--      </div>-->

<!--      &lt;!&ndash; Doughnut breakdown &ndash;&gt;-->
<!--      <div class="card">-->
<!--        <div class="chart-header">-->
<!--          <span class="chart-title">Incident Type Breakdown</span>-->
<!--        </div>-->
<!--        <div class="doughnut-wrapper">-->
<!--          <div style="height:200px;width:200px;position:relative">-->
<!--            <Doughnut v-if="doughnutData.labels?.length" :data="doughnutData" :options="doughnutOptions" />-->
<!--          </div>-->
<!--          <div class="legend">-->
<!--            <div v-for="(label, i) in doughnutData.labels" :key="label" class="legend-item">-->
<!--              <span class="legend-dot" :style="{ background: doughnutColors[i] }"></span>-->
<!--              <span class="legend-label">{{ formatType(label) }}</span>-->
<!--              <span class="legend-count">{{ doughnutData.datasets[0]?.data[i] }}</span>-->
<!--            </div>-->
<!--          </div>-->
<!--        </div>-->
<!--      </div>-->
<!--    </div>-->

<!--    &lt;!&ndash; Top cameras table &ndash;&gt;-->
<!--    <div class="card" style="margin-bottom:20px">-->
<!--      <div class="chart-header" style="margin-bottom:14px">-->
<!--        <span class="chart-title">Top Cameras by Incidents</span>-->
<!--      </div>-->
<!--      <div class="table-wrapper">-->
<!--        <table class="table">-->
<!--          <thead>-->
<!--            <tr>-->
<!--              <th>#</th>-->
<!--              <th>Camera</th>-->
<!--              <th>Building</th>-->
<!--              <th>Floor</th>-->
<!--              <th>Total</th>-->
<!--              <th>Harassment</th>-->
<!--              <th>Harassment %</th>-->
<!--            </tr>-->
<!--          </thead>-->
<!--          <tbody>-->
<!--            <tr v-for="(cam, idx) in topCameras" :key="cam.cameraId">-->
<!--              <td class="text-muted font-mono">{{ idx + 1 }}</td>-->
<!--              <td class="font-medium">{{ cam.cameraName }}</td>-->
<!--              <td class="text-muted">{{ cam.building || '—' }}</td>-->
<!--              <td class="text-muted">{{ cam.floor ?? '—' }}</td>-->
<!--              <td><span class="badge badge-orange">{{ cam.incidentCount }}</span></td>-->
<!--              <td><span class="badge badge-red">{{ cam.harassmentCount }}</span></td>-->
<!--              <td>-->
<!--                <ConfidenceBar-->
<!--                  :value="cam.incidentCount > 0 ? cam.harassmentCount / cam.incidentCount : 0"-->
<!--                />-->
<!--              </td>-->
<!--            </tr>-->
<!--            <tr v-if="!topCameras.length">-->
<!--              <td colspan="7" class="text-center text-muted">No data available</td>-->
<!--            </tr>-->
<!--          </tbody>-->
<!--        </table>-->
<!--      </div>-->
<!--    </div>-->

<!--    &lt;!&ndash; Heatmap placeholder &ndash;&gt;-->
<!--    <div class="card">-->
<!--      <div class="chart-header" style="margin-bottom:14px">-->
<!--        <span class="chart-title">Incident Heatmap</span>-->
<!--        <span class="text-muted text-xs">Geographical incident density</span>-->
<!--      </div>-->
<!--      <div class="heatmap-container" id="heatmap-map"></div>-->
<!--    </div>-->
<!--  </div>-->
<!--</template>-->

<!--<script setup>-->
<!--import { ref, computed, onMounted } from 'vue'-->
<!--import { Line, Doughnut } from 'vue-chartjs'-->
<!--import {-->
<!--  Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement,-->
<!--  ArcElement, Filler, Tooltip, Legend-->
<!--} from 'chart.js'-->
<!--import { AlertTriangle, Bell, Clock, TrendingUp } from 'lucide-vue-next'-->
<!--import { statisticsApi } from '@/services/endpoints'-->
<!--import StatCard       from '@/components/common/StatCard.vue'-->
<!--import ConfidenceBar  from '@/components/common/ConfidenceBar.vue'-->
<!--import { format, subDays } from 'date-fns'-->

<!--ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, ArcElement, Filler, Tooltip, Legend)-->

<!--const dateRange = ref(30)-->
<!--const interval  = ref('day')-->
<!--const dash      = ref({ totalIncidents: 0, openIncidents: 0, incidentsLast24h: 0, incidentsLast7d: 0 })-->
<!--const timeSeries = ref([])-->
<!--const breakdown  = ref([])-->
<!--const topCameras = ref([])-->
<!--const heatmapPts = ref([])-->

<!--const doughnutColors = [-->
<!--  'var(&#45;&#45;red)', 'var(&#45;&#45;orange)', 'var(&#45;&#45;accent)',-->
<!--  'var(&#45;&#45;blue)', 'var(&#45;&#45;purple)', 'var(&#45;&#45;green)', 'var(&#45;&#45;text-muted)'-->
<!--]-->

<!--function dateParams() {-->
<!--  return {-->
<!--    from: subDays(new Date(), Number(dateRange.value)).toISOString(),-->
<!--    to: new Date().toISOString()-->
<!--  }-->
<!--}-->

<!--async function loadAll() {-->
<!--  const params = dateParams()-->
<!--  const [dashRes, tsRes, bdRes, tcRes, hmRes] = await Promise.all([-->
<!--    statisticsApi.dashboard(),-->
<!--    statisticsApi.timeseries({ ...params, interval: interval.value }),-->
<!--    statisticsApi.breakdown(params),-->
<!--    statisticsApi.topCameras(10),-->
<!--    statisticsApi.heatmap(params)-->
<!--  ])-->
<!--  dash.value       = dashRes.data-->
<!--  timeSeries.value = tsRes.data-->
<!--  breakdown.value  = bdRes.data-->
<!--  topCameras.value = tcRes.data-->
<!--  heatmapPts.value = hmRes.data-->
<!--}-->

<!--async function setInterval(iv) {-->
<!--  interval.value = iv-->
<!--  const params   = dateParams()-->
<!--  const { data } = await statisticsApi.timeseries({ ...params, interval: iv })-->
<!--  timeSeries.value = data-->
<!--}-->

<!--onMounted(loadAll)-->

<!--// Line chart-->
<!--const lineData = computed(() => {-->
<!--  if (!timeSeries.value.length) return { labels: [], datasets: [] }-->
<!--  const fmt   = interval.value === 'hour' ? 'HH:mm' : interval.value === 'week' ? 'MMM d' : 'MMM d'-->
<!--  const labels = [...new Set(timeSeries.value.map(p => format(new Date(p.bucket), fmt)))]-->
<!--  const data   = labels.map(l => timeSeries.value-->
<!--    .filter(p => format(new Date(p.bucket), fmt) === l)-->
<!--    .reduce((s, p) => s + (p.count || 0), 0))-->
<!--  return {-->
<!--    labels,-->
<!--    datasets: [{-->
<!--      label: 'Incidents',-->
<!--      data,-->
<!--      borderColor: 'rgba(245,158,11,0.9)',-->
<!--      backgroundColor: 'rgba(245,158,11,0.1)',-->
<!--      fill: true,-->
<!--      tension: 0.4,-->
<!--      pointRadius: 3,-->
<!--      pointBackgroundColor: 'rgba(245,158,11,1)'-->
<!--    }]-->
<!--  }-->
<!--})-->

<!--const lineOptions = {-->
<!--  responsive: true, maintainAspectRatio: false,-->
<!--  plugins: { legend: { display: false } },-->
<!--  scales: {-->
<!--    x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#8b92a8', maxTicksLimit: 10 } },-->
<!--    y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#8b92a8', precision: 0 } }-->
<!--  }-->
<!--}-->

<!--const doughnutData = computed(() => {-->
<!--  if (!breakdown.value.length) return { labels: [], datasets: [] }-->
<!--  return {-->
<!--    labels: breakdown.value.map(b => b.type),-->
<!--    datasets: [{-->
<!--      data: breakdown.value.map(b => b.count),-->
<!--      backgroundColor: doughnutColors,-->
<!--      borderColor: 'rgba(0,0,0,0)',-->
<!--      borderWidth: 0-->
<!--    }]-->
<!--  }-->
<!--})-->

<!--const doughnutOptions = {-->
<!--  responsive: true, maintainAspectRatio: false,-->
<!--  plugins: {-->
<!--    legend: { display: false },-->
<!--    tooltip: {-->
<!--      callbacks: {-->
<!--        label: (ctx) => ` ${ctx.label}: ${ctx.raw}`-->
<!--      }-->
<!--    }-->
<!--  },-->
<!--  cutout: '68%'-->
<!--}-->

<!--function formatType(t) { return t?.replace(/_/g, ' ') || t }-->
<!--</script>-->

<!--<style scoped>-->
<!--.chart-header {-->
<!--  display: flex;-->
<!--  align-items: center;-->
<!--  justify-content: space-between;-->
<!--  margin-bottom: 16px;-->
<!--  flex-wrap: wrap;-->
<!--  gap: 8px;-->
<!--}-->
<!--.chart-title {-->
<!--  font-size: 12px;-->
<!--  font-weight: 600;-->
<!--  text-transform: uppercase;-->
<!--  letter-spacing: 0.5px;-->
<!--  color: var(&#45;&#45;text-secondary);-->
<!--}-->

<!--.doughnut-wrapper {-->
<!--  display: flex;-->
<!--  align-items: center;-->
<!--  gap: 20px;-->
<!--  flex-wrap: wrap;-->
<!--}-->
<!--.legend {-->
<!--  flex: 1;-->
<!--  display: flex;-->
<!--  flex-direction: column;-->
<!--  gap: 7px;-->
<!--  min-width: 140px;-->
<!--}-->
<!--.legend-item {-->
<!--  display: flex;-->
<!--  align-items: center;-->
<!--  gap: 8px;-->
<!--  font-size: 12px;-->
<!--}-->
<!--.legend-dot {-->
<!--  width: 8px; height: 8px;-->
<!--  border-radius: 50%;-->
<!--  flex-shrink: 0;-->
<!--}-->
<!--.legend-label { flex: 1; color: var(&#45;&#45;text-secondary); }-->
<!--.legend-count { font-family: var(&#45;&#45;font-mono); font-size: 11px; color: var(&#45;&#45;text-muted); }-->

<!--.heatmap-container {-->
<!--  height: 350px;-->
<!--  background: var(&#45;&#45;bg-elevated);-->
<!--  border-radius: var(&#45;&#45;radius);-->
<!--  display: flex;-->
<!--  align-items: center;-->
<!--  justify-content: center;-->
<!--  color: var(&#45;&#45;text-muted);-->
<!--  font-size: 13px;-->
<!--  border: 1px dashed var(&#45;&#45;border-mid);-->
<!--  position: relative;-->
<!--  overflow: hidden;-->
<!--}-->
<!--.heatmap-container::after {-->
<!--  content: 'Map view — integrate with Leaflet heatmap layer using heatmapPts data';-->
<!--  position: absolute;-->
<!--  text-align: center;-->
<!--  padding: 20px;-->
<!--}-->

<!--.text-center { text-align: center; }-->
<!--.text-muted  { color: var(&#45;&#45;text-muted); }-->
<!--.text-xs     { font-size: 11px; }-->
<!--.font-mono   { font-family: var(&#45;&#45;font-mono); }-->
<!--.font-medium { font-weight: 500; }-->
<!--</style>-->
