<template>
  <div class="app-layout">
    <!-- Sidebar -->
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-logo">
        <ShieldAlert :size="22" class="logo-icon" />
        <span v-if="!sidebarCollapsed" class="logo-text">GUARDIAN</span>
      </div>

      <nav class="sidebar-nav">
        <RouterLink
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: isActive(item.path) }"
        >
          <component :is="item.icon" :size="17" />
          <span v-if="!sidebarCollapsed" class="nav-label">{{ item.label }}</span>
          <span v-if="!sidebarCollapsed && item.badge" class="nav-badge">{{ item.badge }}</span>
        </RouterLink>
      </nav>

      <div class="sidebar-footer">
        <button class="nav-item" @click="sidebarCollapsed = !sidebarCollapsed">
          <PanelLeftClose v-if="!sidebarCollapsed" :size="17" />
          <PanelLeftOpen v-else :size="17" />
          <span v-if="!sidebarCollapsed">Collapse</span>
        </button>
      </div>
    </aside>

    <!-- Main content -->
    <div class="main-area">
      <!-- Top header -->
      <header class="topbar">
        <div class="topbar-left">
          <div class="breadcrumb">{{ currentRouteName }}</div>
        </div>
        <div class="topbar-right">

          <!-- User menu -->
          <div class="user-menu" @click="showUserMenu = !showUserMenu" ref="userMenuRef">
            <div class="user-avatar">{{ userInitials }}</div>
            <span class="user-name">{{ auth.user?.fullName || auth.user?.username }}</span>
            <ChevronDown :size="14" />
            <div v-if="showUserMenu" class="user-dropdown">
              <div class="user-dropdown-header">
                <div class="font-medium">{{ auth.user?.username }}</div>
                <div class="font-medium"></div>
                <div class="text-muted text-xs">{{ auth.user?.role }}</div>
                <div class="text-muted text-xs"></div>
              </div>
              <RouterLink to="/settings" class="dropdown-item">
                <Settings :size="14" /> Settings
              </RouterLink>
              <button class="dropdown-item danger" @click="handleLogout">
                <LogOut :size="14" /> Sign Out
              </button>
            </div>
          </div>
        </div>
      </header>

      <!-- Page content -->
      <main class="page-content">
        <RouterView v-slot="{ Component }">
          <Transition name="fade" mode="out-in">
            <component :is="Component" />
          </Transition>
        </RouterView>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute, RouterLink, RouterView } from 'vue-router'
import {
  ShieldAlert, LayoutDashboard, Camera, AlertTriangle, Bell,
  BarChart3, History, Settings, LogOut, ChevronDown,
  PanelLeftClose, PanelLeftOpen
} from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import { useIncidentsStore } from '@/stores/incidents'
import { ReconnectingEventSource } from '@/services/sse'
import { useToast } from 'vue-toastification'

const router  = useRouter()
const route   = useRoute()
const auth    = useAuthStore()
const incidentsStore = useIncidentsStore()
const toast   = useToast()

const sidebarCollapsed = ref(false)
const showUserMenu     = ref(false)
const userMenuRef      = ref(null)
const sseConnected     = ref(false)
const newAlertCount    = ref(0)

const navItems = computed(() => [
  { path: '/dashboard',  label: 'Dashboard',  icon: LayoutDashboard },
  { path: '/incidents',  label: 'Incidents',  icon: AlertTriangle,
    badge: incidentsStore.summary.newCount > 0 ? incidentsStore.summary.newCount : null },
  { path: '/cameras',    label: 'Cameras',    icon: Camera },
  // { path: '/alerts',     label: 'Alerts',     icon: Bell,
  //   badge: newAlertCount.value > 0 ? newAlertCount.value : null },
  // { path: '/history',    label: 'History',    icon: History },
  // { path: '/statistics', label: 'Statistics', icon: BarChart3 },
  ...(auth.isAdmin ? [{ path: '/settings', label: 'Settings', icon: Settings }] : [])
])

const currentRouteName = computed(() => route.name || 'Dashboard')

const userInitials = computed(() => {
  return "";
  const name = auth.user?.fullName || auth.user?.username || '?'
  return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
})

function isActive(path) {
  return route.path === path || route.path.startsWith(path + '/')
}

async function handleLogout() {
  await auth.logout()
  router.push('/login')
}

// Close user menu on outside click
onMounted(() => {
  document.addEventListener('click', (e) => {
    if (userMenuRef.value && !userMenuRef.value.contains(e.target)) {
      showUserMenu.value = false
    }
  })
})

