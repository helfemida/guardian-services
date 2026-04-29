<template>
  <div class="login-page">
    <div class="login-bg">
      <div class="scan-line"></div>
      <div class="grid-overlay"></div>
    </div>

    <div class="login-card">
      <div class="login-brand">
        <ShieldAlert :size="32" class="brand-icon" />
        <div class="brand-name">GUARDIAN</div>
        <div class="brand-tagline">Intelligent Surveillance Platform</div>
      </div>

      <form class="login-form" @submit.prevent="handleLogin">
        <div class="form-group">
          <label class="label">Username</label>
          <div class="input-wrapper">
            <User :size="15" class="input-icon" />
            <input
              v-model="form.username"
              class="input with-icon"
              placeholder="Enter username"
              autocomplete="username"
              required
            />
          </div>
        </div>

        <div class="form-group">
          <label class="label">Password</label>
          <div class="input-wrapper">
            <Lock :size="15" class="input-icon" />
            <input
              v-model="form.password"
              :type="showPassword ? 'text' : 'password'"
              class="input with-icon with-icon-right"
              placeholder="Enter password"
              autocomplete="current-password"
              required
            />
            <button type="button" class="input-icon-right" @click="showPassword = !showPassword">
              <Eye v-if="!showPassword" :size="15" />
              <EyeOff v-else :size="15" />
            </button>
          </div>
        </div>

        <div v-if="error" class="error-banner">
          <AlertCircle :size="14" />
          {{ error }}
        </div>

        <button type="submit" class="btn btn-primary btn-lg login-btn" :disabled="loading">
          <span v-if="loading" class="spinner" style="width:16px;height:16px;border-width:2px"></span>
          <span v-else>Sign In</span>
        </button>
      </form>

      <div class="login-footer">
        Guardian Surveillance System &mdash; v1.0.0
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ShieldAlert, User, Lock, Eye, EyeOff, AlertCircle } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth   = useAuthStore()

const form         = ref({ username: '', password: '' })
const loading      = ref(false)
const error        = ref('')
const showPassword = ref(false)

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(form.value.username, form.value.password)
    router.push('/dashboard')
  } catch (e) {
    error.value = e.response?.data?.detail || 'Invalid username or password'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  background: var(--bg-base);
}

.login-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.grid-overlay {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(245,158,11,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(245,158,11,0.03) 1px, transparent 1px);
  background-size: 40px 40px;
}

.scan-line {
  position: absolute;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(245,158,11,0.4), transparent);
  animation: scan 4s linear infinite;
}
@keyframes scan {
  0%   { top: -2px; }
  100% { top: 100%; }
}

.login-card {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 380px;
  background: var(--bg-surface);
  border: 1px solid var(--border-mid);
  border-radius: var(--radius-lg);
  padding: 36px 32px;
  box-shadow: var(--shadow-md), 0 0 60px rgba(245,158,11,0.05);
}

.login-brand {
  text-align: center;
  margin-bottom: 32px;
}
.brand-icon { color: var(--accent); margin-bottom: 10px; }
.brand-name {
  font-family: var(--font-mono);
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 4px;
  color: var(--text-primary);
}
.brand-tagline {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
  letter-spacing: 0.3px;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}
.input-icon {
  position: absolute;
  left: 10px;
  color: var(--text-muted);
  pointer-events: none;
}
.input-icon-right {
  position: absolute;
  right: 10px;
  color: var(--text-muted);
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  display: flex;
}
.input-icon-right:hover { color: var(--text-secondary); }
.input.with-icon { padding-left: 32px; }
.input.with-icon-right { padding-right: 32px; }

.error-banner {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 12px;
  background: var(--red-dim);
  border: 1px solid rgba(239,68,68,0.3);
  border-radius: var(--radius);
  color: var(--red);
  font-size: 13px;
}

.login-btn { width: 100%; justify-content: center; margin-top: 4px; }

.login-footer {
  margin-top: 24px;
  text-align: center;
  font-size: 11px;
  color: var(--text-muted);
  letter-spacing: 0.3px;
}
</style>
