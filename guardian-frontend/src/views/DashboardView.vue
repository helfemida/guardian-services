<template><div class='dashboard'>
<div class='page-header'><div><h1 class='page-title'>Dashboard</h1><p class='page-subtitle'>Real-time surveillance overview</p></div></div>
<div class='grid-4' style='margin-bottom:20px'>
<div class='card'><div>Total Incidents</div><h2>{{stats.total}}</h2></div>
<div class='card'><div>Open / New</div><h2>{{stats.pending}}</h2></div>
<div class='card'><div>Last 24 Hours</div><h2>{{stats.last24}}</h2></div>
<div class='card'><div>Cameras Online</div><h2>{{stats.online}}</h2></div>
</div></div></template>


<script setup>
import {computed, onMounted, ref} from 'vue';
import {camerasApi, incidentsApi} from '@/services/endpoints'

const incidents=ref([]),online=ref(0),selected=ref(null)
const stats=computed(()=>{const now=Date.now();return{total:incidents.value.length,pending:incidents.value.filter(x=>x.status==='PENDING').length,last24:incidents.value.filter(x=>x.status==='PENDING' && now-new Date(x.createdAt).getTime()<86400000).length,online:online.value}})
const videoUrl=computed(()=>selected.value?.minioUrl||'')
async function load(){incidents.value=(await incidentsApi.list()).data;online.value=((await camerasApi.stats()).data||[]).length}
async function resolve(row,val){await incidentsApi.resolve(row.id,val);await load()}
function openModal(r){selected.value=r}
onMounted(load)
</script>
<style scoped>.modal-backdrop{position:fixed;inset:0;background:#0008;display:flex;align-items:center;justify-content:center;padding:20px}.modal{max-width:800px;width:100%}</style>
<script setup>
</script>