// SSE connections
let incidentSse, alertSse

onMounted(async () => {
  await incidentsStore.fetchSummary()

  incidentSse = new ReconnectingEventSource('/incidents/stream', {
    onConnected: () => { sseConnected.value = true },
    onReconnecting: () => { sseConnected.value = false },
    onFailed: () => { sseConnected.value = false },
    onIncident: (incident) => {
      incidentsStore.pushLiveIncident(incident)
      toast.warning(`New incident: ${incident.incidentType}`, { timeout: 5000 })
    }
  })

  alertSse = new ReconnectingEventSource('/alerts/stream', {
    onAlert: (alert) => {
      newAlertCount.value++
      toast.error(`🚨 Alert dispatched!`, { timeout: 8000 })
    }
  })
})

onUnmounted(() => {
  incidentSse?.destroy()
  alertSse?.destroy()
})
</script>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

/* ── Sidebar ─────────────────────────────────────────────── */
.sidebar {
  width: var(--sidebar-w);
  background: var(--bg-surface);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  transition: width 0.2s ease;
  flex-shrink: 0;
  overflow: hidden;
}
.sidebar.collapsed { width: 56px; }

.sidebar-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 16px;
  height: var(--header-h);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}
.logo-icon { color: var(--accent); flex-shrink: 0; }
.logo-text {
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 2px;
  color: var(--text-primary);
  white-space: nowrap;
}

.sidebar-nav {
  flex: 1;
  padding: 12px 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 10px;
  border-radius: var(--radius);
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  background: none;
  border: none;
  width: 100%;
  text-align: left;
  text-decoration: none;
  transition: background 0.12s, color 0.12s;
  white-space: nowrap;
}
.nav-item:hover { background: var(--bg-elevated); color: var(--text-primary); text-decoration: none; }
.nav-item.active {
  background: var(--accent-dim);
  color: var(--accent);
}
.nav-item.active svg { color: var(--accent); }
.nav-label { flex: 1; }
.nav-badge {
  background: var(--red);
  color: white;
  font-size: 10px;
  font-weight: 700;
  padding: 1px 5px;
  border-radius: 10px;
  min-width: 18px;
  text-align: center;
}

.sidebar-footer {
  padding: 8px;
  border-top: 1px solid var(--border);
}

/* ── Main area ───────────────────────────────────────────── */
.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.topbar {
  height: var(--header-h);
  background: var(--bg-surface);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  flex-shrink: 0;
}
.breadcrumb {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.topbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.live-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.3px;
}
.live-indicator.connected { background: var(--green-dim); color: var(--green); }
.live-indicator.disconnected { background: var(--bg-overlay); color: var(--text-muted); }

.topbar-btn {
  position: relative;
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.12s;
}
.topbar-btn:hover { color: var(--text-primary); background: var(--bg-overlay); }
.alert-dot {
  position: absolute;
  top: -4px; right: -4px;
  background: var(--red);
  color: white;
  font-size: 9px;
  font-weight: 700;
  width: 16px; height: 16px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-menu {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 10px 4px 4px;
  border-radius: var(--radius);
  cursor: pointer;
  position: relative;
  border: 1px solid transparent;
  transition: all 0.12s;
}
.user-menu:hover { background: var(--bg-elevated); border-color: var(--border); }
.user-avatar {
  width: 28px; height: 28px;
  border-radius: 50%;
  background: var(--accent-dim);
  color: var(--accent);
  font-size: 11px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}
.user-name { font-size: 13px; font-weight: 500; }

.user-dropdown {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  background: var(--bg-elevated);
  border: 1px solid var(--border-mid);
  border-radius: var(--radius-lg);
  min-width: 180px;
  box-shadow: var(--shadow-md);
  z-index: 100;
  overflow: hidden;
}
.user-dropdown-header {
  padding: 12px 14px;
  border-bottom: 1px solid var(--border);
}
.dropdown-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  font-size: 13px;
  color: var(--text-secondary);
  cursor: pointer;
  background: none;
  border: none;
  width: 100%;
  text-align: left;
  text-decoration: none;
  transition: all 0.12s;
}
.dropdown-item:hover { background: var(--bg-overlay); color: var(--text-primary); text-decoration: none; }
.dropdown-item.danger:hover { color: var(--red); background: var(--red-dim); }

.page-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.text-muted { color: var(--text-muted); }
.text-xs { font-size: 11px; }
.font-medium { font-weight: 500; }
</style>
