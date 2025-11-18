/**
 * API Client - Axios wrapper for backend communication
 */
import axios from 'axios';

// Get API URL from environment, with security fix for HTTPS pages
let rawApiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// If page is HTTPS but API URL is HTTP, automatically upgrade to HTTPS for security
if (typeof window !== 'undefined' && window.location.protocol === 'https:' && rawApiUrl.startsWith('http://')) {
  console.warn('⚠️ Auto-upgrading HTTP API URL to HTTPS for security');
  rawApiUrl = rawApiUrl.replace('http://', 'https://');
}

export const API_BASE_URL = rawApiUrl;

// Log API URL for debugging (both dev and production)
console.log('🔗 API Base URL:', API_BASE_URL);
console.log('📡 Full API URL:', `${API_BASE_URL}/api`);
console.log('🌍 Environment:', import.meta.env.MODE);
console.log('📦 VITE_API_URL from env:', import.meta.env.VITE_API_URL);

// Log warning if not configured
if (!import.meta.env.VITE_API_URL) {
  console.warn('⚠️ VITE_API_URL not set in .env file, using default: http://localhost:8000');
  console.warn('💡 Create .env file in project root with: VITE_API_URL=https://api-aijobsfinder.groture.com');
} else if (import.meta.env.VITE_API_URL.startsWith('http://') && typeof window !== 'undefined' && window.location.protocol === 'https:') {
  console.error('❌ SECURITY ISSUE: Frontend is HTTPS but API URL is HTTP!');
  console.error('   Current API URL:', import.meta.env.VITE_API_URL);
  console.error('   Auto-fixed to:', API_BASE_URL);
  console.error('   Fix: Update .env file to use https:// and rebuild frontend');
}

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

  getProfileScoring: async (forceRefresh: boolean = false) => {
    const response = await api.get('/cv/profile/scoring', {
      params: { force_refresh: forceRefresh }
    });
    return response.data;
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
    const response = await api.get('/jobs/', { params }); // Use trailing slash to avoid 307 redirect
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

  refineCV: async (cvId: string) => {
    const response = await api.post(`/applications/prepare/cv/${cvId}/refine`);
    return response.data;
  },

  saveCVDraft: async (cvId: string, htmlContent: string, status: 'draft' | 'final' = 'draft', notes?: string) => {
    const response = await api.put(`/applications/prepare/cv/${cvId}/save`, {
      html_content: htmlContent,
      status,
      notes
    });
    return response.data;
  },

  validateCV: async (cvId: string, htmlContent: string) => {
    const response = await api.post(`/applications/prepare/cv/${cvId}/validate`, {
      html_content: htmlContent
    });
    return response.data;
  },

  exportCVToPDF: async (cvId: string, htmlContent?: string, htmlFilename?: string) => {
    console.log('API: exportCVToPDF called', { cvId, htmlContentLength: htmlContent?.length, htmlFilename });
    try {
      // Send HTML content if provided (most current), otherwise backend will use database or file
      const requestBody: any = {};
      if (htmlContent && htmlContent.trim().length > 0) {
        requestBody.html_content = htmlContent;
        console.log('API: Sending HTML content in request body', { length: htmlContent.length });
      } else if (htmlFilename) {
        requestBody.html_filename = htmlFilename;
      }
      const response = await api.post(
        `/applications/prepare/cv/${cvId}/export-pdf`,
        requestBody,
        {
          responseType: 'blob',
          timeout: 120000, // 2 minute timeout for PDF generation
        }
      );
      console.log('API: Response received', {
        status: response.status,
        contentType: response.headers['content-type'],
        dataType: response.data?.constructor?.name,
        dataSize: response.data?.size
      });
      // Check if response is actually a PDF
      if (response.data instanceof Blob && response.data.type === 'application/pdf') {
        console.log('API: Valid PDF blob received');
        return response.data;
      }
      // If not a PDF, might be an error - try to parse it
      throw new Error('Response is not a PDF file');
    } catch (error: any) {
      // If error response is a blob, try to parse it as JSON or text
      if (error.response?.data instanceof Blob) {
        try {
          const contentType = error.response.headers['content-type'] || '';
          const errorText = await error.response.data.text();
          
          let errorDetail = 'PDF generation failed';
          if (contentType.includes('application/json') || errorText.trim().startsWith('{')) {
            try {
              const errorJson = JSON.parse(errorText);
              errorDetail = errorJson.detail || errorJson.message || errorDetail;
            } catch {
              // If JSON parse fails, use text as is
              errorDetail = errorText || errorDetail;
            }
          } else {
            // Plain text error
            errorDetail = errorText || errorDetail;
          }
          
          // Create a new error with the parsed detail
          const newError: any = new Error(errorDetail);
          newError.response = {
            ...error.response,
            data: { detail: errorDetail }
          };
          throw newError;
        } catch (parseError) {
          // If parsing fails, throw original error with status info
          const statusError: any = new Error(
            `PDF generation failed with status ${error.response?.status || 'unknown'}. ` +
            `Please check backend logs for details.`
          );
          statusError.response = error.response;
          throw statusError;
        }
      }
      throw error;
    }
  },

  aiAssistCV: async (cvId: string, selectionHtml: string, intent: string, context?: any, timeout: number = 60000, signal?: AbortSignal) => {
    try {
      const response = await api.post(`/applications/prepare/cv/${cvId}/assist`, {
        selection_html: selectionHtml,
        intent,
        context
      }, {
        timeout,
        signal
      });
      return response.data;
    } catch (error: any) {
      if (error.name === 'AbortError' || error.code === 'ECONNABORTED') {
        throw new Error('Request timed out. Please try again.');
      }
      throw error;
    }
  },

  aiAssistCVStream: async (cvId: string, selectionHtml: string, intent: string, context?: any, timeout: number = 60000, signal?: AbortSignal) => {
    const token = localStorage.getItem('access_token');
    
    // Create a combined abort controller that handles both user cancellation and timeout
    const timeoutAbortController = new AbortController();
    const timeoutId = setTimeout(() => {
      timeoutAbortController.abort();
    }, timeout);

    // Combine signals if both are provided (compatible with older browsers)
    const combinedAbortController = new AbortController();
    let isTimeout = false;
    
    // Listen to timeout signal
    timeoutAbortController.signal.addEventListener('abort', () => {
      isTimeout = true;
      combinedAbortController.abort();
    });
    
    // Listen to user signal if provided
    if (signal) {
      signal.addEventListener('abort', () => {
        combinedAbortController.abort();
      });
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/applications/prepare/cv/${cvId}/assist/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'text/event-stream',
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          selection_html: selectionHtml,
          intent,
          context
        }),
        signal: combinedAbortController.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || 'Failed to stream AI assist response');
      }

      if (!response.body) {
        throw new Error('Streaming not supported in this browser');
      }

      return response;
    } catch (error: any) {
      clearTimeout(timeoutId);
      if (error.name === 'AbortError' || combinedAbortController.signal.aborted) {
        if (isTimeout) {
          throw new Error('Request timed out. Please try again.');
        }
        throw new Error('Request was cancelled. Please try again.');
      }
      throw error;
    }
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

// Autofill API
export const autofillAPI = {
  analyzeFields: async (url: string, fields: any[], companyName?: string) => {
    const response = await api.post('/autofill/analyze-fields', {
      url,
      fields,
      company_name: companyName,
    });
    return response.data;
  },

  saveAnswer: async (fieldLabel: string, answer: string, contextType: 'global' | 'company', companyName?: string, jobUrl?: string) => {
    const response = await api.post('/autofill/save-answer', {
      field_label: fieldLabel,
      answer,
      context_type: contextType,
      company_name: companyName,
      job_url: jobUrl,
    });
    return response.data;
  },

  getMemory: async (companyName?: string) => {
    const params = companyName ? `?company_name=${encodeURIComponent(companyName)}` : '';
    const response = await api.get(`/autofill/memory${params}`);
    return response.data;
  },

  deleteMemory: async (memoryId: string) => {
    await api.delete(`/autofill/memory/${memoryId}`);
  },
};

export const apiClient = api;
export default api;
