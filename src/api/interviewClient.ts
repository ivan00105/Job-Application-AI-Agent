import { apiClient } from './client';

export interface StartSessionRequest {
  role_type: 'IT' | 'Finance' | 'Both';
  domain: 'IT' | 'Finance' | 'General';
  job_id?: string;
  total_questions?: number;
}

export interface InterviewSession {
  id: string;
  user_id: string;
  role_type: string;
  domain: string;
  job_id?: string;
  status: 'active' | 'completed' | 'abandoned';
  total_questions: number;
  completed_questions: number;
  avg_score?: number;
  started_at: string;
  completed_at?: string;
}

export interface InterviewQuestion {
  id: string;
  question_text: string;
  role_type: string;
  domain: string;
  category: string;
  difficulty: string;
  ideal_answer?: string;
  metadata?: any;
  is_active: boolean;
  created_at?: string;
}

export interface QuestionWithContext {
  question: InterviewQuestion;
  question_number: number;
  total_questions: number;
  session_progress: number;
}

export interface EvaluationScores {
  overall_score: number;
  relevance_score: number;
  completeness_score: number;
  technical_accuracy_score: number;
  communication_score: number;
}

export interface InterviewResponse {
  id: string;
  session_id: string;
  question_id: string;
  user_answer: string;
  evaluation_scores?: EvaluationScores;
  feedback?: string;
  strengths: string[];
  improvements: string[];
  submitted_at: string;
}

export interface EvaluationResult {
  response: InterviewResponse;
  question: InterviewQuestion;
  is_session_complete: boolean;
  next_question?: InterviewQuestion;
}

export interface SessionHistory {
  sessions: InterviewSession[];
  total_sessions: number;
  avg_performance?: number;
}

export interface SessionDetail {
  session: InterviewSession;
  responses: InterviewResponse[];
  questions: InterviewQuestion[];
}

export interface PerformanceAnalytics {
  user_id: string;
  domain: string;
  total_sessions: number;
  total_questions_answered: number;
  avg_overall_score?: number;
  avg_relevance_score?: number;
  avg_completeness_score?: number;
  avg_technical_accuracy_score?: number;
  avg_communication_score?: number;
  weak_categories: string[];
  strong_categories: string[];
  last_practice_date?: string;
}

export const interviewAPI = {
  startSession: async (data: StartSessionRequest): Promise<InterviewSession> => {
    const response = await apiClient.post('/interview/sessions/start', data);
    return response.data;
  },

  getNextQuestion: async (sessionId: string): Promise<QuestionWithContext> => {
    const response = await apiClient.get(`/interview/sessions/${sessionId}/next-question`);
    return response.data;
  },

  submitAnswer: async (
    sessionId: string,
    questionId: string,
    userAnswer: string
  ): Promise<EvaluationResult> => {
    const response = await apiClient.post(`/interview/sessions/${sessionId}/submit-answer`, {
      session_id: sessionId,
      question_id: questionId,
      user_answer: userAnswer,
    });
    return response.data;
  },

  getSessionHistory: async (limit = 10): Promise<SessionHistory> => {
    const response = await apiClient.get('/interview/sessions/history', {
      params: { limit },
    });
    return response.data;
  },

  getSessionsByJob: async (jobId: string): Promise<SessionHistory> => {
    const response = await apiClient.get(`/interview/sessions/job/${jobId}`);
    return response.data;
  },

  getSessionDetail: async (sessionId: string): Promise<SessionDetail> => {
    const response = await apiClient.get(`/interview/sessions/${sessionId}`);
    return response.data;
  },

  getAnalytics: async (): Promise<PerformanceAnalytics[]> => {
    const response = await apiClient.get('/interview/analytics');
    return response.data;
  },

  abandonSession: async (sessionId: string): Promise<void> => {
    await apiClient.post(`/interview/sessions/${sessionId}/abandon`);
  },

  getQuestions: async (params?: {
    role_type?: string;
    domain?: string;
    difficulty?: string;
    limit?: number;
  }): Promise<InterviewQuestion[]> => {
    const response = await apiClient.get('/interview/questions', { params });
    return response.data;
  },
};
