import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/services/endpoints'

export const useAuthStore = defineStore('auth', () => {
    const accessToken = ref(null)
    const refreshToken = ref(null)
    const user = ref(null)

    const isAuthenticated = computed(() => !!accessToken.value)
    const userRole = computed(() => user.value?.role)
    const isAdmin = computed(() => userRole.value === 'ADMIN')
    const isSecurity = computed(() =>
        ['ADMIN', 'SECURITY_PERSONNEL'].includes(userRole.value)
    )

    // FIXED: send email + password directly
    async function login(email, password) {
        const { data } = await authApi.login(email, password)

        accessToken.value = data.accessToken
        refreshToken.value = data.refreshToken

        user.value = {
            email: data.email,
            role: data.role
        }

        return data
    }

    async function refresh() {
        if (!refreshToken.value) throw new Error('No refresh token')

        const { data } = await authApi.refresh(refreshToken.value)

        accessToken.value = data.accessToken
        refreshToken.value = data.refreshToken

        user.value = {
            email: data.email,
            role: data.role
        }
    }

    async function logout() {
        try {
            await authApi.logout()
        } catch {}

        accessToken.value = null
        refreshToken.value = null
        user.value = null
    }

    return {
        accessToken,
        refreshToken,
        user,
        isAuthenticated,
        userRole,
        isAdmin,
        isSecurity,
        login,
        refresh,
        logout
    }
}, {
    persist: {
        paths: ['accessToken', 'refreshToken', 'user']
    }
})