/*
  # Interview Preparation System Schema

  ## Overview
  This migration creates the complete database schema for the AI-powered interview preparation system
  tailored for IT and Finance roles.

  ## Tables Created

  ### 1. interview_knowledge_base
  - Stores curated domain knowledge for RAG system
  - Fields: id, domain (IT/Finance), category, title, content, chunk_text, embedding (vector), metadata (JSONB)
  - Vector embeddings for semantic retrieval (768 dimensions)
  - Used for generating ideal answers and evaluation context

  ### 2. interview_questions
  - Question bank with metadata
  - Fields: id, question_text, role_type, domain, category, difficulty, ideal_answer, metadata (JSONB)
  - Supports both domain-specific and general questions
  - Categories: technical, behavioral, case_study, situational

  ### 3. interview_sessions
  - Tracks user interview practice sessions
  - Fields: id, user_id, role_type, domain, job_id (optional), status, started_at, completed_at
  - Links to specific jobs for job-specific preparation
  - Status: active, completed, abandoned

  ### 4. interview_responses
  - Stores user answers with AI evaluation
  - Fields: id, session_id, question_id, user_answer, evaluation_scores (JSONB), feedback, submitted_at
  - Scores include: overall, relevance, completeness, technical_accuracy, communication
  - Detailed feedback for improvement

  ### 5. interview_performance_analytics
  - Aggregated performance metrics
  - Fields: user_id, domain, avg_scores by dimension, total_sessions, improvement_rate, weak_categories
  - Automatically updated from responses for dashboard

  ## Vector Search
  - IVFFlat index on knowledge_base embeddings for fast RAG retrieval
  - Helper functions for semantic search and question selection

  ## Security
  - No RLS for POC (consistent with existing schema)
  - Foreign key constraints for data integrity
*/

-- Interview knowledge base for RAG system
CREATE TABLE IF NOT EXISTS interview_knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain TEXT NOT NULL CHECK (domain IN ('IT', 'Finance', 'General')),
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(768),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS interview_kb_embedding_idx 
ON interview_knowledge_base USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS interview_kb_domain_idx ON interview_knowledge_base(domain);
CREATE INDEX IF NOT EXISTS interview_kb_category_idx ON interview_knowledge_base(category);

-- Interview questions bank
CREATE TABLE IF NOT EXISTS interview_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_text TEXT NOT NULL,
    role_type TEXT NOT NULL CHECK (role_type IN ('IT', 'Finance', 'Both')),
    domain TEXT NOT NULL CHECK (domain IN ('IT', 'Finance', 'General')),
    category TEXT NOT NULL CHECK (category IN ('technical', 'behavioral', 'case_study', 'situational', 'coding')),
    difficulty TEXT NOT NULL CHECK (difficulty IN ('beginner', 'intermediate', 'advanced')),
    ideal_answer TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS interview_questions_role_idx ON interview_questions(role_type);
CREATE INDEX IF NOT EXISTS interview_questions_domain_idx ON interview_questions(domain);
CREATE INDEX IF NOT EXISTS interview_questions_category_idx ON interview_questions(category);
CREATE INDEX IF NOT EXISTS interview_questions_difficulty_idx ON interview_questions(difficulty);
CREATE INDEX IF NOT EXISTS interview_questions_active_idx ON interview_questions(is_active);

-- Interview sessions
CREATE TABLE IF NOT EXISTS interview_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    role_type TEXT NOT NULL CHECK (role_type IN ('IT', 'Finance', 'Both')),
    domain TEXT NOT NULL CHECK (domain IN ('IT', 'Finance', 'General')),
    job_id UUID REFERENCES jobs(id) ON DELETE SET NULL,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed', 'abandoned')),
    total_questions INTEGER DEFAULT 0,
    completed_questions INTEGER DEFAULT 0,
    avg_score FLOAT,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS interview_sessions_user_idx ON interview_sessions(user_id);
CREATE INDEX IF NOT EXISTS interview_sessions_job_idx ON interview_sessions(job_id);
CREATE INDEX IF NOT EXISTS interview_sessions_status_idx ON interview_sessions(status);
CREATE INDEX IF NOT EXISTS interview_sessions_started_idx ON interview_sessions(started_at DESC);

-- Interview responses
CREATE TABLE IF NOT EXISTS interview_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES interview_sessions(id) ON DELETE CASCADE NOT NULL,
    question_id UUID REFERENCES interview_questions(id) ON DELETE CASCADE NOT NULL,
    user_answer TEXT NOT NULL,
    evaluation_scores JSONB DEFAULT '{}'::jsonb,
    feedback TEXT,
    strengths TEXT[] DEFAULT ARRAY[]::TEXT[],
    improvements TEXT[] DEFAULT ARRAY[]::TEXT[],
    submitted_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS interview_responses_session_idx ON interview_responses(session_id);
