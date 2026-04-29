<template>
  <div class="settings-view">
    <div class="page-header">
      <div>
        <h1 class="page-title">Settings</h1>
        <p class="page-subtitle">System configuration & user management</p>
      </div>
    </div>

    <div class="settings-grid">
      <!-- User management -->
      <div class="card">
        <div class="section-header">
          <span class="section-title">Users</span>
          <button class="btn btn-primary btn-sm" @click="showAddUser = true">
            <UserPlus :size="13" /> Add User
          </button>
        </div>

        <div class="table-wrapper">
          <table class="table">
            <thead>
              <tr>
                <th>User</th>
                <th>Email</th>
                <th>Role</th>
                <th>Status</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="user in users" :key="user.id">
                <td>
                  <div class="user-cell">
                    <div class="user-avatar-sm">{{ initials(user.fullName || user.username) }}</div>
                    <span>{{ user.fullName || user.username }}</span>
                  </div>
                </td>
                <td class="text-muted">{{ user.email }}</td>
                <td><span class="badge" :class="roleBadge(user.role)">{{ user.role }}</span></td>
                <td>
                  <span class="badge" :class="user.enabled ? 'badge-green' : 'badge-gray'">
                    {{ user.enabled ? 'Active' : 'Disabled' }}
                  </span>
                </td>
                <td class="text-muted text-xs font-mono">{{ formatDate(user.createdAt) }}</td>
              </tr>
              <tr v-if="!users.length">
                <td colspan="5" class="text-center text-muted">Loading users…</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Change password -->
      <div class="card">
        <div class="section-header">
          <span class="section-title">Change Password</span>
        </div>
        <div class="form-stack">
          <div class="form-group">
            <label class="label">Current Password</label>
            <input v-model="pwForm.currentPassword" type="password" class="input" />
          </div>
          <div class="form-group">
            <label class="label">New Password</label>
            <input v-model="pwForm.newPassword" type="password" class="input" />
          </div>
          <div class="form-group">
            <label class="label">Confirm New Password</label>
            <input v-model="pwForm.confirmPassword" type="password" class="input" />
          </div>
          <div v-if="pwError" class="error-banner">{{ pwError }}</div>
          <button class="btn btn-primary" @click="changePassword" :disabled="savingPw">
            <Lock :size="13" />
            {{ savingPw ? 'Updating…' : 'Update Password' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Add user modal -->
    <Teleport to="body">
      <div v-if="showAddUser" class="modal-backdrop" @click.self="showAddUser = false">
        <div class="modal">
          <div class="modal-header">
            <span>Add User</span>
            <button class="btn btn-icon btn-ghost btn-sm" @click="showAddUser = false">
              <X :size="15" />
            </button>
          </div>
          <div class="modal-body">
            <div class="form-stack">
              <div class="grid-2">
                <div class="form-group">
                  <label class="label">First Name *</label>
                  <input v-model="userForm.firstName" class="input" />
                </div>
                <div class="form-group">
                  <label class="label">Full Name</label>
                  <input v-model="userForm.lastName" class="input" />
                </div>
                <div class="form-group">
                  <label class="label">Email *</label>
                  <input v-model="userForm.email" class="input" type="email" />
                </div>
                <div class="form-group">
                  <label class="label">Password *</label>
                  <input v-model="userForm.password" class="input" type="password" />
                </div>
                <div class="form-group">
                  <label class="label">Role</label>
                  <select v-model="userForm.role" class="input">
                    <option value="GUARD">GUARD</option>
                    <option value="ADMIN">ADMIN</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-ghost" @click="showAddUser = false">Cancel</button>
            <button class="btn btn-primary" @click="addUser" :disabled="savingUser">
              {{ savingUser ? 'Creating…' : 'Create User' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { UserPlus, Lock, X } from 'lucide-vue-next'
import { usersApi, authApi } from '@/services/endpoints'
import { useAuthStore } from '@/stores/auth'
import { format } from 'date-fns'
import { useToast } from 'vue-toastification'

const auth  = useAuthStore()
const toast = useToast()

const users       = ref([])
const showAddUser = ref(false)
const savingUser  = ref(false)
const savingPw    = ref(false)
const pwError     = ref('')

const userForm = ref({ firstName: '', lastName: '', email: '', password: '', role: '' })
const pwForm   = ref({ currentPassword: '', newPassword: '', confirmPassword: '' })

onMounted(async () => {
  const { data } = await usersApi.list()
  users.value = data
})

async function addUser() {
  savingUser.value = true
  try {
    await usersApi.addGuard(userForm.value)
    const { data } = await usersApi.list()
    users.value    = data
    showAddUser.value = false
    userForm.value = { firstName: '', lastName: '', email: '', password: '', role: 'ANALYST' }
    toast.success('User created')
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Failed to create user')
  } finally {
    savingUser.value = false
  }
}

async function changePassword() {
  pwError.value = ''
  if (pwForm.value.newPassword !== pwForm.value.confirmPassword) {
    pwError.value = 'New passwords do not match'
    return
  }
  savingPw.value = true
  try {
    await authApi.changePassword({
      currentPassword: pwForm.value.currentPassword,
      newPassword:     pwForm.value.newPassword
    })
    pwForm.value = { currentPassword: '', newPassword: '', confirmPassword: '' }
    toast.success('Password updated successfully')
  } catch (e) {
    pwError.value = e.response?.data?.detail || 'Failed to update password'
  } finally {
    savingPw.value = false
  }
}

function initials(name) {
  return name?.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2) || '?'
}
function formatDate(ts) {
  try { return format(new Date(ts), 'MMM d, yyyy') } catch { return '—' }
}
function roleBadge(role) {
  const m = { ADMIN: 'badge-red', SECURITY_PERSONNEL: 'badge-orange', GUARD: 'badge-blue' }
  return m[role] || 'badge-gray'
}
</script>

<style scoped>
.settings-grid { display: flex; flex-direction: column; gap: 16px; }

.section-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 16px;
}
.section-title {
  font-size: 12px; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.5px;
  color: var(--text-secondary);
}

.form-stack { display: flex; flex-direction: column; gap: 14px; }

.user-cell { display: flex; align-items: center; gap: 8px; }
.user-avatar-sm {
  width: 28px; height: 28px;
  border-radius: 50%;
  background: var(--accent-dim);
  color: var(--accent);
  font-size: 10px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}

.error-banner {
  padding: 8px 12px;
  background: var(--red-dim);
  border: 1px solid rgba(239,68,68,0.3);
  border-radius: var(--radius);
  color: var(--red);
  font-size: 12px;
}

/* Modal */
.modal-backdrop {
  position: fixed; inset: 0; background: rgba(0,0,0,0.6);
  display: flex; align-items: center; justify-content: center;
  z-index: 200; backdrop-filter: blur(4px);
}
.modal {
  background: var(--bg-elevated); border: 1px solid var(--border-mid);
  border-radius: var(--radius-lg); width: 100%; max-width: 580px;
  box-shadow: var(--shadow-md);
}
.modal-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px; border-bottom: 1px solid var(--border);
  font-size: 14px; font-weight: 600;
}
.modal-body   { padding: 20px; }
.modal-footer {
  display: flex; justify-content: flex-end; gap: 8px;
  padding: 16px 20px; border-top: 1px solid var(--border);
}

.text-center { text-align: center; }
.text-muted  { color: var(--text-muted); }
.text-xs     { font-size: 11px; }
.font-mono   { font-family: var(--font-mono); }
</style>
