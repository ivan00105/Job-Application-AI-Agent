-- Migration: Create interview preparation tables in PostgreSQL
-- Created: 2025-01-XX
-- Description: Adds interview tables to PostgreSQL (alternative to Supabase)

-- Interview sessions table
CREATE TABLE IF NOT EXISTS interview_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_type VARCHAR(20) NOT NULL, -- 'IT', 'Finance', 'Both'
    domain VARCHAR(20) NOT NULL, -- 'IT', 'Finance', 'General'
    job_id UUID REFERENCES jobs(id) ON DELETE SET NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active', -- 'active', 'completed', 'abandoned'
    total_questions INTEGER NOT NULL DEFAULT 5,
    completed_questions INTEGER NOT NULL DEFAULT 0,
    avg_score FLOAT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Interview questions table
CREATE TABLE IF NOT EXISTS interview_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_text TEXT NOT NULL,
    question_type VARCHAR(50), -- 'technical', 'behavioral', 'case_study', etc.
    role_type VARCHAR(20) NOT NULL, -- 'IT', 'Finance', 'Both'
    domain VARCHAR(20) NOT NULL, -- 'IT', 'Finance', 'General'
    difficulty VARCHAR(20), -- 'beginner', 'intermediate', 'advanced'
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Interview responses table
CREATE TABLE IF NOT EXISTS interview_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES interview_sessions(id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES interview_questions(id) ON DELETE CASCADE,
    user_answer TEXT NOT NULL,
    evaluation_scores JSONB DEFAULT '{}'::jsonb,
    feedback TEXT,
    strengths TEXT[],
    improvements TEXT[],
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Interview performance analytics table
CREATE TABLE IF NOT EXISTS interview_performance_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    domain VARCHAR(20) NOT NULL,
    total_sessions INTEGER DEFAULT 0,
    total_questions_answered INTEGER DEFAULT 0,
    avg_overall_score FLOAT,
    last_practice_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, domain)
);

-- Indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_interview_sessions_user_id ON interview_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_interview_sessions_status ON interview_sessions(status);
CREATE INDEX IF NOT EXISTS idx_interview_sessions_job_id ON interview_sessions(job_id);
CREATE INDEX IF NOT EXISTS idx_interview_questions_role_domain ON interview_questions(role_type, domain);
CREATE INDEX IF NOT EXISTS idx_interview_questions_active ON interview_questions(is_active);
CREATE INDEX IF NOT EXISTS idx_interview_responses_session_id ON interview_responses(session_id);
CREATE INDEX IF NOT EXISTS idx_interview_responses_question_id ON interview_responses(question_id);
CREATE INDEX IF NOT EXISTS idx_interview_analytics_user_domain ON interview_performance_analytics(user_id, domain);

-- Comments
COMMENT ON TABLE interview_sessions IS 'Stores interview practice sessions';
COMMENT ON TABLE interview_questions IS 'Stores interview questions for practice';
COMMENT ON TABLE interview_responses IS 'Stores user answers and evaluations';
COMMENT ON TABLE interview_performance_analytics IS 'Stores aggregated performance analytics';

