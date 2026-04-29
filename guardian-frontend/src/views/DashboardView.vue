<template><div class='dashboard'>
<div class='page-header'><div><h1 class='page-title'>Dashboard</h1><p class='page-subtitle'>Real-time surveillance overview</p></div></div>
<div class='grid-4' style='margin-bottom:20px'>
<div class='card'><div>Total Incidents</div><h2>{{stats.total}}</h2></div>
<div class='card'><div>Open / New</div><h2>{{stats.pending}}</h2></div>
<div class='card'><div>Last 24 Hours</div><h2>{{stats.last24}}</h2></div>
<div class='card'><div>Cameras Online</div><h2>{{stats.online}}</h2></div>
</div>
<div class='card'>
<div class='card-header'><span class='card-title'>Live Feed</span></div>
<div class='table-wrapper'><table class='table'><thead><tr><th>Severity</th><th>Camera / Facility</th><th>Status</th><th>Reviewed By</th><th>Actions</th></tr></thead>
<tbody><tr v-for='i in incidents' :key='i.id' @click='openModal(i)' style='cursor:pointer'>
<td>{{i.severity}}</td><td>{{i.camera?.name||'-'}}<br><small>{{i.camera?.facility||'-'}}</small></td><td>{{i.status}}</td><td>{{i.reviewedBy?.name||'-'}}</td>
<td @click.stop><button class='btn btn-sm btn-primary' @click='resolve(i,true)'>Confirm</button> <button class='btn btn-sm btn-danger' @click='resolve(i,false)'>False Positive</button></td>
</tr></tbody></table></div></div>
<div v-if='selected' class='modal-backdrop' @click='selected=null'><div class='modal card' @click.stop>
<h3>Incident Details</h3>
<video v-if='videoUrl' :src='videoUrl' controls autoplay style='width:100%;max-height:360px'></video>
<div class='grid-2'>
<div>Confidence: {{selected.confidenceScore}}</div><div>Status: {{selected.status}}</div>
<div>Reviewed At: {{selected.reviewedAt}}</div><div>Created: {{selected.createdAt}}</div>
<div>Source Alert: {{selected.sourceAlertId}}</div><div>Camera: {{selected.camera?.name}}</div>
</div></div></div>
</div></template>
<script setup>
import {ref,onMounted,computed} from 'vue';import {incidentsApi,camerasApi} from '@/services/endpoints'
const incidents=ref([]),online=ref(0),selected=ref(null)
const stats=computed(()=>{const now=Date.now();return{total:incidents.value.length,pending:incidents.value.filter(x=>x.status==='PENDING').length,last24:incidents.value.filter(x=>x.status==='PENDING' && now-new Date(x.createdAt).getTime()<86400000).length,online:online.value}})
const videoUrl=computed(()=>selected.value?.minioUrl||'')
async function load(){incidents.value=(await incidentsApi.list()).data;online.value=((await camerasApi.stats()).data||[]).length}
async function resolve(row,val){await incidentsApi.resolve(row.id,val);await load()}
function openModal(r){selected.value=r}
onMounted(load)
</script>
<style scoped>.modal-backdrop{position:fixed;inset:0;background:#0008;display:flex;align-items:center;justify-content:center;padding:20px}.modal{max-width:800px;width:100%}</style>
