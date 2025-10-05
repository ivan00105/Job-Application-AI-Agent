/*
  # Initial Database Schema for Job Application Agent

  ## Overview
  This migration sets up the complete database schema for the job application agent system.
  
  ## Tables Created
  
  ### 1. users
  - Stores user authentication information
  - Fields: id, username, password_hash, created_at
  - Simple authentication for POC (not using Supabase Auth)
  
  ### 2. cv_profiles
  - Stores parsed CV/resume data
  - Fields: id, user_id, raw_text, parsed_data (JSONB), embedding (vector), timestamps
  - One-to-one relationship with users
  - Vector embeddings for semantic search (768 dimensions for Nomic Embed)
  
  ### 3. jobs
  - Stores scraped job postings
  - Fields: id, title, company, description, requirements, location, salary, url, source, embedding
  - Vector embeddings for matching
  - Indexed for fast similarity search
  
  ### 4. job_matches
  - Stores precomputed job match scores
  - Fields: user_id, job_id, scores (overall, skill, experience), explanation (JSONB)
  - Materialized view of matching results for performance
  
  ### 5. applications
  - Tracks job applications
  - Fields: user_id, job_id, status, resume_text, cover_letter, timestamps
  - Application lifecycle management
  
  ## Vector Search Setup
  - Enables pgvector extension for semantic search
  - Creates IVFFlat indexes on embedding columns
  - Optimized for cosine similarity search
  
  ## Security
  - No RLS for POC (simple auth only)
  - Can be added later if needed
*/

-- Enable pgvector extension for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Users table for authentication
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- CV profiles with vector embeddings
CREATE TABLE IF NOT EXISTS cv_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    raw_text TEXT,
    parsed_data JSONB DEFAULT '{}'::jsonb,
    embedding vector(768),  -- Nomic Embed produces 768-dimensional vectors
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for vector similarity search on CV profiles
CREATE INDEX IF NOT EXISTS cv_profiles_embedding_idx 
ON cv_profiles USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create index for user lookup
CREATE INDEX IF NOT EXISTS cv_profiles_user_id_idx ON cv_profiles(user_id);

-- Jobs table with vector embeddings
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    description TEXT,
    requirements TEXT[] DEFAULT ARRAY[]::TEXT[],  -- Array of requirement strings
    location TEXT,
    salary_min INTEGER,
    salary_max INTEGER,
    url TEXT,
    source TEXT,  -- 'jobsdb', 'linkedin', 'indeed', etc.
    embedding vector(768),
    posted_date DATE,
    scraped_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Create index for vector similarity search on jobs
CREATE INDEX IF NOT EXISTS jobs_embedding_idx 
ON jobs USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS jobs_is_active_idx ON jobs(is_active);
CREATE INDEX IF NOT EXISTS jobs_company_idx ON jobs(company);
CREATE INDEX IF NOT EXISTS jobs_location_idx ON jobs(location);
CREATE INDEX IF NOT EXISTS jobs_posted_date_idx ON jobs(posted_date DESC);

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

-- Create indexes for fast match retrieval
CREATE INDEX IF NOT EXISTS job_matches_user_score_idx 
ON job_matches(user_id, overall_score DESC);

CREATE INDEX IF NOT EXISTS job_matches_job_idx ON job_matches(job_id);

-- Applications tracking
CREATE TABLE IF NOT EXISTS applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'draft',  -- draft, submitted, interviewing, rejected, offer
    resume_text TEXT,
    cover_letter TEXT,
    notes TEXT,
    submitted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for application queries
CREATE INDEX IF NOT EXISTS applications_user_idx ON applications(user_id);
CREATE INDEX IF NOT EXISTS applications_job_idx ON applications(job_id);
CREATE INDEX IF NOT EXISTS applications_status_idx ON applications(status);
CREATE INDEX IF NOT EXISTS applications_created_idx ON applications(created_at DESC);

-- Create a function for vector similarity search (helper)
CREATE OR REPLACE FUNCTION match_jobs(
    query_embedding vector(768),
    match_threshold float,
    match_count int
)
RETURNS TABLE (
    id uuid,
    title text,
    company text,
    description text,
    location text,
    similarity float
)
LANGUAGE sql STABLE
AS $$
    SELECT
        id,
        title,
        company,
        description,
        location,
        1 - (embedding <=> query_embedding) AS similarity
    FROM jobs
    WHERE 1 - (embedding <=> query_embedding) > match_threshold
      AND is_active = true
    ORDER BY embedding <=> query_embedding
    LIMIT match_count;
$$;

-- Create a function for CV-job matching (helper)
CREATE OR REPLACE FUNCTION match_cv_to_jobs(
    cv_embedding vector(768),
    match_count int DEFAULT 20
)
RETURNS TABLE (
    id uuid,
    title text,
    company text,
    similarity float
)
LANGUAGE sql STABLE
AS $$
    SELECT
        id,
        title,
        company,
        1 - (embedding <=> cv_embedding) AS similarity
    FROM jobs
    WHERE is_active = true
      AND embedding IS NOT NULL
    ORDER BY embedding <=> cv_embedding
    LIMIT match_count;
$$;