CREATE INDEX IF NOT EXISTS interview_responses_question_idx ON interview_responses(question_id);
CREATE INDEX IF NOT EXISTS interview_responses_submitted_idx ON interview_responses(submitted_at DESC);

-- Interview performance analytics (aggregated view)
CREATE TABLE IF NOT EXISTS interview_performance_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    domain TEXT NOT NULL CHECK (domain IN ('IT', 'Finance', 'General')),
    total_sessions INTEGER DEFAULT 0,
    total_questions_answered INTEGER DEFAULT 0,
    avg_overall_score FLOAT,
    avg_relevance_score FLOAT,
    avg_completeness_score FLOAT,
    avg_technical_accuracy_score FLOAT,
    avg_communication_score FLOAT,
    weak_categories TEXT[] DEFAULT ARRAY[]::TEXT[],
    strong_categories TEXT[] DEFAULT ARRAY[]::TEXT[],
    last_practice_date TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, domain)
);

CREATE INDEX IF NOT EXISTS interview_analytics_user_idx ON interview_performance_analytics(user_id);
CREATE INDEX IF NOT EXISTS interview_analytics_domain_idx ON interview_performance_analytics(domain);

-- Helper function: Search knowledge base for RAG retrieval
CREATE OR REPLACE FUNCTION search_interview_knowledge(
    query_embedding vector(768),
    search_domain TEXT,
    match_count INT DEFAULT 5
)
RETURNS TABLE (
    id UUID,
    title TEXT,
    content TEXT,
    chunk_text TEXT,
    category TEXT,
    similarity FLOAT
)
LANGUAGE sql STABLE
AS $$
    SELECT
        id,
        title,
        content,
        chunk_text,
        category,
        1 - (embedding <=> query_embedding) AS similarity
    FROM interview_knowledge_base
    WHERE domain = search_domain OR domain = 'General'
      AND embedding IS NOT NULL
    ORDER BY embedding <=> query_embedding
    LIMIT match_count;
$$;

-- Helper function: Get next question for session
CREATE OR REPLACE FUNCTION get_next_interview_question(
    p_session_id UUID,
    p_role_type TEXT,
    p_domain TEXT,
    p_difficulty TEXT DEFAULT 'intermediate'
)
RETURNS TABLE (
    id UUID,
    question_text TEXT,
    category TEXT,
    difficulty TEXT
)
LANGUAGE sql STABLE
AS $$
    SELECT
        q.id,
        q.question_text,
        q.category,
        q.difficulty
    FROM interview_questions q
    WHERE q.role_type IN (p_role_type, 'Both')
      AND q.domain IN (p_domain, 'General')
      AND q.difficulty = p_difficulty
      AND q.is_active = TRUE
      AND q.id NOT IN (
          SELECT question_id 
          FROM interview_responses 
          WHERE session_id = p_session_id
      )
    ORDER BY RANDOM()
    LIMIT 1;
$$;

-- Function to update performance analytics
CREATE OR REPLACE FUNCTION update_interview_analytics(p_user_id UUID, p_domain TEXT)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO interview_performance_analytics (
        user_id,
        domain,
        total_sessions,
        total_questions_answered,
        avg_overall_score,
        avg_relevance_score,
        avg_completeness_score,
        avg_technical_accuracy_score,
        avg_communication_score,
        last_practice_date,
        updated_at
    )
    SELECT
        p_user_id,
        p_domain,
        COUNT(DISTINCT s.id),
        COUNT(r.id),
        AVG((r.evaluation_scores->>'overall_score')::float),
        AVG((r.evaluation_scores->>'relevance_score')::float),
        AVG((r.evaluation_scores->>'completeness_score')::float),
        AVG((r.evaluation_scores->>'technical_accuracy_score')::float),
        AVG((r.evaluation_scores->>'communication_score')::float),
        MAX(r.submitted_at),
        NOW()
    FROM interview_sessions s
    LEFT JOIN interview_responses r ON s.id = r.session_id
    WHERE s.user_id = p_user_id AND s.domain = p_domain
    GROUP BY p_user_id, p_domain
    ON CONFLICT (user_id, domain)
    DO UPDATE SET
        total_sessions = EXCLUDED.total_sessions,
        total_questions_answered = EXCLUDED.total_questions_answered,
        avg_overall_score = EXCLUDED.avg_overall_score,
        avg_relevance_score = EXCLUDED.avg_relevance_score,
        avg_completeness_score = EXCLUDED.avg_completeness_score,
        avg_technical_accuracy_score = EXCLUDED.avg_technical_accuracy_score,
        avg_communication_score = EXCLUDED.avg_communication_score,
        last_practice_date = EXCLUDED.last_practice_date,
        updated_at = NOW();
END;
$$;