/**
 * API Client - Axios wrapper for backend communication
 */
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: async (username: string, password: string) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);

    const response = await api.post('/auth/token', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  register: async (username: string, password: string) => {
    const response = await api.post('/auth/register', { username, password });
    return response.data;
  },

  getMe: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },
};

// CV API
export const cvAPI = {
  upload: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/cv/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  getProfile: async () => {
    const response = await api.get('/cv/profile');
    return response.data;
  },

  deleteProfile: async () => {
    await api.delete('/cv/profile');
  },
};

// Jobs API
export const jobsAPI = {
  search: async (params?: {
    query?: string;
    location?: string;
    min_salary?: number;
    limit?: number;
    offset?: number;
  }) => {
    const response = await api.get('/jobs', { params });
    return response.data;
  },

  getById: async (id: string) => {
    const response = await api.get(`/jobs/${id}`);
    return response.data;
  },
};

// Matches API
export const matchesAPI = {
  getMatches: async (limit: number = 10) => {
    const response = await api.get('/matches', { params: { limit } });
    return response.data;
  },

  calculate: async () => {
    const response = await api.post('/matches/calculate');
    return response.data;
  },
};

export default api;
