import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' }
})

// Request interceptor – attach JWT
api.interceptors.request.use(config => {
  const auth = useAuthStore()
  if (auth.accessToken) {
    config.headers.Authorization = `Bearer ${auth.accessToken}`
  }
  return config
}, Promise.reject)

// Response interceptor – handle 401, token refresh
let refreshing = false
let queue = []


api.interceptors.response.use(
  res => res,
  async err => {
    const original = err.config
    if (err.response?.status === 401 && !original._retry) {
      original._retry = true
      if (refreshing) {
        return new Promise((resolve, reject) => {
          queue.push({ resolve, reject })
        }).then(token => {
          original.headers.Authorization = `Bearer ${token}`
          return api(original)
        })
      }
      refreshing = true
      try {
        const auth = useAuthStore()
        await auth.refreshToken()
        queue.forEach(p => p.resolve(auth.accessToken))
        queue = []
        original.headers.Authorization = `Bearer ${auth.accessToken}`
        return api(original)
      } catch (e) {
        queue.forEach(p => p.reject(e))
        queue = []
        const auth = useAuthStore()
        auth.logout()
        router.push('/login')
        return Promise.reject(e)
      } finally {
        refreshing = false
      }
    }
    return Promise.reject(err)
  }
)

export default api
