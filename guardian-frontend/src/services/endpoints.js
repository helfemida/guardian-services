import api from './api'

export const camerasApi = {list: () => api.get('/api/camera/getAll'),
    stats: () => api.get('/api/camera/getActive')}
export const incidentsApi = {
    list: () => api.get('/api/v1/incidents'),
    resolve: (id, resolved) => api.post(`/api/v1/incidents/${id}/resolve`, null, {params: {resolved}})
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
    list:
        api.get('/api/v1/users', null),

    addGuard: (guardData) =>
        api.post('/api/v1/users/add-guard', guardData),
}



