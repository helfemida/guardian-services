import api from './api'

export const camerasApi = {
    list: () => api.get('/api/camera/getAll'),
    stats: () => api.get('/api/camera/getActive'),
    get: (id) => api.get(`/api/camera/${id}`)
}
export const incidentsApi = {
    list: () => api.get('/api/v1/incidents'),
    resolve: (id, resolved) => api.patch(`/api/v1/incidents/${id}/resolve`, resolved, )
}

export const authApi = {
    login: (email, password) =>
        api.post('/api/v1/auth/login', {
            email: email,
            password: password
        }),

    logout: () => {
        localStorage.removeItem('accessToken')
        localStorage.removeItem('refreshToken')
        localStorage.removeItem('user')
        return Promise.resolve()
    }
}

export const usersApi = {
    list: () =>
        api.get('/api/v1/users', null),

    addGuard: (guardData) =>
        api.post('/api/v1/users/add-guard', guardData),
}



