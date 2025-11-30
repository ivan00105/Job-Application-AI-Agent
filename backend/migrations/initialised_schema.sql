-- ============================================
-- Job Application Agent - Complete Database Schema
-- ============================================
-- This file combines all database migrations into a single schema
-- Run this file to set up the complete database structure
-- ============================================

-- ============================================
-- PART 1: Initial Schema (Core Tables)
-- ============================================

-- Users table for authentication
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- CV profiles (text + JSON only, vectors in Qdrant)
CREATE TABLE IF NOT EXISTS cv_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    raw_text TEXT,
    parsed_data JSONB DEFAULT '{}'::jsonb,
    qdrant_synced BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for user lookup
CREATE INDEX IF NOT EXISTS cv_profiles_user_id_idx ON cv_profiles(user_id);

-- Jobs table with job metadata (vectors in Qdrant)
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    company TEXT,
    company_url TEXT,
    description TEXT NOT NULL,
    requirements TEXT,
    location TEXT,
    salary TEXT,
    url TEXT NOT NULL UNIQUE, -- The URL to the original job post
    source TEXT, -- e.g., 'LinkedIn', 'JobsDB'
    posted_date TIMESTAMPTZ,
    retrieved_date TIMESTAMPTZ DEFAULT NOW(),
    application_type TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    qdrant_synced BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS jobs_company_idx ON jobs(company);
CREATE INDEX IF NOT EXISTS jobs_location_idx ON jobs(location);
CREATE INDEX IF NOT EXISTS jobs_posted_date_idx ON jobs(posted_date DESC);
CREATE INDEX IF NOT EXISTS jobs_is_active_idx ON jobs(is_active);

-- Agent memory for form field answers (vectors in Qdrant)
CREATE TABLE IF NOT EXISTS agent_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    context_key TEXT NOT NULL DEFAULT 'global',
    question_text TEXT NOT NULL,
    answer_text TEXT,
    company_name TEXT,
    job_url TEXT,
    qdrant_synced BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, context_key, question_text, company_name)
);

CREATE INDEX IF NOT EXISTS agent_memory_user_idx ON agent_memory(user_id);
CREATE INDEX IF NOT EXISTS agent_memory_context_idx ON agent_memory(context_key);
CREATE INDEX IF NOT EXISTS agent_memory_company_idx ON agent_memory(user_id, company_name);

-- Job matches with scoring and explanations
CREATE TABLE IF NOT EXISTS job_matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    overall_score FLOAT NOT NULL,
    skill_score FLOAT,
    experience_score FLOAT,
    location_score FLOAT,
    keyword_score FLOAT,
    explanation JSONB DEFAULT '{}'::jsonb,
    calculated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, job_id)
);

CREATE INDEX IF NOT EXISTS job_matches_user_score_idx ON job_matches(user_id, overall_score DESC);
CREATE INDEX IF NOT EXISTS job_matches_job_idx ON job_matches(job_id);

-- Applications tracking
CREATE TABLE IF NOT EXISTS applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'saved',
    generated_resume_text TEXT,
    generated_cover_letter TEXT,
    notes TEXT,
    submitted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, job_id)
);

CREATE INDEX IF NOT EXISTS applications_user_idx ON applications(user_id);
CREATE INDEX IF NOT EXISTS applications_job_idx ON applications(job_id);
CREATE INDEX IF NOT EXISTS applications_status_idx ON applications(status);
CREATE INDEX IF NOT EXISTS applications_created_idx ON applications(created_at DESC);

-- ============================================
-- PART 2: Profile Scoring Cache Tables
-- ============================================
-- Description: Caches profile scoring analysis and recommended jobs to avoid repeated LLM calls

-- Profile scoring cache table
CREATE TABLE IF NOT EXISTS profile_scoring_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    cv_profile_id UUID NOT NULL REFERENCES cv_profiles(id) ON DELETE CASCADE,
    scores JSONB NOT NULL DEFAULT '{}'::jsonb,
    strengths TEXT[] DEFAULT ARRAY[]::TEXT[],
    weaknesses TEXT[] DEFAULT ARRAY[]::TEXT[],
    recommendations JSONB DEFAULT '[]'::JSONB,
    competitor_insights JSONB DEFAULT '{}'::jsonb,
    basic_metrics JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id)
);

CREATE INDEX IF NOT EXISTS profile_scoring_cache_user_idx ON profile_scoring_cache(user_id);
CREATE INDEX IF NOT EXISTS profile_scoring_cache_cv_profile_idx ON profile_scoring_cache(cv_profile_id);

