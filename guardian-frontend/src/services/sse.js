// import { useAuthStore } from '@/stores/auth'

const BASE_URL = import.meta.env.VITE_API_URL || '/api'

export function createEventSource(path) {
  const auth = useAuthStore()
  const url = new URL(`${BASE_URL}${path}`, window.location.origin)
  if (auth.accessToken) {
    url.searchParams.set('token', auth.accessToken)
  }
  return new EventSource(url.toString())
}

export class ReconnectingEventSource {
  constructor(path, handlers = {}) {
    this.path = path
    this.handlers = handlers
    this.es = null
    this.retries = 0
    this.maxRetries = 10
    this.retryDelay = 3000
    this._destroyed = false
    this.connect()
  }

  connect() {
    if (this._destroyed) return
    this.es = createEventSource(this.path)

    this.es.addEventListener('incident', (e) => {
      this.retries = 0
      this.handlers.onIncident?.(JSON.parse(e.data))
    })

    this.es.addEventListener('alert', (e) => {
      this.retries = 0
      this.handlers.onAlert?.(JSON.parse(e.data))
    })

    this.es.addEventListener('heartbeat', () => {
      this.handlers.onHeartbeat?.()
    })

    this.es.onmessage = (e) => {
      this.handlers.onMessage?.(e)
    }

    this.es.onerror = () => {
      this.es.close()
      if (this._destroyed) return
      if (this.retries < this.maxRetries) {
        this.retries++
        const delay = Math.min(this.retryDelay * this.retries, 30000)
        setTimeout(() => this.connect(), delay)
        this.handlers.onReconnecting?.(this.retries, delay)
      } else {
        this.handlers.onFailed?.()
      }
    }

    this.es.onopen = () => {
      this.retries = 0
      this.handlers.onConnected?.()
    }
  }

  destroy() {
    this._destroyed = true
    this.es?.close()
  }
}
