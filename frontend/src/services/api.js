import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 15000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    } else if (error.response && error.response.status === 403) {
      // Just log or show a toast if you have a global toast system.
      console.warn("Access denied: 403 Forbidden");
    }
    return Promise.reject(error);
  }
)

export const apiGet = (url, config = {}) => api.get(url, config)
export const apiPost = (url, data, config = {}) => api.post(url, data, config)
export const apiPut = (url, data, config = {}) => api.put(url, data, config)
export const apiDelete = (url, config = {}) => api.delete(url, config)

export const login = async ({ officer_id, password }) => {
  const response = await api.post('/api/auth/login', { officer_id, password })
  const { access_token, user } = response.data
  localStorage.setItem('token', access_token)
  localStorage.setItem('user', JSON.stringify(user))
  return response
}

export const logout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
}

export default api