-- Recommended jobs cache table
CREATE TABLE IF NOT EXISTS recommended_jobs_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_ids UUID[] NOT NULL DEFAULT ARRAY[]::UUID[],
    cached_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    UNIQUE(user_id)
);

CREATE INDEX IF NOT EXISTS recommended_jobs_cache_user_idx ON recommended_jobs_cache(user_id);
CREATE INDEX IF NOT EXISTS recommended_jobs_cache_expires_idx ON recommended_jobs_cache(expires_at);

-- ============================================
-- PART 3: Application Preparation Tables
-- ============================================
-- Description: Tables for tailored CVs and cover letters

-- Table for tailored CVs
CREATE TABLE IF NOT EXISTS tailored_cvs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    original_cv_profile_id UUID REFERENCES cv_profiles(id) ON DELETE SET NULL,
    tailored_content TEXT NOT NULL, -- JSON string with tailored CV data
    emphasis_notes TEXT, -- Explanation of what was emphasized
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, job_id) -- One tailored CV per job per user
);

-- Table for cover letters
CREATE TABLE IF NOT EXISTS cover_letters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    content TEXT NOT NULL, -- The cover letter text
    template_used VARCHAR(50) DEFAULT 'standard',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, job_id) -- One cover letter per job per user
);

-- Indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_tailored_cvs_user_id ON tailored_cvs(user_id);
CREATE INDEX IF NOT EXISTS idx_tailored_cvs_job_id ON tailored_cvs(job_id);
CREATE INDEX IF NOT EXISTS idx_cover_letters_user_id ON cover_letters(user_id);
CREATE INDEX IF NOT EXISTS idx_cover_letters_job_id ON cover_letters(job_id);

-- Comments
COMMENT ON TABLE tailored_cvs IS 'Stores tailored CVs customized for specific jobs';
COMMENT ON TABLE cover_letters IS 'Stores generated cover letters for specific jobs';

-- ============================================
-- PART 4: Interview Preparation Tables
-- ============================================
-- Description: Interview practice and evaluation tables

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

-- ============================================
-- PART 5: Application Status Constraints
-- ============================================
-- Description: Adds CHECK constraint for valid application statuses

-- First, update any existing 'draft' statuses to 'saved' (more user-friendly)
UPDATE applications SET status = 'saved' WHERE status = 'draft' OR status IS NULL;

-- Add CHECK constraint for valid statuses
DO $$
BEGIN
    -- Drop existing constraint if it exists
    IF EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'applications_status_check'
    ) THEN
        ALTER TABLE applications DROP CONSTRAINT applications_status_check;
    END IF;
    
    -- Add new constraint with all valid statuses
    ALTER TABLE applications ADD CONSTRAINT applications_status_check 
    CHECK (status IN (
        'saved',
        'applied', 
        'interviewing',
        'offer',
        'accepted',
        'rejected',
        'declined',
        'withdrawn',
        'not_interested'
    ));
END $$;

-- Update default status to 'saved' instead of 'draft'
ALTER TABLE applications ALTER COLUMN status SET DEFAULT 'saved';

-- ============================================
-- PART 6: Coding Questions Tables
-- ============================================
-- Description: Pool of coding questions for games

-- Coding questions pool
CREATE TABLE IF NOT EXISTS coding_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    language VARCHAR(20) NOT NULL, -- 'python', 'javascript', etc.
    difficulty VARCHAR(20) NOT NULL, -- 'beginner', 'intermediate', 'advanced'
    concept VARCHAR(100) NOT NULL, -- e.g., 'variables and data types', 'closures'
    
    -- Question content
    description TEXT NOT NULL,
    function_signature TEXT,
    starter_code TEXT NOT NULL,
    test_cases JSONB NOT NULL DEFAULT '[]'::jsonb,
    hints JSONB DEFAULT '[]'::jsonb, -- Array of hint strings
    
    -- Metadata
    points INTEGER DEFAULT 20, -- Points for this question
    estimated_time_minutes INTEGER DEFAULT 5,
    tags TEXT[] DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    usage_count INTEGER DEFAULT 0, -- How many times this question has been used
    success_rate FLOAT, -- Percentage of users who passed (for analytics)
    
    -- Source tracking
    source VARCHAR(50) DEFAULT 'manual', -- 'manual', 'llm', 'imported'
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for fast querying
CREATE INDEX IF NOT EXISTS idx_questions_language_difficulty ON coding_questions(language, difficulty);
CREATE INDEX IF NOT EXISTS idx_questions_concept ON coding_questions(concept);
CREATE INDEX IF NOT EXISTS idx_questions_active ON coding_questions(is_active);
CREATE INDEX IF NOT EXISTS idx_questions_tags ON coding_questions USING GIN(tags);

