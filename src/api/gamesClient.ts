import { apiClient } from './client';

export interface Game {
  id: string;
  title: string;
  description?: string;
  game_type: string;
  domain?: string;
  difficulty?: string;
  game_content: Record<string, any>;
  time_limit_minutes?: number;
  points: number;
  tags: string[];
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface GameTypeInfo {
  id?: string;
  type_code: string;
  name: string;
  description?: string;
  handler_class?: string;
  config_schema?: Record<string, any>;
  is_active: boolean;
  created_at?: string;
}

export interface GameSession {
  id: string;
  user_id: string;
  game_id: string;
  status: 'active' | 'completed' | 'abandoned';
  score?: number;
  time_taken_seconds?: number;
  started_at?: string;
  completed_at?: string;
  result_data?: Record<string, any>;
}

export interface GameAttempt {
  id: string;
  session_id: string;
  game_id: string;
  answer_data: Record<string, any>;
  evaluation_result?: Record<string, any>;
  is_correct?: boolean;
  points_earned?: number;
  submitted_at?: string;
}

export interface StartGameSessionRequest {
  game_id: string;
  force_new?: boolean;
}

export interface SubmitGameAnswerRequest {
  session_id: string;
  answer_data: Record<string, any>;
}

export interface GameResult {
  session: GameSession;
  attempts: GameAttempt[];
  final_score: number;
  badges_earned: string[];
  leaderboard_position?: number;
}

export interface LeaderboardEntry {
  rank: number;
  user_id: string;
  username?: string;
  score: number;
  time_taken_seconds?: number;
  completed_at: string;
}

export interface Leaderboard {
  game_id: string;
  game_title: string;
  entries: LeaderboardEntry[];
  total_players: number;
}

export interface SkillBadge {
  id: string;
  user_id: string;
  badge_type: string;
  game_id?: string;
  game_type?: string;
  earned_at?: string;
  verified: boolean;
  metadata?: Record<string, any>;
}

export interface UserGameStats {
  user_id: string;
  game_type: string;
  total_games_played: number;
  total_score: number;
  avg_score?: number;
  best_score?: number;
  games_completed: number;
  badges_earned: number;
  last_played_at?: string;
}

export interface DomainStats {
  domain: string;
  total_challenges: number;
  completed_challenges: number;
  total_score: number;
  avg_score: number;
  best_score: number;
}

export interface UserStatsResponse {
  stats_by_type: Record<string, UserGameStats>;
  stats_by_domain: Record<string, DomainStats>;
  total_games_played: number;
  total_score: number;
  total_badges: number;
  badges: SkillBadge[];
}

export interface UserSessionHistoryItem {
  id: string;
  user_id: string;
  game_id: string;
  status: 'active' | 'completed' | 'abandoned';
  score?: number;
  time_taken_seconds?: number;
  started_at?: string;
  completed_at?: string;
  result_data?: Record<string, any>;
  title: string;
  game_type: string;
  domain?: string;
  difficulty?: string;
  points: number;
}

export const gamesAPI = {
  getGameTypes: async (): Promise<GameTypeInfo[]> => {
    const response = await apiClient.get('/games/types');
    return response.data;
  },

  getGames: async (params?: {
    game_type?: string;
    domain?: string;
    difficulty?: string;
  }): Promise<Game[]> => {
    const response = await apiClient.get('/games/', { params });
    return response.data;
  },

  getGame: async (gameId: string): Promise<Game> => {
    const response = await apiClient.get(`/games/${gameId}`);
    return response.data;
  },

  checkActiveSessions: async (gameId: string): Promise<{ has_active_sessions: boolean; active_sessions: any[] }> => {
    const response = await apiClient.get(`/games/sessions/check/${gameId}`);
    return response.data;
  },

  startSession: async (data: StartGameSessionRequest): Promise<GameSession> => {
    const response = await apiClient.post('/games/sessions/start', data);
    return response.data;
  },

  submitAnswer: async (sessionId: string, data: SubmitGameAnswerRequest): Promise<GameAttempt> => {
    const response = await apiClient.post(`/games/sessions/${sessionId}/submit`, data);
    return response.data;
  },

  completeSession: async (sessionId: string): Promise<GameResult> => {
    const response = await apiClient.post(`/games/sessions/${sessionId}/complete`);
    return response.data;
  },

  getLeaderboard: async (gameId: string, limit: number = 100): Promise<Leaderboard> => {
    const response = await apiClient.get(`/games/leaderboard/${gameId}`, {
      params: { limit },
    });
    return response.data;
  },

  getUserBadges: async (): Promise<SkillBadge[]> => {
    const response = await apiClient.get('/games/badges');
    return response.data;
  },

  getUserStats: async (): Promise<UserStatsResponse> => {
    const response = await apiClient.get('/games/stats');
    return response.data;
  },

  getSession: async (sessionId: string): Promise<{ session: GameSession; game: Game }> => {
    const response = await apiClient.get(`/games/sessions/${sessionId}`);
    return response.data;
  },

  deleteSession: async (sessionId: string): Promise<void> => {
    await apiClient.delete(`/games/sessions/${sessionId}`);
  },

  getUserSessionsHistory: async (params?: {
    status?: string;
    game_type?: string;
    domain?: string;
    limit?: number;
  }): Promise<UserSessionHistoryItem[]> => {
    const response = await apiClient.get('/games/sessions/history', { params });
    return response.data;
  },
};

