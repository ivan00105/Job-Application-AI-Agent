-- Migration: Create tables for application preparation features
-- Created: 2025-01-XX
-- Description: Adds tables for tailored CVs and cover letters

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