-- Comments
COMMENT ON TABLE coding_questions IS 'Pool of coding questions that can be randomly selected for games';
COMMENT ON COLUMN coding_questions.test_cases IS 'Array of test case objects with input and expected_output';
COMMENT ON COLUMN coding_questions.hints IS 'Array of hint strings to help users';
COMMENT ON COLUMN coding_questions.usage_count IS 'Number of times this question has been used in games';
COMMENT ON COLUMN coding_questions.success_rate IS 'Percentage of users who successfully completed this question';

-- ============================================
-- PART 7: Multiple Choice Questions Tables
-- ============================================
-- Description: Pool of multiple choice questions for games

CREATE TABLE IF NOT EXISTS multiple_choice_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic VARCHAR(100) NOT NULL, -- e.g., "Python", "JavaScript", "Logic", "English", "Math"
    category VARCHAR(50) NOT NULL, -- e.g., "technical", "language", "logic", "general"
    difficulty VARCHAR(20) NOT NULL CHECK (difficulty IN ('beginner', 'intermediate', 'advanced')),
    question_text TEXT NOT NULL,
    options JSONB NOT NULL, -- Array of option objects: [{"text": "Option A", "id": "a"}, ...]
    correct_answer VARCHAR(10) NOT NULL, -- ID of correct option (e.g., "a", "b", "c", "d")
    explanation TEXT, -- Explanation of why the answer is correct
    points INTEGER DEFAULT 10,
    estimated_time_minutes INTEGER DEFAULT 2,
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    domain VARCHAR(20), -- 'IT', 'Finance', 'General', etc.
    source VARCHAR(50) DEFAULT 'manual', -- 'manual', 'llm', 'imported'
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    usage_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2) DEFAULT 0.0, -- Percentage of users who got it correct
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_mc_questions_topic_difficulty ON multiple_choice_questions(topic, difficulty);
CREATE INDEX IF NOT EXISTS idx_mc_questions_category ON multiple_choice_questions(category);
CREATE INDEX IF NOT EXISTS idx_mc_questions_domain ON multiple_choice_questions(domain);
CREATE INDEX IF NOT EXISTS idx_mc_questions_active ON multiple_choice_questions(is_active);
CREATE INDEX IF NOT EXISTS idx_mc_questions_tags ON multiple_choice_questions USING GIN(tags);

-- Comments
COMMENT ON TABLE multiple_choice_questions IS 'Pool of multiple choice questions that can be randomly selected for games';
COMMENT ON COLUMN multiple_choice_questions.options IS 'Array of option objects with text and id';
COMMENT ON COLUMN multiple_choice_questions.correct_answer IS 'ID of the correct option (e.g., "a", "b", "c", "d")';
COMMENT ON COLUMN multiple_choice_questions.explanation IS 'Explanation of why the correct answer is right';
COMMENT ON COLUMN multiple_choice_questions.usage_count IS 'Number of times this question has been used in games';
COMMENT ON COLUMN multiple_choice_questions.success_rate IS 'Percentage of users who got this question correct';

-- ============================================
-- PART 8: Game Library Tables
-- ============================================
-- Description: Extensible game library for skill demonstration

-- Game types registry (extensible)
CREATE TABLE IF NOT EXISTS game_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type_code VARCHAR(50) UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    handler_class TEXT,
    config_schema JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Game library (all games)
CREATE TABLE IF NOT EXISTS games (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT,
    game_type VARCHAR(50) NOT NULL REFERENCES game_types(type_code),
    domain VARCHAR(20), -- 'IT', 'Finance', 'General'
    difficulty VARCHAR(20), -- 'beginner', 'intermediate', 'advanced'
    
    -- Game-specific content stored as JSONB (flexible for all game types)
    game_content JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- Common metadata
    time_limit_minutes INTEGER,
    points INTEGER DEFAULT 100,
    tags TEXT[],
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Game sessions (similar to interview_sessions)
CREATE TABLE IF NOT EXISTS game_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    game_id UUID NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'active', -- 'active', 'completed', 'abandoned'
    score INTEGER,
    time_taken_seconds INTEGER,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    result_data JSONB DEFAULT '{}'::jsonb -- Game-specific results
);

