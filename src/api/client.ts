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

  saveProfile: async (parsedData: any) => {
    const response = await api.post('/cv/profile/save', { parsed_data: parsedData });
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
    hide_saved?: boolean;
    limit?: number;
    offset?: number;
  }) => {
    const response = await api.get('/jobs', { params });
    return response.data;
  },

  searchVector: async (params: {
    query: string;
    location?: string;
    hide_saved?: boolean;
    limit?: number;
    offset?: number;
    use_llm_enhancement?: boolean;
    score_threshold?: number;
  }) => {
    const { query, location, hide_saved, limit, offset, use_llm_enhancement, score_threshold } = params;
    
    // Body contains the JobDataSearch model fields
    const body: any = {
      query,
      limit: limit || 50,
    };
    
    if (use_llm_enhancement !== undefined) {
      body.use_llm_enhancement = use_llm_enhancement;
    }
    
    if (score_threshold !== undefined) {
      body.score_threshold = score_threshold;
    }
    
    // Query parameters for additional filters
    const queryParams: any = {
      limit: limit || 50,
      offset: offset || 0,
      hide_saved: hide_saved || false,
    };
    
    if (location) {
      queryParams.location = location;
    }
    
    const response = await api.post('/jobs/search-vector', body, {
      params: queryParams
    });
    return response.data;
  },

  getById: async (id: string) => {
    const response = await api.get(`/jobs/${id}`);
    return response.data;
  },

  getRecommended: async (params?: {
    limit?: number;
    offset?: number;
    hide_saved?: boolean;
  }) => {
    const response = await api.get('/jobs/recommended', { params });
    return response.data;
  },

  getSimilar: async (jobId: string, params?: {
    limit?: number;
    hide_saved?: boolean;
  }) => {
    const response = await api.get(`/jobs/${jobId}/similar`, { params });
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

// Applications API
export const applicationsAPI = {
  markApplied: async (jobId: string, status: string = 'applied', notes?: string) => {
    const response = await api.post('/applications/mark-applied', {
      job_id: jobId,
      status,
      notes
    });
    return response.data;
  },

  updateStatus: async (jobId: string, status: string, notes?: string) => {
    const response = await api.put(`/applications/${jobId}/status`, {
      status,
      notes
    });
    return response.data;
  },

  getApplications: async () => {
    const response = await api.get('/applications/');
    return response.data;
  },

  checkStatus: async (jobId: string) => {
    const response = await api.get(`/applications/status/${jobId}`);
    return response.data;
  },

  remove: async (jobId: string) => {
    await api.delete(`/applications/${jobId}`);
  },

  // Preparation endpoints
  prepareInterview: async (jobId: string) => {
    const response = await api.post(`/applications/${jobId}/prepare/interview`);
    return response.data;
  },

  prepareCV: async (jobId: string) => {
    const response = await api.post(`/applications/${jobId}/prepare/cv`);
    return response.data;
  },

  prepareCoverLetter: async (jobId: string) => {
    const response = await api.post(`/applications/${jobId}/prepare/cover-letter`);
    return response.data;
  },

  getPreparationStatus: async (jobId: string) => {
    const response = await api.get(`/applications/${jobId}/prepare/status`);
    return response.data;
  },
};

export const apiClient = api;
export default api;
