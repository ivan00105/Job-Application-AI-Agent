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
    status TEXT DEFAULT 'draft',
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