-- Game attempts/responses (unified for all game types)
CREATE TABLE IF NOT EXISTS game_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES game_sessions(id) ON DELETE CASCADE,
    game_id UUID NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    
    -- Flexible answer storage (works for all game types)
    answer_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- Evaluation result from game handler
    evaluation_result JSONB,
    is_correct BOOLEAN,
    points_earned INTEGER,
    submitted_at TIMESTAMPTZ DEFAULT NOW()
);

-- Leaderboards
CREATE TABLE IF NOT EXISTS game_leaderboards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    game_id UUID NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES game_sessions(id) ON DELETE CASCADE,
    rank INTEGER,
    score INTEGER NOT NULL,
    time_taken_seconds INTEGER,
    completed_at TIMESTAMPTZ NOT NULL,
    UNIQUE(game_id, user_id) -- One entry per user per game (best score)
);

-- Skill badges (earned from games)
CREATE TABLE IF NOT EXISTS skill_badges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    badge_type VARCHAR(50) NOT NULL,
    game_id UUID REFERENCES games(id),
    game_type VARCHAR(50),
    earned_at TIMESTAMPTZ DEFAULT NOW(),
    verified BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- User game statistics
CREATE TABLE IF NOT EXISTS user_game_stats (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    game_type VARCHAR(50) NOT NULL,
    total_games_played INTEGER DEFAULT 0,
    total_score INTEGER DEFAULT 0,
    avg_score FLOAT,
    best_score INTEGER,
    games_completed INTEGER DEFAULT 0,
    badges_earned INTEGER DEFAULT 0,
    last_played_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, game_type)
);

-- Indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_games_type ON games(game_type);
CREATE INDEX IF NOT EXISTS idx_games_domain ON games(domain);
CREATE INDEX IF NOT EXISTS idx_games_active ON games(is_active);
CREATE INDEX IF NOT EXISTS idx_game_sessions_user ON game_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_game_sessions_game ON game_sessions(game_id);
CREATE INDEX IF NOT EXISTS idx_game_sessions_status ON game_sessions(status);
CREATE INDEX IF NOT EXISTS idx_game_attempts_session ON game_attempts(session_id);
CREATE INDEX IF NOT EXISTS idx_game_attempts_game ON game_attempts(game_id);
CREATE INDEX IF NOT EXISTS idx_leaderboards_game ON game_leaderboards(game_id);
CREATE INDEX IF NOT EXISTS idx_leaderboards_user ON game_leaderboards(user_id);
CREATE INDEX IF NOT EXISTS idx_leaderboards_score ON game_leaderboards(game_id, score DESC);
CREATE INDEX IF NOT EXISTS idx_badges_user ON skill_badges(user_id);
CREATE INDEX IF NOT EXISTS idx_badges_type ON skill_badges(badge_type);
CREATE INDEX IF NOT EXISTS idx_user_game_stats_user ON user_game_stats(user_id);

-- Comments
COMMENT ON TABLE game_types IS 'Registry of available game types (coding, multiple_choice, personality, etc.)';
COMMENT ON TABLE games IS 'Game library - all available games';
COMMENT ON TABLE game_sessions IS 'User game sessions';
COMMENT ON TABLE game_attempts IS 'Individual game attempts/responses';
COMMENT ON TABLE game_leaderboards IS 'Leaderboards for each game';
COMMENT ON TABLE skill_badges IS 'Badges earned by users from games';
COMMENT ON TABLE user_game_stats IS 'Aggregated statistics per user per game type';

-- Insert default game types (can be extended later)
INSERT INTO game_types (type_code, name, description, handler_class, is_active) VALUES
    ('coding', 'Coding Challenges', 'Programming and algorithm challenges', 'CodingGameHandler', TRUE),
    ('multiple_choice', 'Multiple Choice', 'Quiz-style multiple choice questions', 'MultipleChoiceGameHandler', TRUE),
    ('personality', 'Personality Tests', 'Personality and work style assessments', 'PersonalityGameHandler', TRUE),
    ('puzzle', 'Puzzles', 'Logic puzzles and brain teasers', 'PuzzleGameHandler', TRUE),
    ('system_design', 'System Design', 'Architecture and system design challenges', 'SystemDesignGameHandler', TRUE),
    ('case_study', 'Case Studies', 'Business problem solving scenarios', 'CaseStudyGameHandler', TRUE)
ON CONFLICT (type_code) DO NOTHING;

-- ============================================
-- Schema Creation Complete
-- ============================================

